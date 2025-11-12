# Progressive Filtering Guide

## Overview

Progressive filtering allows you to refine your queries incrementally after setting initial filters. Instead of starting over with a new command, you can add or remove filter parameters step by step, making data exploration more intuitive and efficient.

## Key Features

### 1. Incremental Filter Refinement
After setting an initial filter (e.g., `show w13 at 10mlhr`), you can continue adding parameters:
- Add specific pressures
- Filter to specific devices
- Filter by fluid type
- Filter by DFU row

### 2. Intelligent Parameter Detection
The system automatically detects parameter types:
- **Pressure**: `300mbar` or just `300` (if in pressure range 50-1000)
- **Flow rate**: `10mlhr` or just `10` (if in flow rate range 1-50)
- **Device type**: `W13`, `W14`
- **Device ID**: `W13_S1_R1`, `W13_S2_R9`, etc.
- **Fluid type**: `SDS_SO`, `NaCas_SO`, etc.
- **DFU row**: `DFU1`, `DFU2`, `DFU3`, `DFU4`

### 3. Visual Filter Progression
The prompt clearly shows your active filters:
```
>>> show w13 at 10mlhr
>>> [W13@10mlhr] 300
>>> [W13@10mlhr@300mbar] W13_S2_R9
>>> [W13@10mlhr@300mbar | W13_S2_R9] DFU1
>>> [W13@10mlhr@300mbar | W13_S2_R9,DFU1]
```

- Primary filters (device type, flow rate, pressure) are joined with `@`
- Additional filters (device ID, fluid, DFU row) appear after `|` and are comma-separated

### 4. Filter Management
Remove filters at any time:
- `remove 300mbar` - Remove specific parameter
- `undo` or `back` - Remove the last added filter
- `clear filters` - Clear all filters

## Usage Examples

### Example 1: Drilling Down from Device Type to Specific Device

```
>>> show w13 at 10mlhr
[Shows all W13 devices tested at 10ml/hr with various pressures and devices]

>>> [W13@10mlhr] 300
[Automatically adds 300mbar to filter]
[Shows results for W13 at 10ml/hr at 300mbar only]

>>> [W13@10mlhr@300mbar] W13_S2_R9
[Adds device filter]
[Shows results for W13_S2_R9 at 10ml/hr at 300mbar]

>>> [W13@10mlhr@300mbar | W13_S2_R9] DFU1
[Adds DFU row filter]
[Shows only DFU1 measurements for W13_S2_R9 at 10ml/hr at 300mbar]
```

### Example 2: Using Explicit 'show' Commands

```
>>> show w13 at 10mlhr
>>> [W13@10mlhr] show 300mbar
>>> [W13@10mlhr@300mbar] show W13_S2_R9
>>> [W13@10mlhr@300mbar | W13_S2_R9] show SDS_SO
```

Both shorthand (`300`) and explicit (`show 300mbar`) work identically.

### Example 3: Removing Filters

```
>>> show w13 at 10mlhr
>>> [W13@10mlhr] 300
>>> [W13@10mlhr@300mbar] W13_S2_R9
>>> [W13@10mlhr@300mbar | W13_S2_R9] remove 300mbar
[Removes pressure filter]
>>> [W13@10mlhr | W13_S2_R9]
```

Or use undo:
```
>>> [W13@10mlhr@300mbar | W13_S2_R9] undo
[Removes last filter (W13_S2_R9)]
>>> [W13@10mlhr@300mbar]
```

### Example 4: Filter Replacement

If you add a parameter that's already filtered, it replaces the existing value:
```
>>> show w13 at 10mlhr
>>> [W13@10mlhr] 300
>>> [W13@10mlhr@300mbar] 500
[WARNING] Replacing existing pressure filter: 300 -> 500
>>> [W13@10mlhr@500mbar]
```

## Command Reference

### Adding Filters (Progressive Mode)
Available ONLY when you have active filters set.

| Command | Effect | Example |
|---------|--------|---------|
| `<value>` | Add parameter (shorthand) | `300`, `W13_S2_R9`, `DFU1` |
| `show <value>` | Add parameter (explicit) | `show 300mbar`, `show W13_S2_R9` |

### Removing Filters

| Command | Effect | Example |
|---------|--------|---------|
| `remove <value>` | Remove specific filter | `remove 300mbar`, `remove W13_S2_R9` |
| `undo` or `back` | Remove last filter | `undo`, `back` |
| `clear filters` | Remove all filters | `clear`, `clear filters` |

### Viewing Filters

| Command | Effect |
|---------|--------|
| `show filters` | Display all active filters |

## Available Parameter Suggestions

After applying filters, the system automatically suggests available parameters you can add:

```
>>> [W13@10mlhr] 300
[Shows filtered results...]

----------------------------------------------------------------------
Available parameters to refine your filter:
  Devices: W13_S1_R1, W13_S2_R9, W13_S5_R14 ... (15 total)
  Fluids: NaCas_SO, SDS_SO
  DFU rows: DFU1, DFU2, DFU3, DFU4

Type a value to add it as a filter (e.g., '300', 'W13_S2_R9', 'DFU1')
Or use 'show <value>' for explicit filtering
----------------------------------------------------------------------
```

This helps you understand what refinements are possible based on the current results.

## Parameter Type Detection

