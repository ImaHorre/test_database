# OneDrive File System Scanner - Analyst Component Implementation Roadmap

## Executive Summary

This document outlines the comprehensive implementation plan for fixing critical issues identified in the analyst component code review. The plan prioritizes user experience fixes first, followed by architecture improvements and code quality enhancements.

**Current Status:** Requirements gathering complete. Core analyst component refactored to modular 918-line system with specialized handlers. Ready for user experience improvements.

**Next Phase:** Implementing Priority 0 user-critical fixes, starting with session state management for terminal memory.

---

## Code Review Analysis Summary

### Issues Identified: 25 total across 4 priority levels

**Priority 0 - User Critical (5 issues):**
- Terminal lacks session/context management
- Misleading measurement counts (shows files vs analysis sets)
- Stats command doesn't accept filters
- No user confirmation before plot generation
- Missing fluid/pressure context in results

**Priority 1 - High Impact (5 issues):**
- Generic error messages without guidance
- Weak natural language intent detection
- Overlapping command parser/NL processor responsibilities
- No query result caching
- Missing plot parameter validation

**Priority 2 - Code Quality (10 issues):**
- Configuration hardcoded throughout codebase
- Inconsistent naming conventions
- Missing unit tests
- Business logic mixed with presentation
- Duplicate filter logic across modules

**Priority 3 - Nice-to-Have (5 issues):**
- Query history and undo functionality
- Plot catalog with indexing
- Export functionality
- User preferences
- Query templates/macros

---

## Implementation Timeline

### Phase 1: Priority 0 - User-Critical Issues (Week 1)

#### Task 1: Session State Management (2-3 hours)
**Files:** `dashboard_v2.py`
**Goal:** Enable terminal to "remember" context between queries

**Implementation:**
```python
# Add to SimpleDashboard class
self.session_state = {
    'last_query': None,
    'current_filters': {},
    'last_result': None,
    'last_filtered_df': None,
    'query_history': []
}
```

**Features to Add:**
- Display active filters in prompt: `>>> [W13@5mlhr+200mbar]`
- Commands: "show filters", "clear filters", "repeat last", "use last"
- Auto-inherit filters for plot commands
- Update state after each successful command execution

**Success Criteria:**
- Users can run "filter w13 at 5mlhr" then "plot" without re-specifying filters
- Prompt shows current active filters
- Query history persists during session

#### Task 2: Fix Measurement Counting Logic (2-3 hours)
**Files:** `dashboard_v2.py` lines 314-337, 254-312
**Goal:** Show meaningful analysis counts instead of raw file counts

**Implementation:**
```python
def _count_complete_analyses(self, df):
    """Count complete vs partial analyses by experimental condition"""
    # Group by (device_id, test_date, aqueous_flowrate, oil_pressure, fluids)
    # For each group:
    #   - Count unique DFU rows (4+ = 1 complete droplet analysis)
    #   - Check for frequency files (any present = 1 complete freq analysis)
    # Return: {complete_droplet: N, complete_freq: N, partial: N}
```

**Changes:**
- Update `_cmd_show_params` to display: "1 complete droplet analysis, 1 complete frequency analysis"
- Update `_cmd_filter` to show analysis counts instead of "36 measurements"
- Add data completeness indicators (complete vs partial)

**Success Criteria:**
- Users see "2 complete droplet analyses" instead of "36 measurements"
- Clear distinction between complete vs partial experimental runs
- Counts reflect scientific meaning (experimental conditions tested)

#### Task 3: Add Filter Support to Stats Command (1-2 hours)
**Files:** `dashboard_v2.py` lines 389-427, 208-214
**Goal:** Enable targeted statistics for specific conditions

**Implementation:**
- Extend `parse_command()` regex to handle: "stats w13 at 5mlhr", "stats w13 at 5mlhr 200mbar"
- Apply same filtering logic as `_cmd_filter` to `_cmd_stats`
- Show device-level breakdown with flow parameters tested

