# Live Plot Editing - Quick Start Guide

## What is it?
Interactive plot editing through terminal commands. Create plots in a separate window, edit them live, and save only when you're happy with the result.

## Quick Start

### Step 1: Create a Plot
```
>>> show droplet size across all measured DFUs for w13 devices at 5mlhr
```

A matplotlib window opens showing your plot.
Terminal enters "plot editing mode" with `plot>` prompt.

### Step 2: Edit the Plot
```
plot> help                    # See all commands
plot> change colors           # Cycle color schemes
plot> add test date          # Add testing dates to legend
plot> change title My Title  # Custom title
```

Every command updates the plot window in real-time!

### Step 3: Save When Ready
```
plot> save                    # Save and exit
```

Or discard without saving:
```
plot> discard                 # Close without saving
```

## Essential Commands

| Command | What it does |
|---------|-------------|
| `help` | Show all commands |
| `change colors` | Try different color schemes |
| `add test date` | Add test dates to legend |
| `add bond date` | Add bond dates to legend |
| `change title [text]` | Custom plot title |
| `remove legend` | Hide legend |
| `show legend` | Show legend |
| `remove grid` | Hide grid |
| `add grid` | Show grid |
| `change theme dark` | Dark theme |
| `change theme light` | Light theme |
| `resize large` | Make bigger |
| `save` | Save and exit |
| `discard` | Close without saving |

## Common Workflows

### Quick Color Change
```
plot> change colors
plot> change colors
plot> change colors
plot> save
```
Cycles through 5 color schemes: default → vibrant → pastel → dark → earth

### Add Full Context
```
plot> add test date
plot> add bond date
plot> change title W13 Droplet Analysis - Complete Dataset
plot> save
```

### Dark Mode Scientific Plot
```
plot> change theme dark
plot> remove legend
plot> change title Professional Publication Figure
plot> resize large
plot> save
```

### Clean Minimal Look
```
plot> remove grid
plot> remove legend
plot> change colors
plot> save
```

## Example Session

```
>>> show droplet size across all measured DFUs for w13 devices at 5mlhr

[Success]
DFU analysis complete!
Metric: droplet_size_mean
Found 2 device(s): W13_S1_R1, W13_S1_R2

======================================================================
PLOT EDITING MODE ACTIVE
======================================================================
Plot window opened. Type 'help' for editing options.

plot> change colors
[OK] Color scheme changed to: vibrant

plot> add test date
[OK] Testing date information added to legend

plot> change title W13 Devices - 5ml/hr Performance
[OK] Title changed to: w13 devices - 5ml/hr performance

plot> save
[OK] Plot saved to: outputs/analyst/plots/edited_plot_20251030_143022.png

Plot editing completed.

>>>
```

## Tips

1. **Always type `help` first** to see what's available
2. **Try different color schemes** - just keep typing `change colors`
3. **Preview before saving** - that's the whole point!
4. **Use descriptive titles** - future you will thank present you
5. **Don't forget to `save`** - or all changes are lost!

## What's in the Separate Window?

The matplotlib window shows your plot and updates live as you type commands. You can:
- ✅ See changes instantly
- ✅ Zoom with mouse
- ✅ Pan around
- ✅ Use matplotlib toolbar
- ❌ Don't close it manually (use `save` or `discard` commands instead)

## Color Schemes

Type `change colors` to cycle through:
1. **default** - Standard matplotlib colors
2. **vibrant** - Bold, high-contrast colors
3. **pastel** - Soft, gentle colors
4. **dark** - Muted, professional colors
5. **earth** - Brown and green earth tones

## When to Use Live Editing

**Perfect for:**
- Creating publication figures
- Exploring different visualizations
- Presentations and reports
- When you need precise control

**Maybe skip for:**
- Quick data checks
- Automated batch processing
- When you trust default settings

## Exit Plot Editing Mode

Three ways:
1. `plot> save` - Save plot and exit
2. `plot> discard` - Exit without saving
3. Close plot window manually (not recommended)

After exiting, you return to normal `>>>` prompt.

## Testing Your Setup

Run the test script:
```bash
.venv/Scripts/python.exe test_live_plot_editing.py
```

Choose option 1 for automated test or option 2 for manual testing.

## Getting Help

In plot editing mode:
```
plot> help
```

Shows complete command list with descriptions.

In normal mode:
```
>>> help
```

Shows query examples including DFU plotting.

## That's It!

You now know enough to create beautiful, customized plots interactively. Start with simple commands like `change colors` and `add test date`, then explore more advanced features.

**Remember:** Every command updates the plot window in real-time. Experiment freely - you can always `discard` if you don't like the result!
