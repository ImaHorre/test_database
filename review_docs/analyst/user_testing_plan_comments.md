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

Filter: device_type=W13, flowrate=5mlhr
Found: 1 partial analysis

Matching Devices:
  1. W13_S1_R1: 5ml/hr + 200mbar (SDS_SO)
     • 5ml/hr + 200mbar (SDS_SO): no data

Flow Parameter Combinations in Results:
  1. 5ml/hr + 200mbar (SDS_SO): 1 devices
  2. 5ml/hr + 300mbar (SDS_SO): 1 devices

Droplet Size: 24.88 ± 0.52 µm
Frequency:    9.22 ± 5.51 Hz

(Comment: I am confused as to why ere are two parameter states found but only 1 matching device, which also highlghts the parameters?? a clearer result would be listing the devices matched and undernearth each device list the parameters. this shows the user that this device was done at 5mlhr and 200 mbar and this other device was done at 5mlhr and 300m bar. then as a second check the user can look at the list of 'Flow parameter combinations in results' which will again list the different flow coimbiantions with the number of times they appear. In a different dataset we might see 5mlhr 200mabr 3 devices. We need to be sure that the linguistics dont get confsed here. there will be times when a single device (one device ID) has been tested on multiule days at the same parameters will this appear as multiple devise in this search or only one device. to be cleaerer change the workding of device to 'test' so if one device has been through multiple tests at teh same parameter it will be revealed in this search. 

the prompt changed to W13@5mlhr])

4. Run command: `show filters`
5. **Check**: Does it display current active filters?
6. Run command: `stats` (without parameters)

>>> [W13@5mlhr] show filters

Active filters:
  • device_type: W13
  • flowrate: 5

>>> [W13@5mlhr] stats

[ERROR] Command 'stats' not recognized. Did you mean:
  • stats w13
  • list params

Type 'help' for available commands or try natural language like:
  • Compare W13 and W14 devices
  • Show me W13 devices at 5ml/hr
  • Plot droplet sizes for W13

(comment: hmm not sure what this command is trying to do)

>>> [W13@5mlhr] clear filters

All filters cleared.

>>> w13 stats

Processing query...
INFO:src.analyst:Processing natural language query: w13 stats
INFO:src.query_processor:Processing query: w13 stats
INFO:src.query_processor:Detected intent: help (confidence: 0.00)
INFO:src.query_processor:Extracted entities: {'device_type': 'W13'}
WARNING:src.query_handlers.router:Unknown intent type: help

[Error]

Unknown query type 'help'. Available types: list, filter, compare, analyze, track, plot, plot_dfu, report

>>> stats

[ERROR] Command 'stats' not recognized. Did you mean:
  • stats w13
  • list params

Type 'help' for available commands or try natural language like:
  • Compare W13 and W14 devices
  • Show me W13 devices at 5ml/hr
  • Plot droplet sizes for W13

i tried various thing sincluding clearnign the prompt. 

7. **Check**: Does it show stats for all data or apply filters?
8. Run command: `clear filters`
9. **Check**: Does prompt return to normal `>>>`?
10. Run command: `history`
11. **Check**: Does it show recent commands with timestamps?

yes

## Test Sequence 2: Analysis Counting (Most Important!)

**Goal**: Verify users see meaningful scientific counts instead of raw file counts

### Steps to Test:
1. Run command: `show w13`
2. **Check**: Does it show "X complete droplet analyses" instead of "Y measurements"?

it just shows the devise and the total measuremnts. no X complete droplet analyses" instead of "Y measurements"

3. Run command: `show params for w13`

this is basically working and is maybe an issue with the actual data. 
  1. 5ml/hr + 200mbar: 1 partial, 1 devices
  2. 5ml/hr + 300mbar: no complete analyses, 1 devices
  3. 10ml/hr + 350mbar: 1 partial, 1 devices
  4. 20ml/hr + 400mbar: no complete analyses, 1 devices
  5. 25ml/hr + 50mbar: 1 partial, 1 devices
  6. 30ml/hr + 100mbar: 1 partial, 1 devices
  7. 30ml/hr + 300mbar: 1 partial, 1 devices
  8. 35ml/hr + 200mbar: no complete analyses, 1 devices
  9. 35ml/hr + 350mbar: 1 partial, 1 devices
  10. 40ml/hr + 100mbar: 1 partial, 1 devices
  11. 45ml/hr + 100mbar: 1 partial, 1 devices

what i would expect to see here is do i have droplets measured and do i have frequency measured. sometimes i might have only one but i still want to know which one. 

4. **Check**: Do the numbers represent complete experimental conditions?
5. Run command: `stats w13 at 5mlhr`
6. **Check**: Does it show analysis summary with complete vs partial counts?

Analysis Summary:
  Partial Analyses:             1
  Total Raw Measurements:       72
  Unique Devices:               2

Device Breakdown:
  W13_S1_R1:
    • 5ml/hr + 200mbar (SDS_SO): no data

Droplet Size Statistics:
  Mean:    24.88 µm
  Std:     0.52 µm
  Min:     23.82 µm
  Max:     25.73 µm

Frequency Statistics:
  Mean:    9.22 Hz
  Std:     5.51 Hz
  Min:     1.04 Hz
  Max:     19.46 Hz

the device breakdown is missing the other device at 300mbar. it finds 2 unique devices but either doest show the other one and/or doesn't include it in the stats. 

### Critical Questions:
- Do the analysis counts make scientific sense to you?
- Are you getting insight into experimental completeness?
yes if the commands worked we are dine with the numbers that appear when running stats command, and it runs.
- Is it clear which devices have complete vs partial data sets?
no



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