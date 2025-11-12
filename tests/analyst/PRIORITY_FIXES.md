# Priority Fixes for Terminal UI Dashboard

**Status:** Ready for implementation
**Estimated Time:** 2-3 hours for Priority 0 fixes
**Test Coverage:** Programmatic test suite available (`test_tui_validation.py`)

---

## Priority 0: User-Blocking Bugs (FIX FIRST)

These issues were reported by the user during testing and prevent effective use of the system.

---

### Fix #1: Device Breakdown Shows All Conditions

**File:** `dashboard_v2.py`
**Line:** 592-612 (in `_cmd_filter` method)

**Problem:**
User sees "2 unique devices" but only 1 device shown in breakdown. If a device was tested at multiple pressure values, only the first condition is shown.

**Current Code:**
```python
devices_shown = set()
print("Matching Devices:")
for idx, detail in enumerate(analysis_counts['details'], 1):
    device_id = detail['condition'].split(' at ')[0]
    if device_id not in devices_shown:
        devices_shown.add(device_id)
        # ... only shows this device ONCE
```

**Fix:**
```python
devices_shown = set()
print("Matching Devices:")

# Get unique device IDs first
unique_devices = sorted(set([
    detail['condition'].split(' at ')[0]
    for detail in analysis_counts['details']
]))

# Show each device with ALL its conditions
for idx, device_id in enumerate(unique_devices, 1):
    # Get all conditions for this device
    device_details = [
        d for d in analysis_counts['details']
        if d['condition'].startswith(device_id)
    ]

    print(f"  {idx}. {device_id}:")

    # Show ALL conditions tested for this device
    for d in device_details:
        condition_part = d['condition'].split(' at ', 1)[1]
        print(f"     • {condition_part}: {d['status']}")
```

**Test:**
```bash
>>> show w13 at 5mlhr
Matching Devices:
  1. W13_S1_R1:
     • 5ml/hr + 200mbar (SDS_SO): 4 DFU rows (complete droplet)
     • 5ml/hr + 300mbar (SDS_SO): 3 DFU rows (partial)
  2. W13_S1_R2:
     • 5ml/hr + 200mbar (SDS_SO): 2 DFU rows (partial)
```

---

### Fix #2: Stats Command Shows All Devices

**File:** `dashboard_v2.py`
**Line:** 788-800 (in `_cmd_stats` method)

**Problem:**
Same issue as Fix #1 but in stats command. Shows "2 unique devices" but device breakdown only lists 1.

**Current Code:**
```python
if analysis_counts['details']:
    devices_shown = set()
    print("Device Breakdown:")
    for detail in analysis_counts['details']:
        device_id = detail['condition'].split(' at ')[0]
        if device_id not in devices_shown:
            devices_shown.add(device_id)
            # ... same bug as Fix #1
```

**Fix:**
Apply the same logic as Fix #1 - iterate through all unique devices, then show all conditions per device.

---

### Fix #3: Stats Command Accepts Session Filters

**File:** `dashboard_v2.py`
**Line:** 432-450 (in `parse_command` method) and 740-831 (in `_cmd_stats` method)

**Problem:**
User sets filters (`show w13 at 5mlhr`), then types `stats` expecting to see stats for filtered data. Instead gets error "Command 'stats' not recognized".

**Current Parsing:**
```python
# Pattern: stats w13 (original pattern)
match = re.match(r'stats\s+(w1[34])', cmd)
if match:
    return {
        'type': 'stats',
        'device_type': match.group(1).upper()
    }
```

**Fix - Add New Pattern:**
```python
# NEW: Pattern: stats (use session filters)
if cmd == 'stats':
    return {
        'type': 'stats',
        'use_session_filters': True
    }

# Existing patterns stay the same...
```

**Fix - Update `_cmd_stats` Method:**
```python
def _cmd_stats(self, parsed: Dict):
    """Show statistics with optional filtering by flow parameters."""
    # NEW: Check if should use session filters
    if parsed.get('use_session_filters'):
        session_filters = self.session_state['current_filters']

        if not session_filters:
            print()
            print("[ERROR] No active filters set.")
            print("Either set filters first ('show w13 at 5mlhr') or specify device type ('stats w13')")
            print()
            return

        device_type = session_filters.get('device_type')
        flowrate = session_filters.get('flowrate')
        pressure = session_filters.get('pressure')
    else:
        device_type = parsed.get('device_type')
        flowrate = parsed.get('flowrate')
        pressure = parsed.get('pressure')

    # Rest of method stays the same...
```

**Test:**
```bash
>>> show w13 at 5mlhr
[Filters set]

>>> stats
Statistics for device_type=W13, flowrate=5mlhr:
...
```

---

### Fix #4: Clarify Complete vs Partial Analysis Status

**File:** `dashboard_v2.py`
**Line:** 676-686 (in `_cmd_show_params` method)

**Problem:**
Output says "1 partial" but doesn't tell user if it's partial droplet data, missing frequency data, or both.

**Current Output:**
```
1. 5ml/hr + 200mbar: 1 partial, 1 devices
```

