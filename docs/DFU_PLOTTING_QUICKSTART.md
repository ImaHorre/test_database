# DFU Plotting - Quick Start Guide

## What is DFU Plotting?

DFU (Device From Uniformity) plotting allows you to visualize how a measurement metric varies across different DFU rows for one or more devices. Each device appears as a separate line on the plot, making it easy to compare device performance across DFU positions.

## How to Use

### Option 1: Terminal Dashboard (Recommended)

```bash
cd test_database
.venv/Scripts/python.exe dashboard_v2.py
```

Then type your query:
```
>>> show me the droplet size across all measured DFUs for each w13 device that was tested at 5mlhr200mbar
```

### Option 2: Python Script

```python
from src import DataAnalyst

analyst = DataAnalyst()

# Natural language query
result = analyst.process_natural_language_query(
    "show droplet size across all measured DFUs for w13 devices at 5mlhr200mbar"
)

# Or direct method call
result = analyst.plot_metric_vs_dfu(
    metric='droplet_size_mean',
    device_type='W13',
    aqueous_flowrate=5,
    oil_pressure=200
)

print(f"Plot saved to: {result['plot_path']}")
```

## Query Examples

### Basic Queries

**Single device type, specific parameters:**
```
show droplet size across all measured DFUs for w13 at 5mlhr200mbar
```

**All devices of a type:**
```
show droplet size across all measured DFUs for w13 devices
```

**Frequency instead of droplet size:**
```
show frequency across all measured DFUs for w13 at 5mlhr200mbar
```

### Advanced Queries

**Multiple devices, no parameter filter:**
```
plot droplet size vs DFU rows for all w13 devices
```

**Specific device and pressure only:**
```
show droplet size across DFUs for w14 at 300mbar
```

**Specific device and flowrate only:**
```
display frequency across all measured DFUs for w13 at 30mlhr
```

## What You Get

### Plot Features
- **X-axis:** DFU row number (1-6)
- **Y-axis:** Your chosen metric (droplet size or frequency)
- **Multiple lines:** One per device (automatically color-coded)
- **Error bars:** Standard deviation for each DFU point
- **Legend:** Shows which color corresponds to which device
- **Title:** Shows all applied filters

### Return Information
```python
{
    'plot_path': 'outputs/analyst/plots/nl_query_dfu_20251030_100454.png',
    'metric': 'droplet_size_mean',
    'filters': ['device_type=W13', 'flowrate=5mlhr', 'pressure=200mbar'],
    'num_devices': 1,
    'devices': ['W13_S1_R1'],
    'dfu_rows_measured': [1, 2, 3, 4, 5, 6],
    'total_measurements': 6
}
```

## Filtering Options

You can filter by any combination of:
- **Device Type:** W13, W14, etc.
- **Flowrate:** 5, 10, 20, 30, etc. (ml/hr)
- **Pressure:** 100, 200, 300, etc. (mbar)

If you don't specify a filter, all matching devices will be included.

## Common Use Cases

### 1. Compare specific test condition
**Goal:** See how all W13 devices performed at 5mlhr/200mbar across all DFU positions

**Query:**
```
show droplet size across all measured DFUs for w13 at 5mlhr200mbar
```

**Result:** One line per W13 device tested at those parameters

---

### 2. Compare all devices of a type
**Goal:** See variation across all W13 devices regardless of test parameters

**Query:**
```
show droplet size across all measured DFUs for w13 devices
```

**Result:** Multiple lines showing all W13 devices (different test conditions)

---

### 3. Check frequency variation
**Goal:** See how droplet frequency varies across DFU rows

**Query:**
```
show frequency across all measured DFUs for w13 at 5mlhr200mbar
```

**Result:** Frequency plot instead of droplet size

---

### 4. Single device, specific flowrate
**Goal:** See one device at a specific flowrate across all pressures

**Query:**
```
show droplet size across DFUs for w13 at 5mlhr
```

**Result:** All W13 devices tested at 5mlhr (any pressure)

## Tips

1. **Be specific:** More filters = fewer devices on plot (clearer visualization)
2. **Start broad:** Try without parameters first to see all available data
3. **Check legend:** Multiple lines can overlap - check the legend for device IDs
4. **Error bars:** Larger error bars = more variation at that DFU position
5. **Use help:** Type `help` in dashboard to see more query examples

## Troubleshooting

**No data found:**
- Check spelling of device type (W13, not w-13)
- Verify parameters exist (use `show params for w13` to see available)
- Try broader query (remove some filters)

**Too many devices on plot:**
- Add more specific filters (flowrate AND pressure)
- Filter by single test condition

**Can't see error bars:**
- May be too small to display at current scale
- Try zooming in on saved plot image

## Files and Locations

**Plots saved to:**
```
test_database/outputs/analyst/plots/nl_query_dfu_TIMESTAMP.png
```

**Test script:**
```bash
.venv/Scripts/python.exe test_dfu_plot.py
```

**Dashboard:**
```bash
.venv/Scripts/python.exe dashboard_v2.py
```

## Next Steps

1. Try the example queries above
2. Experiment with different filters
3. Compare your results across different test conditions
4. Use the plots in presentations or reports

---

**Need Help?**
Type `help` in the dashboard or see `DFU_PLOTTING_IMPLEMENTATION.md` for technical details.
