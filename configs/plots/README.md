# Plot Configuration System

## Overview

This directory contains JSON configuration files that define plot specifications for the microfluidic device analysis system. Each config describes how to generate a specific type of plot from filtered CSV data.

## Philosophy

**Separate data filtering from visualization.** The TUI handles filtering and exporting data, while this plotting system focuses solely on creating beautiful, consistent visualizations. This separation enables:

- **Reusability**: Same config works with any compatible filtered dataset
- **Consistency**: All plots of the same type look identical
- **Efficiency**: Quickly generate plots without redesigning each time
- **Experimentation**: Easy to tweak visual parameters without touching data

## Quick Start

### Command Line Usage

```bash
# Basic usage
python src/plot_from_config.py \
  --csv data/filtered_export.csv \
  --config configs/plots/dfu_sweep.json \
  --output outputs/my_plot.png

# Show interactively (matplotlib window)
python src/plot_from_config.py \
  --csv data/filtered_export.csv \
  --config configs/plots/pressure_vs_droplet.json \
  --show
```

### Python Usage

```python
from src.plot_from_config import plot_from_config

# Generate plot
plot_from_config(
    csv_path="data/test_plots/w13_data.csv",
    config_path="configs/plots/dfu_sweep.json",
    output_path="outputs/analysis_plot.png"
)

# Auto-generate output filename
plot_from_config(
    csv_path="data/test_plots/w13_data.csv",
    config_path="configs/plots/dfu_sweep.json"
)
# Saves to: outputs/plots/dfu_sweep_w13_data.png
```

## Available Presets

| Config File | Purpose | Best For |
|------------|---------|----------|
| `dfu_sweep.json` | Droplet size across DFU rows | Spatial variation within a device |
| `pressure_vs_droplet.json` | Droplet size vs oil pressure | Pressure parameter sweeps |
| `flowrate_vs_droplet.json` | Droplet size vs aqueous flowrate | Flowrate parameter sweeps |
| `frequency_vs_pressure.json` | Frequency vs oil pressure | Droplet generation rate analysis |
| `stability_over_time.json` | Droplet size over testing dates | Device stability and consistency |
| `device_type_comparison.json` | W13 vs W14 performance | Device design comparisons |

### 1. DFU Sweep (`dfu_sweep.json`)

**Purpose**: Visualize droplet size variation across DFU rows (spatial uniformity).

**Expected Data**:
- Multiple DFU rows (typically 1-6)
- Single or multiple devices
- Consistent flowrate and pressure recommended

**Example Filter in TUI**:
- Device: W13
- Flowrate: 5 ml/hr
- Pressure: 300 mbar

**Visual Style**: Line plot with markers, one line per device, vibrant colors.

---

### 2. Pressure vs Droplet (`pressure_vs_droplet.json`)

**Purpose**: Analyze how oil pressure affects droplet size (aggregated with error bars).

**Expected Data**:
- Multiple pressure values
- One or more devices
- Data automatically aggregated by device and pressure

**Example Filter in TUI**:
- Device: W13 (all)
- Flowrate: 5 ml/hr (fixed)
- Pressure: Various

**Visual Style**: Line+markers with SEM error bars, aggregated mean per pressure.

---

### 3. Flowrate vs Droplet (`flowrate_vs_droplet.json`)

**Purpose**: Analyze how aqueous flowrate affects droplet size.

**Expected Data**:
- Multiple flowrate values
- One or more devices
- Data automatically aggregated by device and flowrate

**Example Filter in TUI**:
- Device: W13 (all)
- Flowrate: Various
- Pressure: 300 mbar (fixed)

**Visual Style**: Line+markers with SEM error bars, aggregated mean per flowrate.

---

### 4. Frequency vs Pressure (`frequency_vs_pressure.json`)

**Purpose**: Track droplet generation rate across pressure conditions.

**Expected Data**:
- Frequency measurements (not droplet size)
- Multiple pressure values
- One or more devices

**Example Filter in TUI**:
- Measurement type: Frequency
- Pressure: Various

**Visual Style**: Line+markers with dark color scheme, aggregated.

---

### 5. Stability Over Time (`stability_over_time.json`)

