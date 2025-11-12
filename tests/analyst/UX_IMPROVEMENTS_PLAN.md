# TUI UX Improvements Plan - User-Driven

**Date:** 2025-11-02
**Priority:** CRITICAL - Based on actual user testing feedback
**Source:** testnotes.md user testing session

---

## Executive Summary

User testing revealed that the TUI is too strict with syntax and doesn't provide helpful, context-aware guidance. Users want:
1. Forgiving command parsing (handle typos/missing keywords)
2. Interactive menus instead of memorizing exact syntax
3. Smart, context-aware suggestions based on current filters

---

## Critical Issues from User Testing

### Issue 1: Strict Syntax Requirement (BLOCKING USER)

**User Experience:**
```
>>> show w13 5mlhr
[Does nothing - command not recognized]

>>> show w13 at 5mlhr
[Works correctly]
```

**Problem:** User forgot the word "at" and command completely failed. No helpful suggestions.

**Expected Behavior:**
- System should recognize "show w13 5mlhr" as equivalent to "show w13 at 5mlhr"
- OR provide helpful message: "Did you mean: show w13 at 5mlhr?"
- Fuzzy matching should handle minor syntax variations

**Solution:**
```python
# Add flexible parsing patterns:
# Pattern 1: show w13 at 5mlhr (exact)
# Pattern 2: show w13 5mlhr (implied 'at')
# Pattern 3: show w13 5 mlhr (with space)
# Pattern 4: filter w13 5mlhr (alternative verb)

def _fuzzy_parse_command(self, cmd: str) -> Optional[Dict]:
    """Try multiple parsing strategies to be more forgiving."""

    # Strategy 1: Try exact patterns
    parsed = self.parse_command(cmd)
    if parsed:
        return parsed

    # Strategy 2: Try inserting 'at' before flow parameters
    if re.match(r'show\s+w1[34]\s+\d+\s*mlhr', cmd):
        # Insert 'at' before mlhr
        cmd_fixed = re.sub(r'(show\s+w1[34])\s+(\d+)', r'\1 at \2', cmd)
        parsed = self.parse_command(cmd_fixed)
        if parsed:
            print(f"(Interpreted as: {cmd_fixed})")
            return parsed

    # Strategy 3: Check for common typos and suggest fixes
    suggestions = self._suggest_similar_commands(cmd)
    if suggestions:
        print(f"\n❓ Did you mean:")
        for i, suggestion in enumerate(suggestions[:3], 1):
            print(f"  {i}. {suggestion}")
        print()
        choice = input("Select option (1-3) or press Enter to cancel: ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(suggestions):
            return self.parse_command(suggestions[int(choice)-1])

    return None
```

---

### Issue 2: Plot Command Needs Context-Aware Menus (CRITICAL UX)

**User Experience:**
```
>>> [W13@5mlhr] plot

[Clarification Needed]
What would you like to plot? Try specifying a device type, device ID, or parameters.
```

**Problem:** User has active filters (W13@5mlhr) but system asks vague question. Should offer specific, actionable options.

**Expected Behavior:**
```
>>> [W13@5mlhr] plot

📊 PLOT OPTIONS (based on your current filters: W13 @ 5ml/hr)

Data Available:
  • 2 devices (W13_S1_R1, W13_S2_R2)
  • 2 complete droplet analyses (6 DFU rows each)
  • 2 complete frequency analyses (30 measurements each)

What would you like to plot?

DROPLET MEASUREMENTS:
  A. Compare droplet sizes between devices
  B. Droplet size distribution for W13_S1_R1
  C. Droplet size distribution for W13_S2_R2
  D. Droplet size vs DFU row position

FREQUENCY MEASUREMENTS:
  E. Compare frequencies between devices
  F. Frequency distribution for W13_S1_R1
  G. Frequency distribution for W13_S2_R2
  H. Frequency vs ROI position

COMBINED PLOTS:
  I. Both droplet and frequency for W13_S1_R1
  J. Both droplet and frequency for W13_S2_R2
  K. Side-by-side comparison of all measurements

Type a letter (A-K), or 'cancel' to exit:
```

**User Input:** Just type "A" instead of "plot w13 5mlhr droplet sizes compare devices"

**Solution:**
```python
def _generate_plot_menu(self, filtered_data: pd.DataFrame) -> Dict[str, Dict]:
    """Generate context-aware plot options based on available data."""

    options = {}

    # Analyze what data is available
    devices = filtered_data['device_id'].unique()
    has_droplet = len(filtered_data[filtered_data['file_type'] == 'csv']) > 0
    has_freq = len(filtered_data[filtered_data['file_type'] == 'txt']) > 0

    option_key = 'A'

    # Droplet measurement options
    if has_droplet:
        if len(devices) > 1:
            options[option_key] = {
                'description': 'Compare droplet sizes between devices',
                'plot_type': 'compare_devices',
                'metric': 'droplet_size_mean',
                'devices': 'all'
            }
            option_key = chr(ord(option_key) + 1)

        for device in devices:
            options[option_key] = {
                'description': f'Droplet size distribution for {device}',
                'plot_type': 'distribution',
                'metric': 'droplet_size_mean',
                'devices': [device]
            }
            option_key = chr(ord(option_key) + 1)

    # Frequency options...
    # Combined options...

    return options

def _show_interactive_plot_menu(self):
    """Show interactive menu and execute user choice."""
    filtered = self._get_current_filtered_data()

    if len(filtered) == 0:
        print("No data available for plotting. Please set filters first.")
        return

    # Generate options based on current data
    options = self._generate_plot_menu(filtered)

    # Display menu
    print()
    print("=" * 70)
    print("📊 PLOT OPTIONS")
    print("=" * 70)
    print()

    # Show current context
    filters = self.session_state['current_filters']
    print(f"Current filters: {filters}")
    print()

    # Show data summary
    print("Data Available:")
    print(f"  • {filtered['device_id'].nunique()} devices")
    # ... more summary

    print()
    print("What would you like to plot?")
    print()

    # Group and display options
    for key, option in options.items():
        print(f"  {key}. {option['description']}")

    print()
    choice = input("Type a letter, or 'cancel' to exit: ").strip().upper()

    if choice in options:
        # Execute the plot
        self._execute_plot_option(options[choice])
    elif choice == 'CANCEL':
        print("Plot cancelled.")
    else:
        print("Invalid option. Plot cancelled.")
```