**Fix:**
```python
# Build analysis summary
analysis_parts = []

# Show droplet status explicitly
if analysis_counts['complete_droplet'] > 0:
    analysis_parts.append(f"Droplet (complete)")
elif analysis_counts['partial'] > 0:
    # Count how many DFU rows exist
    dfu_counts = group['dfu_row'].nunique()
    analysis_parts.append(f"Droplet ({dfu_counts}/4 DFU rows)")
else:
    analysis_parts.append(f"Droplet (none)")

# Show frequency status explicitly
if analysis_counts['complete_freq'] > 0:
    analysis_parts.append(f"Frequency (available)")
else:
    analysis_parts.append(f"Frequency (none)")

analysis_summary = ", ".join(analysis_parts)

print(f"  {idx}. {flowrate}ml/hr + {pressure}mbar: {analysis_summary}, {unique_devices} devices")
```

**Expected Output:**
```
1. 5ml/hr + 200mbar: Droplet (complete), Frequency (none) - 1 device
2. 5ml/hr + 300mbar: Droplet (2/4 DFU rows), Frequency (available) - 1 device
3. 10ml/hr + 350mbar: Droplet (none), Frequency (available) - 1 device
```

---

## Testing After Fixes

### 1. Run Programmatic Tests

```bash
python -X utf8 test_tui_validation.py
```

**Expected:** All tests should still pass (24/24)

---

### 2. Manual User Testing

Follow these exact commands and verify outputs:

**Test 1: Device Breakdown Completeness**
```bash
>>> show w13 at 5mlhr
```

**Verify:**
- All unique devices listed under "Matching Devices"
- Each device shows ALL tested pressure values
- Device count in summary matches number shown in breakdown

---

**Test 2: Stats with Filters**
```bash
>>> show w13 at 5mlhr
>>> stats
```

**Verify:**
- `stats` command works (no error)
- Shows statistics filtered to W13 at 5mlhr
- Device breakdown shows all devices and conditions

---

**Test 3: Stats without Filters**
```bash
>>> clear filters
>>> stats
```

**Verify:**
- Shows helpful error message
- Suggests either setting filters or providing device type
- No crash

---

**Test 4: Clear Analysis Status**
```bash
>>> show params for w13
```

**Verify:**
- Each parameter combination shows BOTH droplet AND frequency status
- Format: "Droplet (X), Frequency (Y)"
- User can tell what data exists vs what's missing

---

## Additional Test Cases to Add

Once fixes are implemented, add these tests to `test_tui_validation.py`:

```python
def test_device_breakdown_shows_all_conditions(self):
    """Verify all device conditions are shown, not just first."""
    # Get a device with multiple test conditions
    # Execute filter command
    # Parse output and count conditions shown
    # Assert: matches actual number of conditions in data
    pass

def test_stats_with_session_filters(self):
    """Verify stats command uses active session filters."""
    # Set filters
    # Execute: stats (no params)
    # Assert: no error, shows filtered stats
    pass

def test_stats_without_filters_shows_error(self):
    """Verify stats without filters gives helpful message."""
    # Clear filters
    # Execute: stats
    # Assert: error message with suggestions
    pass

def test_analysis_status_shows_both_types(self):
    """Verify analysis status shows droplet AND frequency."""
    # Execute: show params for w13
    # Parse output
    # Assert: each line has both "Droplet" and "Frequency" status
    pass
```

---

## Validation Checklist

Before marking fixes complete:

- [ ] Fix #1 implemented (device breakdown iteration)
- [ ] Fix #2 implemented (stats breakdown iteration)
- [ ] Fix #3 implemented (stats uses session filters)
- [ ] Fix #4 implemented (clear droplet/frequency status)
- [ ] Programmatic tests pass (24/24)
- [ ] Manual test cases pass (all 4 scenarios)
- [ ] User testing plan re-executed (PASS on all sequences)
- [ ] No regressions in working features
- [ ] Documentation updated (command reference)

---

## Estimated Implementation Time

| Fix | Complexity | Time |
|-----|------------|------|
| Fix #1 | Medium | 30 min |
| Fix #2 | Low (same as #1) | 15 min |
| Fix #3 | Medium | 45 min |
| Fix #4 | Medium | 30 min |
| Testing | - | 60 min |
| **Total** | | **2-3 hours** |

---

## Post-Fix Next Steps

After Priority 0 fixes are complete:

1. **Re-run User Testing Plan**
   - File: `review_docs/analyst/user_testing_plan.md`
   - Should now PASS all test sequences

2. **Update Documentation**
   - Update command syntax reference with working `stats` command
   - Remove "Known Issues" that are now fixed

3. **Priority 1 Fixes**
   - Plot confirmation flow
   - Improved NL intent detection
   - Better error messages

4. **Priority 2 Refactoring**
   - Unify parsing systems
   - Extract dashboard commands class
   - Code quality improvements

---

**Created:** 2025-11-02
**Status:** Ready for implementation
**Dependencies:** None (all fixes are independent)
**Risk Level:** Low (targeted bug fixes, no architecture changes)