**Purpose**: Track device performance across multiple test dates.

**Expected Data**:
- Multiple testing dates for same device(s)
- Useful for identifying drift or degradation

**Example Filter in TUI**:
- Device: W13_S1_R2 (or multiple)
- All test dates

**Visual Style**: Line+markers with earth tones, shows temporal trends.

---

### 6. Device Type Comparison (`device_type_comparison.json`)

**Purpose**: Compare W13 vs W14 device designs at population level.

**Expected Data**:
- Both W13 and W14 devices
- Multiple measurements per device type
- Aggregated across all devices of each type

**Example Filter in TUI**:
- Device type: Both W13 and W14
- Same flow conditions

**Visual Style**: Bold lines, large markers, emphasizes type-level differences.

---

## Workflow

### Standard Analysis Workflow

1. **Filter in TUI**
   ```
   > filter device_type W13
   > filter flowrate 5
   > filter pressure 300
   ```

2. **Export CSV**
   ```
   > export
   Exported to: outputs/W13_5mlhr_300mbar_export_20251112_143022.csv
   ```

3. **Generate Plot**
   ```bash
   python src/plot_from_config.py \
     --csv outputs/W13_5mlhr_300mbar_export_20251112_143022.csv \
     --config configs/plots/dfu_sweep.json \
     --output outputs/W13_5mlhr_300mbar_dfu_analysis.png
   ```

4. **Review and Refine**
   - Look at plot
   - Adjust filters if needed
   - Try different configs
   - Tweak config JSON if visual style needs changes

### Batch Processing Example

```python
# Generate multiple plot types from same dataset
from src.plot_from_config import plot_from_config

csv_file = "outputs/W13_5mlhr_export.csv"

configs = [
    "configs/plots/dfu_sweep.json",
    "configs/plots/pressure_vs_droplet.json",
    "configs/plots/flowrate_vs_droplet.json"
]

for config in configs:
    plot_from_config(csv_path=csv_file, config_path=config)
    print(f"✓ Generated plot from {config}")
```

## Creating Custom Configs

### Step-by-Step Guide

1. **Identify your question**
   - What relationship do you want to visualize?
   - Example: "How does temperature affect droplet size?"

2. **Determine axes**
   - X-axis: Independent variable (temperature)
   - Y-axis: Dependent variable (droplet_size_mean)

3. **Choose grouping**
   - Should different series be colored by device? fluid? date?
   - Example: `"group_by": "device_id"`

4. **Decide aggregation**
   - Show raw points (`"method": "none"`) or aggregate?
   - If aggregating, what columns to group by?
   - Example: Aggregate by device and temperature

5. **Configure style**
   - Plot type: line, scatter, line+markers, bar, etc.
   - Colors: vibrant, pastel, dark, earth
   - Markers, line width, transparency

6. **Test it**
   ```bash
   python src/plot_from_config.py \
     --csv your_filtered_data.csv \
     --config your_new_config.json \
     --show
   ```

7. **Refine and save**
   - Adjust labels, colors, sizing
   - Save to `configs/plots/` with descriptive name

### Example: Creating a New Config

Let's create a config for "Droplet Size Distribution by Fluid Type":

```json
{
  "name": "fluid_type_comparison",
  "description": "Compare droplet sizes across different fluid combinations",
  "version": "1.0",

  "axes": {
    "x": "aqueous_fluid",
    "y": "droplet_size_mean"
  },

  "grouping": {
    "group_by": "oil_fluid",
    "facet_row": null,
    "facet_col": null
  },

  "aggregation": {
    "method": "mean",
    "group_cols": ["aqueous_fluid", "oil_fluid"],
    "error_method": "sem"
  },

  "style": {
    "plot_type": "bar",
    "color_scheme": "vibrant",
    "marker_size": 8,
    "line_width": 2,
    "alpha": 0.85,
    "show_grid": true,
    "show_legend": true,
    "legend_position": "best"
  },

  "scales": {
    "x_scale": "linear",
    "y_scale": "linear",
    "x_limits": null,
    "y_limits": null
  },

  "labels": {
    "title": "Droplet Size by Fluid Type",
    "x_label": "Aqueous Fluid",
    "y_label": "Mean Droplet Diameter (µm)",
    "legend_title": "Oil Fluid"
  },

  "figure": {
    "width": 12,
    "height": 7,
    "dpi": 300
  },

  "advanced": {
    "sort_x": false,
    "sort_legend": true,
    "show_counts": true,
    "connect_points": false,
    "fill_between": false
  }
}
```

