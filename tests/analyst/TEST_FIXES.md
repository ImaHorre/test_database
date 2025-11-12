# Quick Test Plan for 4 Priority Fixes

## Setup
```bash
python dashboard_v2.py
```

---

## Test 1: Device Breakdown Completeness (Fix #1)

**Command:**
```
show w13 at 5mlhr
```

**Expected:**
- Should see device breakdown section
- Each device (W13_S1_R1, etc.) should show ALL pressure values tested at 5mlhr
- Device count in summary should match number of devices listed



its still doing the same thing: >>> show w13 at 5mlhr

Filter: device_type=W13, flowrate=5mlhr
Found: 1 partial analysis

Matching Devices:
  1. W13_S1_R1:
     • 5ml/hr + 200mbar (SDS_SO): no data			(why only one device here and what is the no data thing)

Flow Parameter Combinations in Results:
  1. 5ml/hr + 200mbar (SDS_SO): 1 devices
  2. 5ml/hr + 300mbar (SDS_SO): 1 devices

Droplet Size: 24.88 ± 0.52 µm
Frequency:    9.22 ± 5.51 Hz




---

## Test 2: Stats with Session Filters (Fix #3)

**Commands:**
```
show w13 at 5mlhr
stats
```

**Expected:**
- First command sets filters (prompt changes to `>>> [W13@5mlhr]`)
- Second command `stats` should work WITHOUT error
- Should show stats filtered to W13 at 5mlhr
- Device breakdown should show all devices and conditions



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

we are missing a device/condition, and again what is the no data thing. 

**Then test without filters:**
```
clear filters


change this command to just  'clear' 


stats
```

**Expected:**
- Should get helpful error message
- Should suggest either setting filters OR providing device type


working fine 
---

## Test 3: Stats Device Breakdown (Fix #2)

**Command:**
```
stats w13
```

**Expected:**
- Device Breakdown section should list ALL W13 devices
- Each device should show ALL test conditions (not just first one)
- Should see W13_S1_R1 with ~6 conditions, W13_S1_R2 with 2 conditions



--------------------------------------------------
Analysis Summary:
  Partial Analyses:             8
  Total Raw Measurements:       396
  Unique Devices:               3

Device Breakdown:
  W13_S1_R1:
    • 5ml/hr + 200mbar (SDS_SO): no data
    • 30ml/hr + 100mbar (SDS_SO): no data
    • 40ml/hr + 100mbar (SDS_SO): no data
    • 10ml/hr + 350mbar (NaCas_SO): no data
    • 35ml/hr + 350mbar (NaCas_SO): no data
    • 45ml/hr + 100mbar (NaCas_SO): no data
  W13_S1_R2:
    • 25ml/hr + 50mbar (NaCas_SO): no data
    • 30ml/hr + 300mbar (NaCas_SO): no data

Droplet Size Statistics:
  Mean:    24.97 µm
  Std:     0.39 µm
  Min:     23.82 µm
  Max:     25.76 µm

Frequency Statistics:
  Mean:    10.24 Hz
  Std:     5.52 Hz
  Min:     1.04 Hz
  Max:     19.90 Hz

Flow Parameters Tested: 11
  • 5ml/hr + 200mbar: 36 raw measurements
  • 5ml/hr + 300mbar: 36 raw measurements
  • 10ml/hr + 350mbar: 36 raw measurements
  • 20ml/hr + 400mbar: 36 raw measurements
  • 25ml/hr + 50mbar: 36 raw measurements
  • 30ml/hr + 100mbar: 36 raw measurements
  • 30ml/hr + 300mbar: 36 raw measurements
  • 35ml/hr + 200mbar: 36 raw measurements
  • 35ml/hr + 350mbar: 36 raw measurements
  • 40ml/hr + 100mbar: 36 raw measurements
  • 45ml/hr + 100mbar: 36 raw measurements
---