**Output Format:**
```
Device W13_S1_R1:
  - 5mlhr + 200mbar (SDS_SO): 1 complete droplet analysis
  - 5mlhr + 300mbar (NaCas_SO): 1 complete droplet + 1 complete freq

Device W13_S1_R2:
  - 5mlhr + 200mbar (SDS_SO): 1 complete droplet analysis
```

**Success Criteria:**
- Command "stats w13 at 5mlhr" shows only W13 devices at 5mlhr flow rate
- Output includes fluid information and analysis completeness
- Maintains same filtering syntax as filter command

#### Task 4: User Confirmation Before Plot Generation (3-4 hours)
**Files:** `dashboard_v2.py` lines 429-450, `src/analyst.py` plot handlers
**Goal:** Prevent wrong plots from being generated silently

**Implementation:**
```python
def _preview_plot_data(self, filtered_df, entities):
    """Show data preview before expensive plot generation"""
    # Display:
    # - Number of devices found
    # - Flow parameter combinations
    # - Fluid types
    # - Measurement counts (complete analyses)
    # Return: preview_text, is_ambiguous, clarification_options
```

**Features:**
- Data preview showing devices, conditions, measurement counts
- Prompt: "Continue? (y/n)" before expensive operations
- Handle ambiguous cases with multiple choice options
- Add `--preview` flag for dry-run mode
- Validate plot feasibility before calling plot functions

**Ambiguous Case Handling:**
```
Found 2 devices at 5mlhr with different conditions:
(1) W13_S1_R1: 5mlhr+200mbar (SDS_SO)
(2) W13_S1_R2: 5mlhr+300mbar (NaCas_SO)

Plot options:
(1) Plot both on same graph (color by device)
(2) Plot separately (2 plots)
(3) Cancel
```

**Success Criteria:**
- Users see data preview before every plot generation
- Ambiguous requests prompt for clarification
- Wrong plots generated <5% of time
- Plot validation catches infeasible requests early

#### Task 5: Add Missing Fluid/Pressure Info (1 hour)
**Files:** `dashboard_v2.py` lines 254-312
**Goal:** Provide experimental context in filtered results

**Implementation:**
- Add breakdown of varying parameters in filtered results
- Show unique combinations of (flowrate, pressure, fluids) tested
- Indicate which devices tested which conditions

**Output Format:**
```
Found 2 devices matching 'W13 at 5mlhr':

Device W13_S1_R1: 5mlhr + 200mbar (SDS_SO), 5mlhr + 300mbar (NaCas_SO)
Device W13_S1_R2: 5mlhr + 200mbar (SDS_SO)

Flow parameter combinations tested:
- 5mlhr + 200mbar (SDS_SO): 2 devices
- 5mlhr + 300mbar (NaCas_SO): 1 device
```

**Success Criteria:**
- All filtered results include fluid and pressure information
- Users understand which experimental conditions were tested
- Clear mapping between devices and their tested conditions

---

### Phase 2: Priority 1 - High-Impact Improvements (Week 2)

#### Task 6: Enhanced NL Processor Architecture (5-6 hours)
**Files:** `dashboard_v2.py` lines 130-216, `src/query_processor.py`
**Goal:** Unify command parsing with single processor handling both simple and complex queries

**Architecture Decision (Based on Code Review):**
- **Approach:** Enhance NL processor to handle both simple and complex queries
- **Implementation:** Create CommandNormalizer that detects simple patterns and converts to canonical NL format
- **Benefits:** Single processing pipeline, consistent entity extraction, easier maintenance

**Implementation:**
```python
class CommandNormalizer:
    """Detects simple command patterns and normalizes to NL format"""

    def normalize_query(self, query):
        # Detect if query matches simple pattern (e.g., "filter w13 at 5mlhr")
        # If simple: convert to natural language equivalent
        # If complex: pass through unchanged
        # Route all through enhanced NL processor
```

**Changes:**
- Remove duplicate regex patterns from dashboard
- Enhance NL processor to handle normalized simple commands
- Raise confidence threshold from 0.7 to 0.85 for auto-execution
- Implement weighted scoring system for intent detection
- Add fuzzy matching for common typos

**Success Criteria:**
- Both "filter w13 at 5mlhr" and "show me W13 devices at 5 ml/hr" work identically
- Single code path for all query processing
- Confidence threshold improvements reduce false positives
- Typo tolerance for device names and parameters

