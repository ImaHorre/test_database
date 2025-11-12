# Live Plot Preview and Editing System

## Overview

The live plot preview and editing system provides a sophisticated, interactive workflow for creating and modifying plots through terminal commands. Instead of generating static plots, users can now:

1. Open plots in a **separate matplotlib window** (not embedded in terminal)
2. Use **terminal commands** to interactively modify the plot
3. See changes **reflected in real-time** in the plot window
4. **Save only when ready** with the `save` command

## Key Features

- **Separate Plot Window**: Plots open in their own matplotlib window while terminal remains interactive
- **Terminal Control**: Full plot control via natural language commands
- **Real-time Updates**: All modifications appear immediately in the plot window
- **State Management**: Tracks all plot state and modifications
- **Comprehensive Editing**: Change colors, themes, legends, grids, titles, and more
- **Metadata Integration**: Add test dates, bond dates, and other metadata to plots
- **Help System**: Built-in help shows all available commands

## User Experience Flow

```
>>> show droplet size across all measured DFUs for w13 devices at 5mlhr

[Success]
DFU analysis complete!

Metric: droplet_size_mean
Found 2 device(s):
  - W13_S1_R1
  - W13_S1_R2

DFU rows measured: 1, 2, 3, 4, 5, 6
Total measurements: 12

Varying parameters detected: oil_pressure
(Legend includes context for differentiating devices)

======================================================================
PLOT EDITING MODE ACTIVE
======================================================================

Plot window opened. Type 'help' for editing options.
Commands: help, save, discard, change colors, add test date, etc.

----------------------------------------------------------------------

plot> help

========================================
PLOT EDITING COMMANDS
========================================

LEGEND & DISPLAY:
  show legend       - Display plot legend
  remove legend     - Hide plot legend
  add grid          - Show grid lines
  remove grid       - Hide grid lines

VISUAL STYLING:
  change colors     - Cycle through color schemes
  change theme [light/dark] - Change plot theme
  resize [small/medium/large] - Change figure size

DATA DISPLAY:
  add error bars    - Show error bars on data points
  remove error bars - Hide error bars
  add test date     - Add testing date info to legend
  add bond date     - Add bonding date info to legend

CUSTOMIZATION:
  change title [new title] - Set custom plot title

ACTIONS:
  save             - Save plot to file and exit
  discard          - Close plot without saving
  help             - Show this help message

========================================

plot> change colors
[OK] Color scheme changed to: vibrant
Plot updated. Continue editing or type 'save' to finish.

plot> add test date
[OK] Testing date information added to legend
Plot updated. Continue editing or type 'save' to finish.

plot> change title W13 Droplet Size Analysis - 5ml/hr
[OK] Title changed to: w13 droplet size analysis - 5ml/hr
Plot updated. Continue editing or type 'save' to finish.

plot> save
[OK] Plot saved to: outputs/analyst/plots/edited_plot_20251030_105132.png

Plot saved to: outputs\analyst\plots\edited_plot_20251030_105132.png

Plot editing completed.

----------------------------------------------------------------------

>>>
```

## Architecture