3 unique devvices but only two listed, showing no data for all...should be shoing the numbner of DFU measures and Freq measures for each. (all we have to do here is read if there is a droplet measure avg and or a freq measure avg attributed in teh database row if yes its a droplet measure test done. We want to present a similar thing when dispaying the flow parameters if all 3 devices had tested for example 5mlhr+200mbar once each then we would see here 3 droplet and 3 frequency measurements. 


## Test 4: Clear Analysis Status (Fix #4)

**Command:**
```
show params for w13

Flow Parameter Combinations for W13:

  1. 5ml/hr + 200mbar: Droplet (6/4 DFU rows), Frequency (none) - 1 device
  2. 5ml/hr + 300mbar: Droplet (none), Frequency (none) - 1 device
  3. 10ml/hr + 350mbar: Droplet (6/4 DFU rows), Frequency (none) - 1 device
  4. 20ml/hr + 400mbar: Droplet (none), Frequency (none) - 1 device
  5. 25ml/hr + 50mbar: Droplet (6/4 DFU rows), Frequency (none) - 1 device
  6. 30ml/hr + 100mbar: Droplet (6/4 DFU rows), Frequency (none) - 1 device
  7. 30ml/hr + 300mbar: Droplet (6/4 DFU rows), Frequency (none) - 1 device
  8. 35ml/hr + 200mbar: Droplet (none), Frequency (none) - 1 device
  9. 35ml/hr + 350mbar: Droplet (6/4 DFU rows), Frequency (none) - 1 device
  10. 40ml/hr + 100mbar: Droplet (6/4 DFU rows), Frequency (none) - 1 device
  11. 45ml/hr + 100mbar: Droplet (6/4 DFU rows), Frequency (none) - 1 device


is this just a fult of the fake folder/database we have? 6/4 is meaning becuase we set full to be 4 dfus. lets just presetn '6 dfu rows measured' we coudl also present if it is possilb ewiht the current backend setup the total DFUs measured (sum all ROIs for that device/parameter test, meaning we mayb have 5 roi for each DFU row = 5*6=36 DFUs. frequency is recorning as none. but the data is tehre on teh database. 
```

**Expected:**
- Each line should show format: `Droplet (X), Frequency (Y)`
- Should see things like:
  - `Droplet (6/4 DFU rows), Frequency (none)`
  - `Droplet (complete), Frequency (available)` (if any exist)
  - `Droplet (none), Frequency (none)`
- NO ambiguous "1 partial" without context

---

## Edge Case Tests (Pushing Limits)

### Should Work:
```
show w14
show w13 at 10mlhr
show w14 at 25mlhr
stats w14
show params for w14
list devices
list types
show all flow parameter combinations
```

### Maybe Works (Test boundaries):
```
stats w13 at 5mlhr 200mbar
stats w14 at 10mlhr
show w13 at 5mlhr 200mbar 300mbar
show params w13
```


>>> show w13 at 5mlhr 200mbar 300mbar

Filter: device_type=W13, flowrate=5mlhr, pressure=200mbar
Found: 1 partial analysis

Matching Devices:
  1. W13_S1_R1:
     • 5ml/hr + 200mbar (SDS_SO): no data

Flow Parameter Combinations in Results:
  1. 5ml/hr + 200mbar (SDS_SO): 1 devices

Droplet Size: 25.01 ± 0.57 µm
Frequency:    8.59 ± 4.95 Hz

>>> [W13@5mlhr@200mbar] 

only pickign up the first pressure command clear filters

### Should Fail Gracefully:
```
show w15
show w13 at 999mlhr
stats
stats w13 w14
random garbage command
```

---

## Session State Tests

**Test filter persistence:**
```
show w13 at 5mlhr
show params for w13
clear filters
show params for w13
```

**Expected:**
- First `show params` should use W13 filters from session
- After clear, `show params` should show all W13 data

**Test prompt updates:**
```
show w13
show w13 at 5mlhr
show w13 at 5mlhr 200mbar
clear filters
```

**Expected:**
- Prompt should update each time: `>>> [W13]` → `>>> [W13@5mlhr]` → `>>> [W13@5mlhr+200mbar]` → `>>>`

---

## Quick Smoke Test (All working commands)

Run these in sequence - all should work:
```
list devices
show w13
show w13 at 5mlhr
stats
clear filters
stats w13
show params for w13
show all flow parameter combinations
history
show filters
```

---

## Notes for Testing

- ✅ = Works as expected
- ⚠️ = Works but with issues
- ❌ = Broken or unexpected behavior

Add your observations next to each test.