## Config Schema Reference

See `SCHEMA.md` for complete documentation of all available fields and options.

### Quick Field Reference

**Required Fields**:
- `name`: Unique identifier
- `description`: Human-readable purpose
- `axes.x`, `axes.y`: Column names
- `aggregation.method`: "none", "mean", or "median"
- `style.plot_type`: "line", "scatter", "line+markers", "bar", etc.

**Common Optional Fields**:
- `axes.y_error`: Column for error bars (if aggregation is "none")
- `grouping.group_by`: Column to split into series
- `aggregation.group_cols`: Columns to group before aggregating
- `aggregation.error_method`: "std", "sem", "ci95" (if aggregating)
- `style.color_scheme`: "vibrant", "pastel", "dark", "earth"
- `labels.title`, `x_label`, `y_label`: Plot labels

## Testing Your Configs

### Using Test Data

Test datasets are in `data/test_plots/`. These are real database exports with known characteristics:

```bash
# Test with provided data
python src/plot_from_config.py \
  --csv data/test_plots/dfu_sweep_w13_5mlhr_300mbar.csv \
  --config configs/plots/dfu_sweep.json \
  --show
```

### Generating New Test Data

Modify `generate_test_data.py` to create filtered datasets for testing:

```python
# Example: Generate test data for a specific device
test_df = df[
    (df['device_id'] == 'W13_S1_R2') &
    (df['measurement_type'] == 'dfu_measure')
]
test_df.to_csv('data/test_plots/my_test_data.csv', index=False)
```

## Troubleshooting

### "Missing columns in CSV"

**Problem**: Config references columns that don't exist in your CSV.

**Solution**: Check your CSV columns. Either:
1. Export data with the required columns, or
2. Modify config to use available columns

```bash
# Check columns in your CSV
python -c "import pandas as pd; print(pd.read_csv('your_file.csv').columns.tolist())"
```

### "Empty plot" or "No data shown"

**Problem**: Filters or grouping resulted in empty groups.

**Solution**: Check that:
1. Your CSV has data
2. Grouping column has valid values
3. X and Y columns have non-null data

### "Aggregation failed"

**Problem**: `group_cols` don't match your data structure.

**Solution**: Ensure `group_cols` lists all columns you want to group by before aggregating. Must include both X column and any grouping column.

## Tips for Great Plots

1. **Keep data filtering separate**: Filter in TUI, visualize here
2. **Use descriptive config names**: `dfu_sweep.json`, not `plot1.json`
3. **Test with real data**: Don't design in a vacuum
4. **Iterate**: Generate, review, tweak, repeat
5. **Document assumptions**: Note in description what data the config expects
6. **Version your configs**: Increment version on breaking changes
7. **Share successful configs**: Build a library over time

## Advanced Features

### Faceting (Coming Soon)

```json
"grouping": {
  "group_by": "device_id",
  "facet_row": "fluid_type",
  "facet_col": "pressure"
}
```

Creates a grid of subplots with different combinations.

### Multiple Y-Axes (Coming Soon)

```json
"axes": {
  "x": "pressure",
  "y": ["droplet_size_mean", "frequency_mean"]
}
```

Plots multiple Y variables on same or separate axes.

### Custom Color Palettes

```json
"style": {
  "color_scheme": "custom",
  "custom_colors": ["#FF5733", "#33FF57", "#3357FF"]
}
```

## Integration with TUI (Future)

Planned integration:
- `plotws <config_name>` - Generate plot from current filters using named config
- `plotws list` - Show available configs
- `plotws edit <config_name>` - Open config in editor
- `plotws create` - Interactive config creation wizard

For now, use the command-line or Python interface.

## Questions?

See `SCHEMA.md` for detailed schema documentation.

Check `../test_plots/` for example filtered datasets.

Review existing configs in this directory for patterns and examples.
