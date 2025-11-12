# DFU-Based Plotting Implementation

## Overview

Successfully implemented DFU-based analysis plotting functionality to enable queries like:
> "Show me the droplet size across all measured DFUs for each W13 device that was tested at 5mlhr200mbar"

## Implementation Details

### 1. New Method: `plot_metric_vs_dfu()` (analyst.py)

**Location:** `src/analyst.py` (lines 878-1032)

**Purpose:** Creates multi-line plots showing how a metric (droplet size or frequency) varies across DFU rows for multiple devices.

**Features:**
- X-axis: DFU row number (1-6)
- Y-axis: Selected metric (droplet size mean or frequency mean)
- Multiple lines: One per device matching the filter criteria
- Error bars: Standard deviation for each DFU point
- Legend: Shows device IDs with color coding
- Automatic filtering by device type, flowrate, and pressure

**Parameters:**
```python
def plot_metric_vs_dfu(
    metric: str = 'droplet_size_mean',           # or 'frequency_mean'
    device_type: Optional[str] = None,           # e.g., 'W13', 'W14'
    aqueous_flowrate: Optional[int] = None,      # e.g., 5 (ml/hr)
    oil_pressure: Optional[int] = None,          # e.g., 200 (mbar)
    output_path: str = 'outputs/dfu_analysis.png'
) -> Dict
```

**Returns:**
```python
{
    'plot_path': str,               # Path to saved plot
    'metric': str,                  # Metric plotted
    'filters': List[str],           # Applied filters
    'num_devices': int,             # Number of devices plotted
    'devices': List[str],           # List of device IDs
    'dfu_rows_measured': List[int], # DFU rows with data
    'total_measurements': int       # Total data points
}
```

### 2. Query Recognition: `plot_dfu` Intent (query_processor.py)

**Location:** `src/query_processor.py` (lines 73-78)

**Added patterns to recognize DFU-based queries:**
```python
'plot_dfu': [
    r'\b(across|vs|versus)\b.*\bdfu\b',
    r'\bdfu\b.*\b(rows?|numbers?)\b',
    r'\b(show|plot|display)\b.*\b(across|for|at)\b.*\b(measured|all)\b.*\bdfu',
    r'\ball\s+measured\s+dfus?\b',
]
```

**Recognized query patterns:**
- "across all measured DFUs"
- "DFU rows"
- "show/plot/display ... across ... measured DFU"
- "all measured DFUs"

### 3. Query Handler: `_handle_plot_dfu_query()` (analyst.py)

**Location:** `src/analyst.py` (lines 1326-1375)

**Purpose:** Routes natural language queries to the `plot_metric_vs_dfu()` method.

**Workflow:**
1. Extract entities from query (device_type, flowrate, pressure, metric)
2. Call `plot_metric_vs_dfu()` with extracted parameters
3. Generate timestamped output filename
4. Return formatted success/error response with plot path

### 4. Dashboard Integration (dashboard_v2.py)

The new functionality automatically integrates with the existing dashboard through the natural language query processor. No dashboard changes were needed.

## Usage Examples

### Through Natural Language (dashboard_v2.py)

```python
from src import DataAnalyst

analyst = DataAnalyst()

# Query 1: Specific device type and parameters
query = "show me the droplet size across all measured DFUs for each w13 device that was tested at 5mlhr200mbar"
result = analyst.process_natural_language_query(query)

# Query 2: Frequency instead of droplet size
query = "show me the frequency across all measured DFUs for each w13 device at 5mlhr200mbar"
result = analyst.process_natural_language_query(query)

# Query 3: All devices of a type (no parameter filter)
query = "show droplet size across all measured DFUs for w13 devices"
result = analyst.process_natural_language_query(query)
```

### Direct Method Call

```python
from src import DataAnalyst

analyst = DataAnalyst()

# Plot droplet size vs DFU for W13 at 5mlhr/200mbar
result = analyst.plot_metric_vs_dfu(
    metric='droplet_size_mean',
    device_type='W13',
    aqueous_flowrate=5,
    oil_pressure=200,
    output_path='outputs/my_dfu_analysis.png'
)

print(f"Found {result['num_devices']} devices: {result['devices']}")
print(f"Plot saved to: {result['plot_path']}")
```

## Test Results

### Test Script: `test_dfu_plot.py`

All tests passed successfully:

