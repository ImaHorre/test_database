# Context-Aware DFU Plotting

## Overview

The enhanced `plot_metric_vs_dfu()` method now automatically detects which parameters **vary** in your filtered dataset and includes them in the plot legend and title. This solves the problem where plots showed device IDs without explaining **why** different devices had different results.

## The Problem (Before)

**User Query:** "show droplet size across all measured DFUs for w13 devices at 5mlhr"

**Result:** 2 devices found
- W13_S1_R1 (tested at 200mbar)
- W13_S2_R1 (tested at 300mbar)

**Issue:** Plot legend only showed:
```
W13_S1_R1
W13_S2_R1
```

**User couldn't tell from the legend that pressure was the key differentiator!**

## The Solution (After)

Same query now produces a legend like:
```
W13_S1_R1 (200mbar)
W13_S2_R1 (300mbar)
```

**And the title shows:** "Droplet Size Mean (µm) vs DFU Row for W13 devices (Multiple Pressures)"

## How It Works

### 1. Automatic Parameter Detection

The system analyzes your filtered data and identifies which parameters have **multiple unique values**:

```python
# Always checked (core operational parameters):
- oil_pressure
- aqueous_flowrate
- device_type
- aqueous_fluid
- oil_fluid

# Checked only if mentioned in query (metadata):
- testing_date (if query contains "date", "test date", "when tested")
- bond_date (if query contains "bond", "bonding")
- wafer (if query contains "wafer")
- shim (if query contains "shim")
```

### 2. Context-Aware Legend Generation

For each device, the legend includes values for **only the parameters that vary**:

**Example scenarios:**

| Varying Parameters | Legend Format |
|-------------------|---------------|
| Pressure only | `W13_S1_R1 (200mbar)` |
| Flowrate only | `W13_S1_R1 (5ml/hr)` |
| Both fluids | `W13_S1_R1 (NaCas+SO)` |
| Pressure + Fluids | `W13_S1_R1 (300mbar, SDS+SO)` |
| Nothing varies | `W13_S1_R1` |

### 3. Enhanced Plot Titles

Titles now indicate what varies:

- **Multiple pressures:** "Droplet Size vs DFU for W13 devices (Multiple Pressures)"
- **Multiple fluids:** "Droplet Size vs DFU for W13 devices (Multiple Fluids)"
- **Multiple conditions:** "Droplet Size vs DFU for W13 devices (Multiple Pressures, Multiple Fluids)"
- **Fixed conditions:** "Droplet Size vs DFU for W13 devices (5ml/hr, 200mbar)"

## Usage Examples

### Example 1: Compare devices at same flowrate, different pressures

```python
analyst.plot_metric_vs_dfu(
    metric='droplet_size_mean',
    device_type='W13',
    aqueous_flowrate=5,  # Fixed
    oil_pressure=None,   # Let it vary
    output_path='outputs/w13_varying_pressure.png'
)
```

**Result:**
- Legend shows pressure for each device
- Title indicates "Multiple Pressures"

### Example 2: Compare across all conditions

```python
analyst.plot_metric_vs_dfu(
    metric='droplet_size_mean',
    device_type='W13',
    aqueous_flowrate=None,  # Vary
    oil_pressure=None,      # Vary
    output_path='outputs/w13_all_conditions.png'
)
```

**Result:**
- Legend shows flowrate AND pressure for each device
- Title indicates both vary

### Example 3: Include test dates in comparison

```python
analyst.plot_metric_vs_dfu(
    metric='droplet_size_mean',
    device_type='W13',
    aqueous_flowrate=5,
    oil_pressure=200,
    query_text='show droplet size across DFUs for W13 at 5mlhr 200mbar on different test dates',
    output_path='outputs/w13_with_dates.png'
)
```

**Result:**
- Legend includes test dates (because query mentioned "test dates")
- Shows temporal variation

### Example 4: Natural language query

```python
query = "show droplet size across all measured DFUs for w13 devices at 5mlhr"
analyst.process_natural_language_query(query)
```

**Result:**
- Automatically detects varying pressure
- Generates context-aware plot
- Returns message explaining what was detected

## Technical Implementation

### Parameter Variation Detection