---

### Issue 3: Better "Did You Mean" Suggestions

**Current Behavior:**
```
>>> [W13@5mlhr] 5mlhr
[Error] Unknown query type 'help'
```

**Problem:** User typed just "5mlhr" (maybe trying to change filter) and got unhelpful error.

**Expected Behavior:**
```
>>> [W13@5mlhr] 5mlhr

❓ I'm not sure what you want to do with '5mlhr'.

Did you mean:
  1. show w13 at 5mlhr (already active)
  2. stats w13 at 5mlhr
  3. show params for w13

Or type:
  • 'help' for command reference
  • 'clear' to reset filters
  • 'plot' for plotting options

>>>
```

**Solution:**
- Use fuzzy string matching (difflib) to find similar commands
- Suggest based on context (current filters, recent commands)
- Provide numbered options for easy selection

---

## Implementation Plan

### Phase 1: Fuzzy Command Parsing (HIGH PRIORITY)

**Files to Modify:**
- `dashboard_v2.py` - Add `_fuzzy_parse_command()` method
- `dashboard_v2.py` - Modify `parse_command()` to handle variations

**Tasks:**
1. Add pattern for "show w13 5mlhr" (without 'at')
2. Add pattern for "show w13 5 mlhr" (with extra space)
3. Add pattern for alternative verbs: "filter", "find", "get"
4. Implement "did you mean" suggestions using difflib
5. Test with user's exact failing commands

**Time Estimate:** 2-3 hours

---

### Phase 2: Interactive Plot Menus (HIGH PRIORITY)

**Files to Modify:**
- `dashboard_v2.py` - Add `_generate_plot_menu()` method
- `dashboard_v2.py` - Add `_show_interactive_plot_menu()` method
- `dashboard_v2.py` - Modify plot command handling

**Tasks:**
1. Detect when "plot" is typed with active filters
2. Analyze available data (droplet vs frequency, device count)
3. Generate context-aware menu options
4. Display interactive menu with letter selections
5. Execute selected plot option
6. Test with user's exact scenario (W13@5mlhr, typing "plot")

**Time Estimate:** 3-4 hours

---

### Phase 3: Enhanced Error Messages (MEDIUM PRIORITY)

**Files to Modify:**
- `src/error_handler.py` - Enhance suggestion logic
- `dashboard_v2.py` - Better error display

**Tasks:**
1. Improve command similarity matching
2. Add context-aware suggestions (based on filters, history)
3. Provide actionable options (numbered choices)
4. Test with various typos and incomplete commands

**Time Estimate:** 1-2 hours

---

## Success Criteria

### Test 1: Fuzzy Command Matching
```bash
>>> show w13 5mlhr
(Interpreted as: show w13 at 5mlhr)
✓ Filter: device_type=W13, flowrate=5mlhr
```

### Test 2: Interactive Plot Menu
```bash
>>> [W13@5mlhr] plot
📊 PLOT OPTIONS
...
A. Compare droplet sizes between devices
...
Type a letter (A-K): A
✓ Generating plot...
```

### Test 3: Helpful Error Messages
```bash
>>> [W13@5mlhr] 5mlhr
❓ Did you mean:
  1. stats w13 at 5mlhr
  2. show params for w13
✓ Select option (1-2) or press Enter to cancel:
```

---

## User Experience Goals

1. **Less Typing:** Use letters/numbers instead of full commands
2. **Forgiving:** Handle typos and missing keywords gracefully
3. **Helpful:** Suggest what user probably meant
4. **Context-Aware:** Use active filters to offer smart options
5. **Interactive:** Menus instead of memorizing syntax

---

## Technical Notes

### Fuzzy Matching Library
```python
from difflib import SequenceMatcher, get_close_matches

def similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

def suggest_commands(input_cmd: str, valid_commands: List[str]) -> List[str]:
    return get_close_matches(input_cmd, valid_commands, n=3, cutoff=0.6)
```

### Interactive Menu Pattern
```python
def show_menu(title: str, options: Dict[str, str]) -> str:
    print(f"\n{title}")
    print("=" * 70)
    for key, desc in options.items():
        print(f"  {key}. {desc}")
    return input("\nSelect option: ").strip().upper()
```

---

## Next Steps

1. **Immediate:** Implement fuzzy command parsing (fixes user's "show w13 5mlhr" issue)
2. **High Priority:** Build interactive plot menu system
3. **Follow-up:** Enhance all error messages with suggestions
4. **Testing:** Re-run user's exact test scenario from testnotes.md

---

**Created:** 2025-11-02
**Based on:** User testing session (testnotes.md)
**Status:** Ready for implementation
**Priority:** CRITICAL - These are user-blocking issues