#### Task 7: Context-Aware Error Messages (3-4 hours)
**Files:** All query handlers, `src/analyst.py` exception handling
**Goal:** Provide actionable guidance when queries fail

**Implementation:**
```python
class ErrorMessageBuilder:
    def suggest_similar(self, query, available_options):
        # Fuzzy matching for typos using Levenshtein distance

    def show_valid_options(self, category):
        # List available devices, flowrates, etc.

    def explain_what_was_attempted(self, filters):
        # Show what was tried and why it failed
```

**Error Message Examples:**
- "No devices found matching 'W15' (did you mean W13 or W14?)"
- "Flowrate 1000ml/hr not found. Available: 5, 15, 30, 35, 40, 45 ml/hr"
- "No data found for W13 at 5mlhr. W13 was tested at: 15mlhr, 30mlhr, 45mlhr"

**Success Criteria:**
- Error messages include specific suggestions for correction
- Users can successfully reformulate queries >80% of time
- Distinguish between user errors vs system errors
- Provide recovery suggestions for common mistakes

#### Task 8: Query Result Caching (2-3 hours)
**Files:** `src/analyst.py`, query handlers
**Goal:** Avoid redundant computations for repeated queries

**Implementation:**
```python
from functools import lru_cache

class DataAnalyst:
    def __init__(self):
        self._device_summary_cache = None
        self._filter_cache = {}

    @lru_cache(maxsize=32)
    def _filter_cached(self, device_type, flowrate, pressure):
        # Return hashable key for cache

    @property
    def device_summary(self):
        if self._device_summary_cache is None:
            self._device_summary_cache = self.df.groupby(...)
        return self._device_summary_cache
```

**Features:**
- LRU cache for expensive filter operations
- Use DataFrame views instead of copies when no modification needed
- Precompute common aggregations in `__post_init__`
- Invalidate cache when data refreshes

**Success Criteria:**
- Repeated queries execute <100ms (cached)
- Memory usage remains reasonable (cache size limits)
- Cache invalidation works correctly on data updates

#### Task 9: Plot Parameter Validation (2-3 hours)
**Files:** `src/plotting/dfu_plots.py`, `src/analyst.py` plot methods
**Goal:** Catch plot errors before expensive generation

**Implementation:**
```python
def validate_plot_feasibility(df, metric, grouping):
    """Validate plot can be generated successfully"""
    # Check sufficient data points (>1 DFU row for DFU plots)
    # Check valid metric values (not all NaN)
    # Check varying parameters exist for comparison
    # Return: (is_valid, error_message, suggestions)
```

**Features:**
- Add `dry_run` parameter to plot methods
- Call validation before expensive plotting operations
- Show data preview and validation results
- Suggest alternative plot types if current one infeasible

**Success Criteria:**
- Plot failures caught before generation starts
- Users get clear explanations of why plot cannot be generated
- Alternative suggestions provided when appropriate

---

### Phase 3: Priority 2 - Code Quality & Maintainability (Week 3-4)

#### Task 10: Configuration Module Extraction (1 hour)
**Goal:** Centralize all configuration constants

**Implementation:**
```python
# config/analyst_config.py
@dataclass
class AnalystConfig:
    PLOT_DPI: int = 300
    OUTPUT_BASE: Path = Path('outputs/analyst')
    CONFIDENCE_THRESHOLD: float = 0.85
    MAX_PLOT_CACHE: int = 50
    DEFAULT_FIGSIZE: Tuple[int, int] = (12, 6)
    COLOR_PALETTE: str = 'Set2'

    # Terminal settings
    MAX_HISTORY_SIZE: int = 100
    PROMPT_TEMPLATE: str = ">>> {filters}"

    # Data validation
    MIN_DFU_ROWS_FOR_COMPLETE: int = 4
    REQUIRED_COLUMNS: List[str] = [...]
```

#### Task 11: Standardize Naming Conventions (2-3 hours)
**Goal:** Consistent terminology throughout codebase