### Component Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     User Query                               │
│  "show droplet size across all measured DFUs for w13 at 5mlhr" │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  v
┌─────────────────────────────────────────────────────────────┐
│               QueryProcessor                                 │
│  - Parses natural language                                  │
│  - Detects 'plot_dfu' intent                                │
│  - Extracts parameters                                       │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  v
┌─────────────────────────────────────────────────────────────┐
│               DataAnalyst                                    │
│  - _handle_plot_dfu_query(intent, live_preview=True)       │
│  - Calls plot_metric_vs_dfu() with live_preview=True       │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  v
┌─────────────────────────────────────────────────────────────┐
│          plot_metric_vs_dfu()                                │
│  - Filters data based on criteria                           │
│  - Creates matplotlib figure and axes                       │
│  - Plots data with context-aware labeling                   │
│  - If live_preview=True:                                    │
│    * plt.ion() - Enable interactive mode                    │
│    * plt.show(block=False) - Show plot window              │
│    * Create PlotEditor instance                             │
│    * Return editor in result dict                           │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  v
┌─────────────────────────────────────────────────────────────┐
│               PlotEditor                                     │
│  - Stores fig, ax, plot_data, metadata                      │
│  - Tracks modifications state                               │
│  - process_command(cmd) -> result dict                      │
│  - _refresh_plot() - Updates display                        │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  v
┌─────────────────────────────────────────────────────────────┐
│            SimpleDashboard                                   │
│  - Detects live_preview=True in result                      │
│  - enter_plot_editing_mode(result)                          │
│  - Changes prompt to "plot>"                                │
│  - Routes commands to PlotEditor                            │
│  - Exits mode on save/discard                               │
└─────────────────────────────────────────────────────────────┘
```

### Key Files

#### 1. `src/plot_editor.py` (NEW)
**PlotEditor Class**
- Manages live plot state and modifications
- Processes editing commands
- Handles real-time plot updates
- Saves/discards plots

**Key Methods:**
- `__init__(fig, ax, plot_data, metadata)` - Initialize with plot objects
- `process_command(command)` - Parse and execute commands
- `_toggle_legend(show)` - Show/hide legend
- `_toggle_grid(show)` - Show/hide grid
- `_cycle_color_scheme()` - Change color palette
- `_change_theme(theme)` - Switch light/dark mode
- `_add_test_date_info()` - Add test dates to legend
- `_add_bond_date_info()` - Add bond dates to legend
- `_change_title(title)` - Update plot title
- `_save_plot()` - Save to file
- `_discard_plot()` - Close without saving
- `_refresh_plot()` - Update display

#### 2. `src/analyst.py` (MODIFIED)
**plot_metric_vs_dfu() Updates**
- Added `live_preview: bool = False` parameter
- When `live_preview=True`:
  - Enables `plt.ion()` for interactive mode
  - Shows plot with `plt.show(block=False)`
  - Collects device metadata (dates)
  - Creates PlotEditor instance
  - Returns editor in result dict
- When `live_preview=False`:
  - Saves immediately and closes
  - Returns plot path

**_handle_plot_dfu_query() Updates**
- Added `live_preview: bool = True` parameter
- Passes live_preview to plot_metric_vs_dfu()
- Live preview enabled by default for DFU plots

#### 3. `dashboard_v2.py` (MODIFIED)
**SimpleDashboard Updates**

**New State Variables:**
```python
self.plot_editor = None
self.in_plot_editing_mode = False
```

**New Methods:**
- `enter_plot_editing_mode(plot_result)` - Enter editing mode
- `exit_plot_editing_mode()` - Exit editing mode
- `handle_plot_editing_command(command)` - Route commands to editor

**Modified Methods:**
- `execute_natural_language()` - Detects live preview and enters editing mode
- `run()` - Checks editing mode, uses "plot>" prompt, routes commands

#### 4. `test_live_plot_editing.py` (NEW)
**Test Suite**
- **Automated Test Mode**: Tests all commands automatically
- **Manual Test Mode**: Interactive testing with user control
- Tests plot creation, command processing, modifications, and saving
- Validates file outputs

## Command Reference

### Legend & Display Commands

| Command | Description | Example |
|---------|-------------|---------|
| `show legend` | Display plot legend | `plot> show legend` |
| `remove legend` | Hide plot legend | `plot> remove legend` |
| `add grid` | Show grid lines | `plot> add grid` |
| `remove grid` | Hide grid lines | `plot> remove grid` |

### Visual Styling Commands

| Command | Description | Example |
|---------|-------------|---------|
| `change colors` | Cycle through color schemes (default, vibrant, pastel, dark, earth) | `plot> change colors` |
| `change theme [mode]` | Change theme (light/dark) | `plot> change theme dark` |
| `resize [size]` | Change figure size (small/medium/large) | `plot> resize large` |

### Data Display Commands

| Command | Description | Example |
|---------|-------------|---------|
| `add error bars` | Show error bars on data points | `plot> add error bars` |
| `remove error bars` | Hide error bars | `plot> remove error bars` |
| `add test date` | Add testing date info to legend | `plot> add test date` |
| `add bond date` | Add bonding date info to legend | `plot> add bond date` |

### Customization Commands

| Command | Description | Example |
|---------|-------------|---------|
| `change title [text]` | Set custom plot title | `plot> change title My Custom Title` |

### Action Commands

| Command | Description | Example |
|---------|-------------|---------|
| `save` | Save plot to file and exit editing mode | `plot> save` |
| `discard` | Close plot without saving | `plot> discard` |
| `help` | Show all available commands | `plot> help` |

## Color Schemes

The system includes 5 color schemes that you can cycle through:

1. **default** - Matplotlib default colors
2. **vibrant** - High contrast, vibrant colors
3. **pastel** - Soft, pastel colors
4. **dark** - Dark, muted colors
5. **earth** - Earth tone colors

Each time you type `change colors`, it cycles to the next scheme.

## Technical Implementation Details

### Interactive Mode Setup

```python
if live_preview:
    # Enable interactive mode
    plt.ion()
    plt.show(block=False)

    # Create plot editor
    from .plot_editor import create_live_plot_editor

    editor = create_live_plot_editor(fig, ax, plot_data, metadata)

    # Return with editor
    return {
        'live_preview': True,
        'editor': editor,
        'fig': fig,
        'ax': ax,
        ...
    }
```

### Dashboard Mode Detection

```python
def execute_natural_language(self, query: str):
    result = self.analyst.process_natural_language_query(query)

    # Check if live preview mode was activated
    if isinstance(result.get('result'), dict) and result['result'].get('live_preview'):
        self.enter_plot_editing_mode(result['result'])
        return
