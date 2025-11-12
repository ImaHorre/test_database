# Plot Configuration Schema

## Overview

This document defines the JSON schema for plot configurations in the microfluidic device analysis system. Each configuration file describes how to generate a specific type of plot from filtered CSV data.

## Design Principles

1. **Data-agnostic**: Configs reference column names, not specific values (e.g., "W13" or "SDS")
2. **Reusable**: Same config can generate plots from any filtered CSV with matching columns
3. **Declarative**: Describe *what* to plot, not *how* to implement it
4. **Extensible**: Easy to add new plot types and options

## PlotConfig Schema

```json
{
  "name": "string (required)",
  "description": "string (required)",
  "version": "string (optional, default: '1.0')",

  "axes": {
    "x": "string (required) - column name for x-axis",
    "y": "string or array (required) - column name(s) for y-axis",
    "y_error": "string or null (optional) - column for error bars"
  },

  "grouping": {
    "group_by": "string or null (optional) - column for series/color grouping",
    "facet_row": "string or null (optional) - column for row facets",
    "facet_col": "string or null (optional) - column for column facets"
  },

  "aggregation": {
    "method": "none | mean | median (required)",
    "group_cols": "array of strings (optional) - columns to group by before aggregating",
    "error_method": "none | std | sem | ci95 (optional)"
  },

  "style": {
    "plot_type": "line | scatter | line+markers | bar | box | violin (required)",
    "color_scheme": "default | vibrant | pastel | dark | earth | custom (optional)",
    "marker_size": "number (optional, default: 6)",
    "line_width": "number (optional, default: 2)",
    "alpha": "number 0-1 (optional, default: 0.8)",
    "show_grid": "boolean (optional, default: true)",
    "show_legend": "boolean (optional, default: true)",
    "legend_position": "best | upper right | upper left | lower right | lower left | outside (optional)"
  },

  "scales": {
    "x_scale": "linear | log | symlog (optional, default: 'linear')",
    "y_scale": "linear | log | symlog (optional, default: 'linear')",
    "x_limits": "[min, max] or null (optional)",
    "y_limits": "[min, max] or null (optional)"
  },

  "labels": {
    "title": "string (optional) - supports {column_name} placeholders",
    "x_label": "string (optional)",
    "y_label": "string (optional)",
    "legend_title": "string or null (optional)"
  },

  "figure": {
    "width": "number (optional, default: 10)",
    "height": "number (optional, default: 6)",
    "dpi": "number (optional, default: 300)"
  },

  "advanced": {
    "sort_x": "boolean (optional, default: false) - sort data by x before plotting",
    "sort_legend": "boolean (optional, default: true) - sort legend entries",
    "show_counts": "boolean (optional, default: false) - add n= to legend",
    "connect_points": "boolean (optional, default: true for line plots)",
    "fill_between": "boolean (optional, default: false) - fill area under line"
  }
}
```

## Column Name Reference

Available columns from `database.csv`:

### Device Identification
- `device_type` - W13, W14
- `device_id` - Full ID (e.g., W13_S1_R2)
- `wafer`, `shim`, `replica` - Components of device ID

### Experimental Parameters
- `bonding_date` - Device bonding date
- `testing_date` - Measurement date
- `aqueous_fluid` - Aqueous phase fluid (SDS, NaCas, etc.)
- `oil_fluid` - Oil phase fluid (SO, etc.)
- `aqueous_flowrate` - Flowrate value (numeric)
- `aqueous_flowrate_unit` - Usually "ml/hr"
- `oil_pressure` - Pressure value (numeric)
- `oil_pressure_unit` - Usually "mbar"

### Measurement Location
- `measurement_type` - "droplet" or "frequency"
- `dfu_row` - DFU row number (1-6)
- `roi` - Region of interest (1-3)
- `measurement_area` - Area suffix (A, B, C, etc.)
- `timepoint` - Time series index (0, 1, 2, etc.)