**Standard Names:**
- `device_type`: W13, W14 (categorical)
- `device_id`: W13_S1_R1 (full identifier)
- `aqueous_flowrate`: Never abbreviate to just "flowrate"
- `oil_pressure`: Always include "oil" prefix
- `measurement_id`: Unique identifier for each measurement file

**Tasks:**
- Audit all uses of device_id vs device_type vs dtype
- Update variable names consistently
- Document naming conventions in style guide
- Update comments and docstrings

#### Task 12: Comprehensive Unit Tests (6-8 hours)
**Goal:** Test coverage >80% for critical components

**Test Structure:**
```
tests/
├── unit/
│   ├── test_command_parser.py
│   ├── test_entity_extraction.py
│   ├── test_filter_logic.py
│   ├── test_query_handlers.py
│   └── test_session_state.py
├── integration/
│   ├── test_full_pipeline.py
│   └── test_dashboard_workflow.py
└── fixtures/
    ├── mock_data.csv
    └── test_scenarios.json
```

**Focus Areas:**
- Command parser patterns and edge cases
- Entity extraction with malformed input
- Filter logic with empty results
- Error handling paths
- Session state management
- Each query handler independently

#### Task 13: Extract Business Logic from Dashboard (4-5 hours)
**Goal:** Separate presentation from business logic

**Architecture:**
```python
# presentation/terminal_presenter.py
class TerminalPresenter:
    """Handles all data formatting for terminal display"""
    def format_filter_results(self, result): ...
    def format_stats_output(self, stats): ...
    def format_error_message(self, error): ...

# commands/terminal_commands.py
class TerminalCommands:
    """Handles command execution logic"""
    def __init__(self, analyst, presenter):
        self.analyst = analyst
        self.presenter = presenter

    def execute_filter(self, entities): ...
    def execute_stats(self, entities): ...
    def execute_plot(self, entities): ...

# dashboard_v2.py (becomes thin coordinator)
class SimpleDashboard:
    """Coordinates user input and response display"""
    def __init__(self):
        self.commands = TerminalCommands(analyst, presenter)

    def run(self):
        # Parse input -> Delegate to commands -> Display results
```

**Benefits:**
- Clear separation of concerns
- Easier unit testing
- Reusable business logic
- Follow MVC pattern

---

### Phase 4: Priority 3 - Nice-to-Have Features (Future)

#### Task 14: Query History and Undo (2-3 hours)
**Features:**
- Command: "history" shows last 10 queries with timestamps
- Command: "undo" reverts to previous state
- Command: "repeat 3" re-runs query #3 from history
- Persistent history across sessions (save to file)

#### Task 15: Plot Catalog with Indexing (2-3 hours)
**Features:**
- Maintain `plot_index.json` with metadata
- Command: "list plots" shows recent plots with descriptions
- Command: "open plot 5" opens specific plot in default viewer
- Search plots by device, date, parameters
- Organize plots by date: `outputs/analyst/plots/2025-10-31/`

#### Task 16: Export Functionality (1-2 hours)
**Features:**
- Command: "export to csv filtered_w13.csv"
- Command: "export plot to pdf report.pdf"
- Support multiple formats (CSV, Excel, PDF)
- Include metadata in exports (query used, timestamp, etc.)

#### Task 17: User Preferences (1-2 hours)
**Features:**
- Save plotting preferences (colors, DPI, style)
- Save default filters and common queries
- User config file: `~/.analyst_preferences.json`
- Command: "set preference plot_dpi 300"

#### Task 18: Query Templates/Macros (2-3 hours)
**Features:**
- Save common queries: "save query as compare_w13_w14"
- Load saved queries: "run compare_w13_w14"
- Template system with parameters: "compare {device1} vs {device2}"
- Share templates between users

---

## Architecture Decisions

### Natural Language Processing Enhancement

**Decision:** Enhance existing NL processor to handle both simple commands and complex natural language queries.

**Rationale:**
- Code review recommends single processing pipeline
- User wants structured commands as backbone with NL conversion
- Reduces code duplication and maintenance overhead
- Enables consistent entity extraction across input types