### High Confidence Detection
The system can automatically identify these with high confidence:
- **Pressure with units**: `300mbar`, `500mbar`
- **Flow rate with units**: `10mlhr`, `5mlhr`
- **Device type**: `W13`, `W14`
- **Device ID pattern**: `W13_S1_R1`, `W14_S3_R2`
- **DFU row pattern**: `DFU1`, `DFU2`, `DFU3`, `DFU4`
- **Known fluid names**: `SDS_SO`, `NaCas_SO` (if in database)

### Number-Only Detection
When you type just a number (e.g., `300` or `10`), the system:
1. Checks if it exactly matches known values in the database
2. If exact match found → HIGH confidence
3. If not found but in typical range → LOW confidence (asks for confirmation)

**Typical ranges:**
- Pressure: 50-1000 (interpreted as mbar)
- Flow rate: 1-50 (interpreted as ml/hr)

### Low Confidence Confirmation
If the system isn't sure, it will ask:
```
>>> [W13@10mlhr] 75
Interpret '75' as pressure '75'? (y/n):
```

## Implementation Details

### Filter Storage
Filters are stored in `session_state['current_filters']` as a dictionary:
```python
{
    'device_type': 'W13',
    'flowrate': 10,
    'pressure': 300,
    'device': 'W13_S2_R9',
    'fluid': 'SDS_SO',
    'dfu': 'DFU1'
}
```

### Filter Application Order
1. **Primary filters** (device_type, flowrate, pressure) are applied via cached query
2. **Additional filters** (device, fluid, dfu) are applied to the filtered DataFrame
3. **Exclusions and outlier detection** are applied last

### Prompt Formatting Logic
```
Primary filters: device_type @ flowrate @ pressure
Additional filters: device, fluid, dfu (comma-separated)
Combined: [primary @ primary @ primary | additional, additional]
```

## Tips and Best Practices

### 1. Start Broad, Then Narrow
```
show w13 at 10mlhr      (broad: all W13 at 10ml/hr)
  -> 300                (narrower: specific pressure)
  -> W13_S2_R9          (narrower: specific device)
  -> DFU1               (narrowest: specific DFU row)
```

### 2. Use Suggestions
Look at the "Available parameters" section after each filter to see what options you have.

### 3. Remove Instead of Replace
If you want to try different values, remove the filter first:
```
>>> [W13@10mlhr@300mbar] remove 300mbar
>>> [W13@10mlhr] 500mbar
```
This is clearer than replacement.

### 4. Check Active Filters
Use `show filters` if you forget what's currently filtered:
```
>>> [W13@10mlhr@300mbar | W13_S2_R9] show filters
Active filters:
  device_type: W13
  flowrate: 10
  pressure: 300
  device: W13_S2_R9
```

### 5. Combine with Other Features
Progressive filtering works with:
- **Outlier detection**: `-outliers` toggles outlier removal
- **Manual exclusions**: `-remove W13_S5_R14 DFU1`
- **Statistics**: `stats` uses active filters
- **Plotting**: Plots respect active filters

## Troubleshooting

### "Cannot determine parameter type"
**Problem**: You entered an ambiguous value
**Solution**: Add units explicitly (e.g., `300mbar` instead of `300`)

### "No active filters to undo"
**Problem**: You tried to use `undo` without any filters set
**Solution**: Set a filter first with `show w13 at 10mlhr`

### Progressive filtering not triggering
**Problem**: You're trying to add filters without setting initial filters first
**Solution**: Progressive filtering ONLY works when you already have active filters. Start with a command like `show w13 at 10mlhr` first.

### Filter results in no data
**Problem**: The combination of filters matches nothing in the database
**Solution**:
- Use `remove <parameter>` to backtrack
- Check `show filters` to see what's active
- Use `clear filters` and start over

## Technical Architecture

### Key Methods

1. **`_detect_parameter_type(value: str) -> Dict`**
   - Detects parameter type from raw string input
   - Returns type, value, and confidence level

2. **`_cmd_add_filter_parameter(parsed: Dict)`**
   - Adds a new parameter to active filters
   - Validates and applies the filter
   - Shows available next steps

3. **`_cmd_remove_filter_parameter(parsed: Dict)`**
   - Removes a specific parameter from filters
   - Re-runs query with remaining filters

4. **`_cmd_undo_filter()`**
   - Removes the most recently added filter
   - Maintains filter order (Python 3.7+ dict ordering)

5. **`_suggest_available_parameters()`**
   - Analyzes current filtered data
   - Suggests parameters that would further refine results

### Integration Points

Progressive filtering integrates with:
- **Command parsing**: New patterns added to `parse_command()`
- **Command execution**: New handlers in `execute_command()`
- **Session state**: Filters stored in `session_state['current_filters']`
- **Prompt display**: `_get_prompt()` shows filter progression
- **Filter application**: `_cmd_filter()` stores `last_filtered_df`

## Future Enhancements

Potential improvements for future versions:
1. **Filter history navigation**: Move back/forward through filter history
2. **Named filter snapshots**: Save current filters as named bookmark
3. **Filter suggestions based on data variance**: Suggest parameters that maximize data spread
4. **Auto-complete for parameter values**: Tab completion for device IDs, fluids, etc.
5. **Filter templates**: Save common filter progressions for reuse
6. **Multi-parameter addition**: Add multiple filters in one command (`300mbar W13_S2_R9`)

---

**Version**: 1.0
**Last Updated**: 2025-11-12
**Feature Status**: Implemented and Tested