### Measurement Values
- `droplet_size_mean` - Mean droplet diameter (µm)
- `droplet_size_std` - Standard deviation
- `droplet_size_min`, `droplet_size_max` - Range
- `droplet_count` - Number of droplets measured
- `frequency_mean` - Mean droplet generation frequency (Hz)
- `frequency_min`, `frequency_max` - Range
- `frequency_count` - Number of frequency measurements

### Metadata
- `parse_quality` - Quality flag
- `date_validation_warning` - Warning flag
- `file_name`, `file_type` - Source file info
- `raw_path`, `download_url` - File locations
- `scan_timestamp`, `extraction_timestamp` - Processing times

## Example Configs

### 1. Simple DFU Sweep (no aggregation)

```json
{
  "name": "dfu_sweep_simple",
  "description": "Plot droplet size vs DFU row, one line per test",
  "axes": {
    "x": "dfu_row",
    "y": "droplet_size_mean",
    "y_error": "droplet_size_std"
  },
  "grouping": {
    "group_by": "device_id"
  },
  "aggregation": {
    "method": "none"
  },
  "style": {
    "plot_type": "line+markers",
    "color_scheme": "vibrant",
    "show_grid": true
  },
  "labels": {
    "title": "Droplet Size Across DFU Rows",
    "x_label": "DFU Row",
    "y_label": "Droplet Size (µm)"
  }
}
```

### 2. Aggregated Pressure Analysis

```json
{
  "name": "pressure_vs_droplet_aggregated",
  "description": "Mean droplet size vs pressure, grouped by device, with error bars",
  "axes": {
    "x": "oil_pressure",
    "y": "droplet_size_mean"
  },
  "grouping": {
    "group_by": "device_id"
  },
  "aggregation": {
    "method": "mean",
    "group_cols": ["device_id", "oil_pressure"],
    "error_method": "sem"
  },
  "style": {
    "plot_type": "line+markers",
    "color_scheme": "vibrant",
    "marker_size": 8,
    "line_width": 2
  },
  "labels": {
    "title": "Droplet Size vs Oil Pressure",
    "x_label": "Oil Pressure (mbar)",
    "y_label": "Mean Droplet Size (µm)"
  },
  "advanced": {
    "sort_x": true,
    "show_counts": true
  }
}
```

## Usage Examples

### Python

```python
from src.plot_from_config import plot_from_config

# Generate plot from config and CSV
plot_from_config(
    csv_path="data/test_plots/w13_5mlhr_data.csv",
    config_path="configs/plots/dfu_sweep_simple.json",
    output_path="outputs/test_plot.png"
)
```

### Command Line

```bash
python src/plot_from_config.py \
  --csv data/test_plots/w13_5mlhr_data.csv \
  --config configs/plots/dfu_sweep_simple.json \
  --output outputs/test_plot.png
```

## Creating New Configs

1. **Identify the question**: What comparison/trend do you want to visualize?
2. **Choose axes**: What should be on X and Y?
3. **Determine grouping**: Should different series be colored by device, fluid, pressure, etc.?
4. **Decide aggregation**: Show raw points or aggregate by mean/median?
5. **Configure style**: Line, scatter, markers, colors, etc.
6. **Test with data**: Generate filtered CSV and test the config
7. **Refine**: Adjust labels, scales, styling until it looks right
8. **Save**: Store in `configs/plots/` with descriptive name

## Best Practices

1. **Name configs descriptively**: `dfu_sweep_by_device.json`, not `plot1.json`
2. **Include good descriptions**: Help future users understand when to use each config
3. **Test with multiple datasets**: Ensure config works with different filters
4. **Document assumptions**: Note in description what columns/values are expected
5. **Keep it simple**: Don't over-specify; use defaults where possible
6. **Version your configs**: Increment version if you make breaking changes

## Validation

The plotting engine will validate:
- Required fields are present
- Column names exist in the CSV
- Aggregation settings are compatible
- Style options are valid

Errors will provide clear messages about what's wrong and how to fix it.