```python
def _detect_varying_parameters(data, query_text):
    """
    Analyzes filtered data to find parameters with multiple values.

    Returns list like: ['oil_pressure', 'aqueous_fluid']
    """
    varying_params = []

    # Check core parameters
    for param in ['oil_pressure', 'aqueous_flowrate', ...]:
        if len(data[param].unique()) > 1:
            varying_params.append(param)

    # Check metadata if mentioned in query
    if query_text and 'test date' in query_text.lower():
        if len(data['testing_date'].unique()) > 1:
            varying_params.append('testing_date')

    return varying_params
```

### Label Generation

```python
def _generate_context_label(device_id, device_data, varying_params):
    """
    Builds label with context info.

    Example: "W13_S1_R1 (200mbar, NaCas+SO)"
    """
    context_info = []

    for param in varying_params:
        value = device_data[param].mode()[0]  # Most common value

        if param == 'oil_pressure':
            context_info.append(f"{int(value)}mbar")
        elif param == 'aqueous_flowrate':
            context_info.append(f"{int(value)}ml/hr")
        elif param in ['aqueous_fluid', 'oil_fluid']:
            # Combine if both vary
            context_info.append(f"{aq_fluid}+{oil_fluid}")
        # ... etc

    return f"{device_id} ({', '.join(context_info)})"
```

### Title Generation

```python
def _generate_context_title(ylabel, filter_desc, varying_params, device_type):
    """
    Creates informative title showing what varies.

    Example: "Droplet Size vs DFU for W13 devices (Multiple Pressures)"
    """
    title = f"{ylabel} vs DFU Row"

    if varying_params:
        variations = []
        if 'oil_pressure' in varying_params:
            variations.append('Multiple Pressures')
        if 'aqueous_flowrate' in varying_params:
            variations.append('Multiple Flowrates')
        # ... etc

        title += f" for {device_type} devices ({', '.join(variations)})"

    return title
```

## Benefits

1. **Clarity:** Users immediately understand why lines differ
2. **Self-documenting:** Plots explain themselves without external context
3. **Flexibility:** Works with any combination of varying parameters
4. **Smart defaults:** Only shows what's relevant
5. **Query-aware:** Respects user's intent when they mention specific metadata

## API Changes

### New Parameter

```python
plot_metric_vs_dfu(
    metric='droplet_size_mean',
    device_type=None,
    aqueous_flowrate=None,
    oil_pressure=None,
    output_path='outputs/dfu_analysis.png',
    query_text=None  # NEW: Original query text for context detection
)
```

### Enhanced Return Value

```python
{
    'plot_path': 'outputs/...',
    'metric': 'droplet_size_mean',
    'filters': ['device_type=W13', 'flowrate=5ml/hr'],
    'num_devices': 2,
    'devices': ['W13_S1_R1', 'W13_S2_R1'],
    'dfu_rows_measured': [1, 2, 3, 4, 5],
    'total_measurements': 50,
    'varying_parameters': ['oil_pressure']  # NEW: Shows what varies
}
```

## Dashboard Integration

The feature works seamlessly with `dashboard_v2.py`:

```python
# User types natural language query
>>> show droplet size across all measured DFUs for w13 devices at 5mlhr

# System automatically:
# 1. Detects query intent
# 2. Filters data
# 3. Identifies varying parameters
# 4. Generates context-aware plot
# 5. Returns informative message

[Success]

DFU analysis complete!

Metric: droplet_size_mean
Found 2 device(s):
  - W13_S1_R1
  - W13_S2_R1

DFU rows measured: 1, 2, 3, 4, 5
Total measurements: 50

Varying parameters detected: oil_pressure
(Legend includes context for differentiating devices)

Filters applied: device_type=W13, flowrate=5ml/hr

Plot saved: outputs/analyst/plots/nl_query_dfu_20251030_143022.png
```

## Testing

Run the test script to verify functionality:

```bash
python test_context_aware_dfu.py
```

This tests:
- ✓ Varying pressure detection
- ✓ Multiple parameter variations
- ✓ Single condition (no variation)
- ✓ Query-based date inclusion
- ✓ Natural language integration

## Future Enhancements

Potential additions:
- Statistical significance annotations when comparing pressures/flowrates
- Color-coding by parameter (e.g., all 200mbar devices in blue)
- Automatic grouping of similar conditions
- Interactive tooltips showing full metadata
- Export legend as separate table for reports

## Summary

**Before:** "Why are these lines different?"

**After:** "Ah, W13_S1_R1 was tested at 200mbar and W13_S2_R1 at 300mbar - now I understand!"

The plot tells the full story.
