# Filter Command - Quick Reference Guide

## Command Syntax

```bash
> filter
```

Single command to launch the interactive filter builder.

---

## How It Works

The filter wizard guides you through 3 steps:

1. **Device Type** - Select W13, W14, or both
2. **Flow Rate** - Select from available flowrates (ml/hr)
3. **Pressure** - Select from available pressures (mbar)

At each step, you'll see:
- Available options based on previous selections
- Measurement counts next to each option
- Context showing what filters are active

---

## Example Session

```
> filter

======================================================================
INTERACTIVE FILTER BUILDER
======================================================================

Device Type:
  1. W13 (977 measurements)
  2. W14 (239 measurements)
  3. Both (no filter)
Select (1-3): 2

Flow Rate:
  (Available for W14)
  1. 1ml/hr (43 measurements)
  2. 5ml/hr (138 measurements)
  3. 10ml/hr (29 measurements)
  4. 15ml/hr (27 measurements)
  5. 25ml/hr (1 measurements)
  6. Any (no filter)
Select (1-6): 3

Pressure:
  (Available for W14 at 10ml/hr)
  1. 200mbar (29 measurements)
  2. Any (no filter)
Select (1-2): 1

Executing: show w14 at 10mlhr 200mbar

======================================================================

Filter: device_type=W14, flowrate=10mlhr, pressure=200mbar
Total: 29 measurements

[Results displayed...]

======================================================================
Save this filter as a preset? (y/n): y
Enter preset name: w14_standard_test
Preset 'w14_standard_test' saved successfully.
======================================================================
```

---

## Key Features

### 1. Progressive Filtering
Each step shows ONLY options that have data based on previous selections.

**Example**: If you select W14 at 10ml/hr, you'll ONLY see pressures that exist for W14 at 10ml/hr in the database.

**Result**: You CANNOT get "no data found" errors - all options shown are guaranteed to have data.

### 2. Measurement Counts
See how many measurements each option has before selecting it.

```
  1. 5ml/hr (138 measurements)
  2. 10ml/hr (29 measurements)
```

This helps you choose options with sufficient data for analysis.

### 3. Clear Context
At each step, you see what filters are already active:

```
Pressure:
  (Available for W14 at 10ml/hr)
```

This prevents confusion about what you're filtering.

### 4. "Any" Option
At each step, you can choose "Any (no filter)" to skip that filter category.

**Example**:
- Select W14
- Select 5ml/hr
- Select "Any" for pressure
- Result: Shows all W14 devices at 5ml/hr regardless of pressure

### 5. Preset Saving
After building a custom filter, you're prompted to save it as a preset.

```
Save this filter as a preset? (y/n): y
Enter preset name: my_filter
```

Next time, you can load the preset instantly instead of rebuilding it.

---

## Common Use Cases

### Use Case 1: Standard Device Test
**Goal**: Analyze W13 devices at standard testing conditions (5ml/hr, 150mbar)

```
> filter
  Select: 1 (W13)
  Select: 2 (5ml/hr)
  Select: 3 (150mbar)
  Save as: "w13_standard"
```

### Use Case 2: Compare All Flowrates for W14
**Goal**: See all W14 measurements at any flowrate and pressure

```
> filter
  Select: 2 (W14)
  Select: 7 (Any flowrate)
  Select: (Any pressure)
```

### Use Case 3: High-Pressure Testing
**Goal**: Find all devices tested at high pressure (300mbar+)

```
> filter
  Select: 3 (Both device types)
  Select: (Any flowrate)
  Select: 6 (300mbar) [or higher]
```

### Use Case 4: Low-Flow Analysis
**Goal**: Analyze devices at low flowrate (1ml/hr)

```
> filter
  Select: 3 (Both device types)
  Select: 1 (1ml/hr)
  Select: (Any pressure)
```

---

## Tips

1. **Start broad, then narrow**: Select device type first, then flowrate, then pressure
2. **Check measurement counts**: Choose options with enough data for meaningful analysis (>10 measurements recommended)
3. **Use presets**: Save commonly used filters as presets to avoid rebuilding them
4. **Combine with other commands**: After filtering, use `stats`, `list`, `count`, etc.

---

## Related Commands

After using `filter`, you can:

```bash
> stats              # Show statistics for filtered data
> list               # List all measurements in filtered data
> count              # Count measurements by device
> show filters       # See currently active filters
> clear filters      # Clear all filters
> presets            # Manage saved presets
```

---

## Preset Management

### View Presets
```bash
> presets
```

### Load Preset
```bash
> presets
  [L] Load preset
  Enter number: 1
```

### Delete Preset
```bash
> presets
  [D] Delete preset
  Enter number: 2
```

---

## Troubleshooting

### Problem: No options shown at a step
**Cause**: The combination you've selected has no data in the database.

**Solution**: Go back and select a different option at the previous step.

**Note**: This should be rare with progressive filtering - only happens if you skip earlier filters.

### Problem: Only one option shown
**Cause**: Your previous selections narrow down to only one valid option.

**Example**: W14 at 10ml/hr has ONLY 200mbar data.

**Solution**: This is correct behavior - select the option or choose "Any (no filter)" to broaden the search.

### Problem: Want to change earlier selection
**Cause**: You made a selection but want to change it.

**Solution**: Exit the wizard (Ctrl+C) and restart with `filter`.

---

## Comparison with Direct Filter Commands

You can also filter directly without the wizard:

```bash
# Using filter wizard
> filter
  [Interactive selections...]

# Using direct command
> show w13 at 5mlhr 150mbar
```

**When to use filter wizard**:
- Exploring the data (don't know exact parameters)
- Want to see available options
- Building complex filters with multiple conditions

**When to use direct commands**:
- Know exact parameters
- Repeating a previous filter
- Want faster workflow

---

## Advanced: Combining with Other Features

### Filter + Outlier Detection
```bash
> -outliers          # Enable outlier detection
> filter             # Build filter
  [Results will exclude outliers]
```

### Filter + Manual Exclusions
```bash
> -remove W13_S5_R14 DFU1    # Exclude specific device
> filter                     # Build filter
  [Results will exclude W13_S5_R14 DFU1]
```

### Filter + Repeat Last
```bash
> filter             # Build and execute filter
> repeat last        # Repeat the same filter
```

---

## Summary

The `filter` command provides an intelligent, user-friendly way to build database queries without needing to know exact syntax or valid parameter combinations.

**Key Benefits**:
- No "no data found" errors
- See measurement counts before selecting
- Save commonly used filters as presets
- Clear context at each step

**Recommended For**:
- First-time users
- Exploratory data analysis
- Building complex multi-parameter filters
- Anyone who wants to see available options