**Test 1:** Specific query with full parameters
- Query: "show me the droplet size across all measured DFUs for each w13 device that was tested at 5mlhr200mbar"
- Result: Found 1 device (W13_S1_R1), 6 DFU rows measured
- Plot: Single line with error bars

**Test 2:** Frequency metric
- Query: "show me the frequency across all measured DFUs for each w13 device that was tested at 5mlhr200mbar"
- Result: Found 1 device, 30 measurements (5 ROIs × 6 DFU rows)
- Plot: Single line with error bars

**Test 3:** Multiple devices (no parameter filter)
- Query: "show droplet size across all measured DFUs for w13 devices"
- Result: Found 3 devices (W13_S1_R1, W13_S1_R2, W13_S2_R2)
- Plot: Three lines with different colors, legend showing all devices

**Test 4:** Direct method call
- Result: Successfully created plot with correct parameters

## Generated Plots

### Single Device Plot
![Single Device DFU Plot](outputs/analyst/plots/nl_query_dfu_20251030_100246.png)
- Clear title showing filters applied
- X-axis: DFU rows 1-6
- Y-axis: Droplet Size Mean (µm)
- Single line with markers and error bars
- Legend shows device ID

### Multiple Device Plot
![Multiple Device DFU Plot](outputs/analyst/plots/nl_query_dfu_20251030_100248.png)
- Three devices shown as separate lines
- Different colors for each device
- Error bars for each data point
- Legend clearly identifies devices

## Key Features

1. **Automatic Device Grouping:** Each device gets its own line on the plot
2. **Error Bars:** Standard deviation shown for each DFU point
3. **Smart Filtering:** Combines device type, flowrate, and pressure filters
4. **Clear Labeling:** Title includes all applied filters
5. **Flexible Metrics:** Works with both droplet size and frequency
6. **Integration:** Seamlessly works with existing QueryProcessor and dashboard

## File Structure

```
test_database/
├── src/
│   ├── analyst.py                    # Contains plot_metric_vs_dfu() and _handle_plot_dfu_query()
│   └── query_processor.py            # Contains plot_dfu intent patterns
├── dashboard_v2.py                    # Terminal dashboard (auto-integrated)
├── test_dfu_plot.py                   # Test script
└── outputs/
    └── analyst/
        └── plots/
            └── nl_query_dfu_*.png     # Generated plots
```

## Code Architecture

```
User Query
    ↓
QueryProcessor (query_processor.py)
    - Detects 'plot_dfu' intent
    - Extracts entities (device_type, flowrate, pressure, metric)
    ↓
DataAnalyst._handle_plot_dfu_query() (analyst.py)
    - Routes query to plotting method
    - Generates output filename
    ↓
DataAnalyst.plot_metric_vs_dfu() (analyst.py)
    - Filters data by criteria
    - Groups by device and DFU row
    - Calculates statistics (mean, std)
    - Creates matplotlib plot
    - Saves plot to file
    ↓
Returns result with plot_path
```

## Future Enhancements (Optional)

1. **Min/Max Error Bars:** Option to show min/max range instead of std dev
2. **Statistical Annotations:** Add p-values or significance markers
3. **Custom Color Palettes:** Allow user to specify device colors
4. **Interactive Plots:** Add hover tooltips with detailed statistics
5. **Subplots:** Option to create separate subplots per device
6. **Export Options:** Save data tables alongside plots

## Integration with Dashboard

Users can now access DFU plotting through:

1. **Natural Language:** Type queries directly into dashboard_v2.py
2. **Help Command:** Type 'help' to see DFU query examples
3. **Direct Method:** Import DataAnalyst and call plot_metric_vs_dfu()

## Testing

Run tests with:
```bash
cd test_database
.venv/Scripts/python.exe test_dfu_plot.py
```

Expected output:
- 4 successful tests
- 4 generated plots
- No errors or warnings

## Compatibility

- Works with existing CSV database structure
- No changes needed to data schema
- Compatible with dashboard_v2.py terminal interface
- Follows existing matplotlib styling patterns
- Uses existing logging and error handling

## Performance

- Fast plotting for typical dataset sizes (100-1000 measurements)
- Efficient groupby operations using pandas
- Plots generated in <1 second per query
- No memory issues with current dataset (612 measurements)

## Summary

The DFU-based plotting functionality is now fully implemented and tested. Users can query the system using natural language to generate multi-line plots showing how metrics vary across DFU rows for multiple devices, with automatic filtering by device type and flow parameters.