**Implementation Approach:**
1. Create CommandNormalizer that detects simple vs complex queries
2. Simple commands (e.g., "filter w13 at 5mlhr") get normalized to NL format
3. All queries route through enhanced NL processor
4. Single entity extraction system
5. Consistent confidence scoring and validation

### Session State Management

**Decision:** Implement comprehensive session state in terminal dashboard.

**Features:**
- Track current filters, last query, query history
- Display active filters in prompt
- Enable filter inheritance between commands
- Persist state during entire session

**Benefits:**
- Users can build on previous queries naturally
- Reduces repetitive typing
- Enables workflow efficiency
- Matches user mental model of "conversation with data"

### Error Handling Strategy

**Decision:** Context-aware error messages with actionable suggestions.

**Features:**
- Fuzzy matching for typos (Levenshtein distance)
- Show available options for each entity type
- Explain what was attempted and why it failed
- Provide specific correction suggestions

**Benefits:**
- Users can self-correct >80% of errors
- Reduces support burden
- Improves learning curve
- Builds user confidence

---

## Success Metrics

### User Experience Goals
- ✅ Users can build on previous queries without re-entering filters
- ✅ Plot generation has <5% error rate (wrong plot created)
- ✅ Error messages lead to successful query reformulation >80% of time
- ✅ Terminal session feels conversational and context-aware

### Performance Goals
- ✅ Repeated queries execute <100ms (cached)
- ✅ Plot generation takes <2s for typical datasets
- ✅ Memory usage remains stable during long sessions

### Code Quality Goals
- ✅ Test coverage >80% for critical components
- ✅ No modules >500 lines (except main analyst.py)
- ✅ DRY violations reduced by >70%
- ✅ Clear separation of concerns (MVC pattern)

### Reliability Goals
- ✅ Session state management works reliably
- ✅ Cache invalidation prevents stale data
- ✅ Error handling covers edge cases
- ✅ Input validation prevents system crashes

---

## Risk Assessment

### High Risk Items
1. **Session State Complexity** - Managing state across complex query sequences
   - *Mitigation:* Start with simple state, add complexity incrementally
   - *Fallback:* Stateless mode as backup option

2. **NL Processor Enhancement** - Risk of breaking existing functionality
   - *Mitigation:* Comprehensive test coverage before changes
   - *Fallback:* Keep old parser as backup during transition

3. **Performance Impact** - Caching and state management overhead
   - *Mitigation:* Performance testing with realistic datasets
   - *Fallback:* Configurable caching levels

### Medium Risk Items
1. **User Confirmation Flow** - Risk of interrupting user workflow
   - *Mitigation:* Smart defaults and skip options for power users
2. **Error Message Quality** - Risk of overwhelming novice users
   - *Mitigation:* Progressive disclosure, simple/advanced error modes

### Low Risk Items
- Configuration extraction
- Naming standardization
- Unit test addition
- Documentation improvements

---

## Next Steps

### Immediate Actions (Next Session)
1. ✅ **Document this roadmap** in `/docs/` folder ← COMPLETED
2. **Start with session state management** implementation
3. **Fix measurement counting logic**
4. **Implement user confirmation flow** for plots
5. **Add missing contextual information** to results

### Week 1 Goals
- Complete all Priority 0 tasks
- Terminal dashboard has session memory
- Users see meaningful analysis counts
- Plot generation requires confirmation
- Filtered results include experimental context

### Validation Approach
- Test each task with realistic user workflows
- Validate fixes solve original complaints from code review
- Get user feedback on UX improvements
- Measure success metrics (error rates, query success rates)

---

## Conclusion

This roadmap addresses all 25 issues identified in the code review, prioritizing user experience improvements that will have immediate impact on productivity. The architecture decisions align with the code review recommendations while supporting the user's vision of structured commands with natural language conversion.

The implementation timeline balances thorough fixes with practical development constraints, ensuring critical user issues are resolved first while building toward a maintainable, well-tested codebase.

**Total Estimated Effort:** 4-6 weeks for comprehensive implementation
**Phase 1 (P0) Completion:** Week 1 (user-critical fixes)
**Production Ready:** End of Week 2 (with P1 improvements)