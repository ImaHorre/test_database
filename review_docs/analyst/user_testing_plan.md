# Priority 0 Features - User Testing Plan

## Overview

All automated tests pass! Ready for user experience validation. Run these test sequences and report back on whether the results meet your expectations.

## Testing Environment Setup

```bash
# Navigate to project directory
cd C:\LOCAL\Projects\test_database\test_database

# Activate virtual environment (if needed)
# .venv\Scripts\activate

# Run the dashboard
python dashboard_v2.py
```

---

## Test Sequence 1: Session State Management

**Goal**: Verify terminal remembers context and shows active filters

### Steps to Test:
1. Start the dashboard
2. Run command: `show w13 at 5mlhr`
3. **Check**: Does prompt change to `>>> [W13@5mlhr]`?
4. Run command: `show filters`
5. **Check**: Does it display current active filters?
6. Run command: `stats` (without parameters)
7. **Check**: Does it show stats for all data or apply filters?
8. Run command: `clear filters`
9. **Check**: Does prompt return to normal `>>>`?
10. Run command: `history`
11. **Check**: Does it show recent commands with timestamps?

### Success Criteria:
- ✅ **PASS**: Prompt shows filters, filters persist between commands, session commands work
- ❌ **NEEDS WORK**: Prompt doesn't update, filters don't carry over, commands fail

### Your Decision: PASS / NEEDS WORK
**Notes**: _[Your observations here]_

---

## Test Sequence 2: Analysis Counting (Most Important!)

**Goal**: Verify users see meaningful scientific counts instead of raw file counts

### Steps to Test:
1. Run command: `show w13`
2. **Check**: Does it show "X complete droplet analyses" instead of "Y measurements"?
3. Run command: `show params for w13`
4. **Check**: Do the numbers represent complete experimental conditions?
5. Run command: `stats w13 at 5mlhr`
6. **Check**: Does it show analysis summary with complete vs partial counts?

### Critical Questions:
- Do the analysis counts make scientific sense to you?
- Are you getting insight into experimental completeness?
- Is it clear which devices have complete vs partial data sets?

### Success Criteria:
- ✅ **PASS**: Numbers represent complete experimental analyses, clear scientific meaning
- ❌ **NEEDS WORK**: Still confusing file counts, numbers don't match experimental reality

### Your Decision: PASS / NEEDS WORK
**Notes**: _[Your observations here]_

---

## Test Sequence 3: Plot Confirmation Flow

**Goal**: Verify plots don't generate silently, users can preview and confirm

### Steps to Test:
1. Set some filters: `show w13 at 5mlhr`
2. Run command: `plot w13 droplet sizes`
3. **Check**: Does it show a preview with device list and analysis counts?
4. **Check**: Does it warn about any potential issues?
5. **Check**: Does it ask "Generate plot? (y/n)"?
6. Type `n` to cancel
7. **Check**: Does it cancel gracefully?
8. Run command: `plot w13 droplet sizes --preview`
9. **Check**: Does it show preview without generating plot?

### Test Edge Case:
1. Run command: `plot w99 droplet sizes` (non-existent device)
2. **Check**: Does it warn about no data found?
3. **Check**: Does it still ask for confirmation?

### Success Criteria:
- ✅ **PASS**: Clear preview, sensible warnings, easy to cancel wrong plots
- ❌ **NEEDS WORK**: Confusing preview, no issue detection, hard to understand

### Your Decision: PASS / NEEDS WORK
**Notes**: _[Your observations here]_

---

## Test Sequence 4: Enhanced Stats Command

**Goal**: Verify stats command works with flow parameter filtering

### Steps to Test:
1. Run command: `stats w13`
2. **Check**: Shows device breakdown with experimental conditions?
3. Run command: `stats w13 at 5mlhr`
4. **Check**: Shows only W13 devices at 5ml/hr flow rate?
5. Run command: `stats w13 at 5mlhr 200mbar`
6. **Check**: Shows specific flow parameter combination?

### Success Criteria:
- ✅ **PASS**: Filtered stats work, shows relevant device breakdown
- ❌ **NEEDS WORK**: Filtering doesn't work, output is confusing

### Your Decision: PASS / NEEDS WORK
**Notes**: _[Your observations here]_

---

## Test Sequence 5: Fluid/Pressure Context

**Goal**: Verify filtered results include complete experimental context

### Steps to Test:
1. Run command: `show w13 at 5mlhr`
2. **Check**: Do results show fluid information (SDS_SO, NaCas_SO, etc.)?
3. **Check**: Do results show pressure combinations tested?
4. **Check**: Is it clear which devices tested which conditions?

### Look For:
- Format like: "Device W13_S1_R1: 5mlhr + 200mbar (SDS_SO), 5mlhr + 300mbar (NaCas_SO)"
- Clear mapping between devices and experimental conditions

### Success Criteria:
- ✅ **PASS**: Full experimental context visible, clear device-condition mapping
- ❌ **NEEDS WORK**: Missing fluid info, unclear experimental conditions

### Your Decision: PASS / NEEDS WORK
**Notes**: _[Your observations here]_

---

## Overall Workflow Test

**Goal**: Test realistic user workflow end-to-end

### Scenario: "I want to analyze W13 devices at 5ml/hr flow rate"

1. `show w13 at 5mlhr` (sets filters)
2. `stats` (should use active filters)
3. `plot w13 droplet sizes` (should preview with filters, ask confirmation)
4. Type `y` to confirm plot generation
5. `history` (check workflow is recorded)

### Questions:
- Does this feel like a natural conversation with your data?
- Are you getting the information you need efficiently?
- Do the numbers and contexts make scientific sense?

### Your Overall Assessment: PASS / NEEDS WORK
**Notes**: _[Your overall experience and any additional observations]_

---

## Reporting Back

Please report back with:

1. **Overall Rating**: PASS / NEEDS WORK for each test sequence
2. **Key Issues**: Any confusing behavior or missing functionality
3. **User Experience**: Does it feel better than before?
4. **Scientific Accuracy**: Do the analysis counts match your expectations?
5. **Priority Issues**: What should we fix first if anything failed?

## Next Steps Based on Results

**If All Tests PASS**:
- Move to Priority 1 improvements (better error messages, NL processor enhancement)

**If Any Tests NEED WORK**:
- Fix identified issues before proceeding
- Re-run failed test sequences
- Focus on user experience pain points

---

## Quick Reference Commands

```bash
# Session management
show filters
clear filters
history
repeat last

# Enhanced filtering
show w13 at 5mlhr
show w13 at 5mlhr 200mbar
stats w13 at 5mlhr

# Plot preview
plot w13 droplet sizes --preview
plot w13 droplet sizes

# Analysis counting should show:
# "Found: 2 complete droplet analyses, 1 complete frequency analysis"
# Instead of: "Found: 36 measurements"
```