```

### Plot Editing Loop

```python
while True:
    if self.in_plot_editing_mode:
        user_input = input("plot> ").strip()

        should_exit = self.handle_plot_editing_command(user_input)
        if should_exit:
            self.exit_plot_editing_mode()
        continue
```

### Real-time Updates

```python
def _refresh_plot(self):
    """Refresh the plot display."""
    try:
        self.fig.canvas.draw()
        self.fig.canvas.flush_events()
    except Exception as e:
        logger.warning(f"Could not refresh plot: {e}")
```

## Testing

### Running Tests

**Automated Test (All Commands):**
```bash
cd test_database
.venv/Scripts/python.exe test_live_plot_editing.py
# Choose option 1
```

**Manual Test (Interactive):**
```bash
cd test_database
.venv/Scripts/python.exe test_live_plot_editing.py
# Choose option 2
```

### Test Coverage

The test suite verifies:
- ✓ Live plot preview creation
- ✓ Plot window opening in separate window
- ✓ Help command display
- ✓ Color scheme cycling
- ✓ Grid toggle (on/off)
- ✓ Title customization
- ✓ Test date addition (when available)
- ✓ Plot saving
- ✓ File existence validation

**Test Output:**
```
======================================================================
TEST COMPLETED SUCCESSFULLY
======================================================================

Summary:
- Live plot preview: WORKING
- Command processing: WORKING
- Plot modifications: WORKING
- Plot saving: WORKING
```

## Usage Examples

### Example 1: Basic DFU Plot with Editing

```python
>>> show droplet size across all measured DFUs for w13 devices at 5mlhr

[Plot opens in separate window]

plot> help
[Shows all commands]

plot> change colors
[OK] Color scheme changed to: vibrant

plot> change title W13 Performance at 5ml/hr
[OK] Title changed

plot> save
[OK] Plot saved to: outputs/analyst/plots/edited_plot_20251030_143022.png
```

### Example 2: Theme Switching

```python
plot> change theme dark
[OK] Theme changed to: dark

plot> remove grid
[OK] Grid hidden

plot> save
```

### Example 3: Adding Metadata

```python
plot> add test date
[OK] Testing date information added to legend

plot> add bond date
[OK] Bonding date information added to legend

plot> resize large
[OK] Figure resized to: large

plot> save
```

## Advantages Over Static Plots

### Before (Static Plots)
- ❌ Plot saved immediately, no preview
- ❌ Can't modify after creation
- ❌ Must regenerate entire plot for small changes
- ❌ No interactive refinement

### Now (Live Plot Editing)
- ✅ Preview plot before saving
- ✅ Interactively refine appearance
- ✅ Try different color schemes instantly
- ✅ Add metadata on demand
- ✅ Customize title and layout
- ✅ Only save when satisfied
- ✅ Natural language commands

## Best Practices

1. **Preview First**: Always review the plot before adding customizations
2. **Use Help**: Type `help` to see all available commands
3. **Experiment with Colors**: Try different color schemes to find the best visual
4. **Add Context**: Use `add test date` and `add bond date` for documentation
5. **Custom Titles**: Use descriptive titles that explain the plot
6. **Save When Done**: Don't forget to type `save` when finished

## Troubleshooting

### Plot Window Doesn't Open
- **Cause**: Matplotlib backend issue
- **Solution**: Ensure you're using a GUI backend (TkAgg, Qt5Agg)
- **Check**: `import matplotlib; print(matplotlib.get_backend())`

### Commands Not Working
- **Cause**: Not in plot editing mode
- **Solution**: Create a plot with live preview first
- **Check**: Look for "plot>" prompt

### Plot Window Closes Unexpectedly
- **Cause**: Window manually closed
- **Solution**: Type `discard` to exit cleanly

### Changes Not Visible
- **Cause**: Plot refresh failed
- **Solution**: Try another command to trigger refresh
- **Note**: Some backends may not support all updates

## Future Enhancements

Potential future additions:
- ✨ Undo/redo functionality
- ✨ Custom annotation tools
- ✨ Export to multiple formats (PDF, SVG)
- ✨ Batch editing for multiple plots
- ✨ Plot templates/presets
- ✨ Keyboard shortcuts
- ✨ Mouse interaction support

## Integration with Existing Workflows

The live plot editing system is **fully backward compatible**:
- Setting `live_preview=False` (or omitting parameter) produces immediate static plots
- All existing code continues to work without modification
- Dashboard can use both modes simultaneously

## Conclusion

The live plot preview and editing system transforms plot creation from a static, one-shot process into an interactive, iterative refinement workflow. Users can now create professional-quality plots with precisely the appearance they want, all through natural terminal commands.

**Key Benefits:**
- 🎨 Interactive visual refinement
- 🖥️ Separate plot window + terminal control
- ⚡ Real-time updates
- 📊 Comprehensive customization
- 💾 Save only when ready
- 📝 Natural language commands

This system significantly enhances the data analysis workflow by putting full plot control at the user's fingertips.
