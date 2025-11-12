# Analyst Agent Tests & Phase Documentation

This directory contains tests, phase completion documentation, and development artifacts for the **Analyst Agent**, which processes natural language queries and generates reports/visualizations.

## Agent Responsibility

The Analyst Agent:
- Processes natural language queries from users
- Generates data visualizations and plots
- Creates comparison reports (device-to-device, parameter effects, etc.)
- Implements interactive plotting with LLM guidance
- Builds a library of reusable plotting methods over time

## Files in this Directory

### Test Files
- **test_phase1_methods.py** - Phase 1 analysis method tests
  - Tests basic plotting capabilities
  - Validates data comparison functions
  - Checks device grouping logic

### Phase Completion Documentation

The `phase_completion/` subdirectory contains milestone documentation:

- **PHASE1_COMPLETE.md** - Phase 1: Basic Analysis Capabilities
  - Documents initial plotting methods
  - Records what was achieved in Phase 1
  - Serves as reference for completed features

- **PHASE2_COMPLETE.md** - Phase 2: Advanced Analysis & Dashboard
  - Documents dashboard implementation
  - Records advanced plotting capabilities
  - Describes interactive features added

These documents help you understand what each phase accomplished and provide context for future development.

## Running Analyst Tests

```bash
# Activate virtual environment
.venv\Scripts\activate

# Run phase 1 method tests
python tests\analyst\test_phase1_methods.py
```

## Analysis Priorities

### Device Comparison
- Compare flow parameters within device types (W13 vs W14)
- Device type is primary comparison axis
- Track individual device performance over time

### Interactive Plotting
- LLM asks clarifying questions before plotting
- Dynamic method generation on-the-fly
- Save successful methods for reuse
- Build plotting library over time

### Priority Query Types
1. Compare all W13 (or W14) devices at specific flow parameters
2. Track individual device performance over multiple test dates
3. Identify patterns across fluid types
4. Analyze DFU row performance metrics

## Related Components

- **Source Code:** `src/analyst.py`
- **Slash Command:** `.claude/commands/analyst.md`
- **Dashboard:** `dashboard.py` (root directory)
- **Dashboard Guide:** `docs/analyst/DASHBOARD_USER_GUIDE.md`
- **Output Plots:** `outputs/analyst/plots/`
- **Dependencies:** `matplotlib`, `pandas`, `numpy`

## Multi-LLM Architecture

The system is designed for multiple LLM backends:
- **Primary:** Claude Code for interactive queries
- **Secondary:** ChatGPT, Gemini for additional capacity
- Enables team collaboration and cost optimization

## Notes

- Plotting methods are saved as `.py` files for reuse
- LLM guidance makes analysis interactive and user-friendly
- Dashboard provides real-time interactive exploration
- Phase documentation helps maintain project context
