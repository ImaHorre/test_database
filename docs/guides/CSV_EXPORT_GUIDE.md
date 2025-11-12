# CSV Export Feature - Usage Guide

## Overview

The CSV export feature in `dashboard_v2.py` allows you to export filtered data from the database to a standalone CSV file for further analysis in Excel, Python, R, or other tools.

## Key Features

- **Filter-aware**: Exports only the data matching your current filter settings
- **Automatic naming**: Generates descriptive filenames based on applied filters
- **Timestamp-based**: Each export includes a timestamp to avoid overwriting previous exports
- **Full data export**: Includes all 35 columns from the database (device info, flow parameters, measurements, metadata)
- **Exclusion-aware**: Respects outlier detection and manual exclusions if enabled

## How to Use

### Basic Usage

1. **Set your filters** (optional):
   ```
   >>> show w13 at 5mlhr 200mbar
   ```

2. **Export the filtered data**:
   ```
   >>> export
   ```

3. **Find your file** in the `outputs/` directory with a name like:
   ```
   W13_5mlhr_200mbar_export_20251112_130556.csv
   ```

### Command Aliases

All of these commands do the same thing:
- `export`
- `export csv`
- `save`
- `save csv`

### Example Workflows

#### Export all W13 devices
```
>>> show w13
>>> export
```
Output: `W13_export_[timestamp].csv`

#### Export specific flow parameters
```
>>> show w13 at 10mlhr 200mbar
>>> export
```
Output: `W13_10mlhr_200mbar_export_[timestamp].csv`

#### Export with progressive filters
```
>>> show w13 at 5mlhr
>>> 300mbar
>>> W13_S2_R9
>>> export
```
Output: `W13_5mlhr_300mbar_W13_S2_R9_export_[timestamp].csv`

#### Export entire database
```
>>> clear filters
>>> export
```
Output: `all_data_export_[timestamp].csv`

#### Export with outlier detection
```
>>> show w13 at 5mlhr
>>> -outliers
>>> export
```
The exported CSV will exclude outliers detected by the Modified Z-Score method.

## Exported Data Structure

The exported CSV contains **all 35 columns** from the database:

### Device Information
- `device_type` (W13, W14)
- `device_id` (W13_S1_R2, etc.)
- `wafer`, `shim`, `replica`

### Experimental Conditions
- `bonding_date`, `testing_date`
- `aqueous_fluid`, `oil_fluid`
- `aqueous_flowrate`, `aqueous_flowrate_unit`
- `oil_pressure`, `oil_pressure_unit`

### Measurement Details
- `measurement_type` (dfu_measure, freq_analysis)
- `dfu_row` (1-6)
- `roi` (region of interest)
- `measurement_area` (_B, _C, etc.)
- `timepoint` (_t0, _t1, etc.)

### Results
- `droplet_size_mean`, `droplet_size_std`, `droplet_size_min`, `droplet_size_max`, `droplet_count`
- `frequency_mean`, `frequency_min`, `frequency_max`, `frequency_count`

### Metadata
- `file_name`, `file_type`
- `parse_quality`, `date_validation_warning`
- `raw_path`, `download_url`
- `scan_timestamp`, `extraction_timestamp`

## Export Summary

After each export, you'll see a summary like:

```
[OK] Exported 69 measurements to:
  C:\Users\...\outputs\W13_10mlhr_200mbar_export_20251112_130556.csv

Export summary:
  • 69 measurements
  • 2 devices
  • 1 flow/pressure combinations
  • Date range: 2025-10-13 to 2025-10-30
```

## File Location

All exports are saved to:
```
C:\Users\conor\Documents\Code Projects\test_database\outputs\
```

## Error Handling

If you try to export with filters that return no data:
```
>>> show w13 at 999mlhr
>>> export

[ERROR] No data to export. Current filters return 0 measurements.
```

## Tips

1. **Use descriptive filters before exporting** - This creates meaningful filenames
2. **Exports are cumulative** - Previous exports are never overwritten (thanks to timestamps)
3. **Clear filters to export everything** - Use `clear filters` then `export` for full database export
4. **Verify in help** - Type `help` or `h` to see the DATA EXPORT section

## Integration with Analysis

Example Python workflow after export:

```python
import pandas as pd
import matplotlib.pyplot as plt

# Load exported data
df = pd.read_csv('outputs/W13_5mlhr_200mbar_export_20251112_130556.csv')

# Analyze
print(df.groupby('device_id')['droplet_size_mean'].mean())

# Plot
df.groupby('device_id')['droplet_size_mean'].mean().plot(kind='bar')
plt.ylabel('Mean Droplet Size (μm)')
plt.title('W13 Devices at 5ml/hr 200mbar')
plt.show()
```

## Troubleshooting

**Q: Where are my exports saved?**
A: Always in the `outputs/` directory at the project root.

**Q: Can I customize the filename?**
A: Currently no, but filenames are automatically descriptive based on your filters.

**Q: Does export include outliers?**
A: Only if outlier detection is disabled. Enable with `-outliers` before exporting to exclude outliers.

**Q: What if the outputs/ directory doesn't exist?**
A: It will be created automatically on first export.

---

**Last Updated:** 2025-11-12
**Dashboard Version:** dashboard_v2.py
