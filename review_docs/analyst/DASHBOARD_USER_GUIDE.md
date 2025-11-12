# Interactive CLI Dashboard - User Guide

## Overview

The Microfluidic Device Analysis Dashboard is a beautiful terminal interface for analyzing your microfluidic device data. Built with Textual, it provides an intuitive way to run all Phase 1 analysis methods with real-time feedback.

![Dashboard Status: READY](outputs/dashboard_ready.txt)

---

## Getting Started

### Launch the Dashboard

```bash
python dashboard.py
```

Or with the virtual environment:

```bash
.venv/Scripts/python.exe dashboard.py
```

---

## Dashboard Layout

```
┌──────────────────────────────────────────────────────────────┐
│  HEADER: Microfluidic Device Analysis Dashboard      [Clock] │
├─────────────────────┬────────────────────────────────────────┤
│                     │                                        │
│  DATABASE STATUS    │                                        │
│  ━━━━━━━━━━━━━━━   │                                        │
│  Total Records: 612 │          RESULT DISPLAY                │
│  Devices: 5         │                                        │
│  W13: 396          │  (Results appear here after running    │
│  W14: 216          │   a command)                           │
│                     │                                        │
│  QUICK COMMANDS     │                                        │
│  ━━━━━━━━━━━━━━━   │                                        │
│  [1] Compare        │                                        │
│      Devices        │                                        │
│  [2] Parameter      │                                        │
│      Effects        │                                        │
│  [3] Track Device   │                                        │
│  [4] DFU Comparison │                                        │
│  [5] Fluid Compare  │                                        │
│  [6] List Devices   │                                        │
│                     │                                        │
│  [Q] Ask Question   │                                        │
│  [R] Refresh        │                                        │
│  [X] Exit           │                                        │
│                     │                                        │
└─────────────────────┴────────────────────────────────────────┘
│  FOOTER: Keyboard shortcuts                                  │
└──────────────────────────────────────────────────────────────┘
```

---

## Commands

### [1] Compare Devices at Same Parameters

**Purpose:** Compare all devices tested under identical flow conditions

**Workflow:**
1. Click button or press `1`
2. Input dialog appears asking for:
   - Device Type (e.g., W13, W14, or leave empty for all)
   - Aqueous Flowrate (ml/hr, or leave empty)
   - Oil Pressure (mbar, or leave empty)
3. Click "Run Analysis"
4. Results appear in right panel
5. Plot automatically saved to `outputs/`

**Example Use Cases:**
- "Compare all W13 devices tested at 30ml/hr"
- "Show me all devices at 5ml/hr and 200mbar"
- "Compare all W13 and W14 at any 100mbar pressure"

**Output:**
- Statistics table (mean, std, count per device)
- Box plots for droplet size and frequency
- Plot path shown in results

---

### [2] Analyze Flow Parameter Effects

**Purpose:** Understand how flow parameters affect measurements

**Workflow:**
1. Click button or press `2`
2. Input dialog asks for:
   - Device Type (required, e.g., W13)
   - Parameter (`aqueous_flowrate` or `oil_pressure`)
   - Metric (`droplet_size_mean` or `frequency_mean`)
3. Click "Run Analysis"
4. Results show correlation and statistics
5. Two-panel plot saved automatically

**Example Use Cases:**
- "How does flowrate affect droplet size in W13?"
- "What's the relationship between pressure and frequency?"
- "Is there correlation between flowrate and droplet variation?"

**Output:**
- Correlation coefficient
- Scatter plot with trend line
- Box plots by parameter value
- Grouped statistics table

---

### [3] Track Device Over Time

**Purpose:** Monitor individual device performance across test dates

**Workflow:**
1. Click button or press `3`
2. Input dialog asks for:
   - Device ID (e.g., W13_S1_R1)
3. Click "Run Analysis"
4. Comprehensive 4-panel plot generated

**Example Use Cases:**
- "How did W13_S1_R1 perform over time?"
- "Did device quality improve or degrade?"
- "What flow parameters were tested on W13_S2_R2?"

**Output:**
- Droplet size temporal plot
- Frequency temporal plot
- Flow parameters tested (bar chart)
- Summary statistics panel
- Date range and test count

---

### [4] Compare DFU Row Performance

**Purpose:** Identify which DFU rows perform best or show variation

**Workflow:**
1. Click button or press `4`
2. Input dialog asks for:
   - Device Type (optional, leave empty for all)
   - Metric (`droplet_size_mean` or `frequency_mean`)
3. Click "Run Analysis"
4. Box plots and bar charts generated

**Example Use Cases:**
- "Which DFU rows are most consistent?"
- "Do certain rows underperform for W13?"
- "Is there variation across DFU rows?"

**Output:**
- Statistics by DFU row (mean, std, min, max)
- Box plot distribution
- Bar chart with error bars

---

### [5] Compare Fluid Types

**Purpose:** Determine which fluid combinations perform better

**Workflow:**
1. Click button or press `5`
2. Input dialog asks for:
   - Device Type (optional)
3. Click "Run Analysis"
4. Side-by-side comparison plots

**Example Use Cases:**
- "Does SDS or NaCas perform better?"
- "How do fluids affect droplet formation?"
- "Which fluid gives most consistent results?"

**Output:**
- Fluid combination statistics
- Droplet size comparison
- Frequency comparison
- Test counts per fluid type

---

### [6] View All Available Devices

**Purpose:** Quick reference of all devices in database

**Workflow:**
1. Click button or press `6`
2. Device list appears immediately (no inputs needed)

**Output:**
- Device ID and type
- Number of tests
- Date range for each device

**Example:**
```
W13_S1_R1 (W13)
  Tests: 216
  Date range: 2025-08-23 to 2025-09-03

W13_S1_R2 (W13)
  Tests: 72
  Date range: 2025-10-01 to 2025-10-01
...
```

---

### [Q] Ask a Question (Coming Soon)

**Future Feature:** Natural language query interface powered by Claude API

This will allow you to type questions like:
- "Compare all W13 devices"
- "Show me the best performing DFU row"
- "Plot droplet size over time for W13_S1_R1"

**Status:** Phase 3 (not yet implemented)

---

### [R] Refresh Database

**Purpose:** Reload data from CSV database

**Use When:**
- You've updated the database externally
- You've run a scan and want to see new data
- Status display seems stale

**Workflow:**
1. Click button or press `R`
2. Database reloads automatically
3. Status panel updates
4. Confirmation message appears

---

### [X] Exit

**Purpose:** Close the dashboard

**Shortcuts:**
- Click button
- Press `Q` (keyboard shortcut)
- Press `Ctrl+C`

---

## Keyboard Shortcuts

The dashboard supports keyboard navigation:

| Key | Action |
|-----|--------|
| `1` | Compare Devices at Same Parameters |
| `2` | Analyze Flow Parameter Effects |
| `3` | Track Device Over Time |
| `4` | Compare DFU Row Performance |
| `5` | Compare Fluid Types |
| `6` | List All Devices |
| `R` | Refresh Database |
| `Q` | Quit/Exit |
| `Tab` | Navigate between elements |
| `Enter` | Click focused button |
| `Esc` | Cancel input dialog |

---

## Tips & Best Practices

### 1. Leaving Inputs Empty
- Empty inputs = "any value"
- Example: Device Type empty → includes W13 AND W14
- Useful for broad comparisons

### 2. Plot Management
- All plots saved with timestamps: `dashboard_*.png`
- Format: `dashboard_[analysis]_YYYYMMDD_HHMMSS.png`
- Check `outputs/` directory for saved plots
- Open plots in external viewer (not shown in terminal)

### 3. Error Handling
- Invalid inputs show error messages in result panel
- Error messages explain what went wrong
- Cancel dialog and try again with corrected inputs

### 4. Performance
- Commands execute instantly for small datasets
- Larger analyses may take a few seconds
- Progress shown in result panel
- Dashboard remains responsive during execution

### 5. Data Freshness
- Dashboard loads database once at startup
- Use `[R] Refresh` if data changes externally
- Running `python main.py scan` updates the database
- Then use `[R] Refresh` to reload in dashboard

---

## Output Files

All analysis results are saved automatically:

```
outputs/
├── dashboard_device_comparison_20251029_140530.png
├── dashboard_param_effects_20251029_140615.png
├── dashboard_tracking_20251029_140702.png
├── dashboard_dfu_20251029_140745.png
└── dashboard_fluids_20251029_140820.png
```

**Naming Convention:**
- `dashboard_` prefix
- Analysis type
- Timestamp (YYYYMMDD_HHMMSS)
- `.png` extension

---

## Troubleshooting

### Dashboard Won't Launch
**Problem:** Terminal shows error immediately

**Solutions:**
1. Check virtual environment is activated
2. Verify textual is installed: `pip list | grep textual`
3. Check database exists: `data/database.csv`
4. Run: `.venv/Scripts/python.exe dashboard.py`

### "No data found" Errors
**Problem:** Analysis returns no results

**Solutions:**
1. Check input parameters (typos?)
2. Try broader search (leave some fields empty)
3. Use `[6]` to see available devices
4. Verify database has data: `[R] Refresh`

### Plot Files Not Found
**Problem:** Result says plot saved but file missing

**Solutions:**
1. Check `outputs/` directory exists
2. Look for recent files: `dir outputs | sort`
3. Check file permissions on `outputs/` folder

### Display Issues
**Problem:** Dashboard looks garbled or misaligned

**Solutions:**
1. Maximize terminal window
2. Use modern terminal (Windows Terminal, not cmd.exe)
3. Check terminal supports Unicode
4. Resize window and refresh: `[R]`

### Database Out of Sync
**Problem:** Expecting different data than shown

**Solutions:**
1. Run scan: `python main.py scan --path fake_onedrive_database`
2. Refresh dashboard: `[R]`
3. Restart dashboard completely

---

## Example Workflow

### Scenario: Compare W13 Device Performance

1. **Launch Dashboard**
   ```bash
   python dashboard.py
   ```

2. **Check Available Devices**
   - Press `6` to view all devices
   - Note: W13_S1_R1 and W13_S1_R2 available

3. **Compare at Specific Flowrate**
   - Press `1` (Compare Devices)
   - Enter: Device Type = "W13"
   - Enter: Flowrate = "30"
   - Leave pressure empty
   - Click "Run Analysis"
   - View results and plot path

4. **Track Individual Device**
   - Press `3` (Track Device)
   - Enter: Device ID = "W13_S1_R1"
   - Click "Run Analysis"
   - Review temporal performance

5. **Check Parameter Effects**
   - Press `2` (Parameter Effects)
   - Enter: Device Type = "W13"
   - Enter: Parameter = "aqueous_flowrate"
   - Enter: Metric = "droplet_size_mean"
   - Click "Run Analysis"
   - Check correlation value

6. **View All Plots**
   - Exit dashboard (`Q`)
   - Open `outputs/` folder
   - Review generated plots

---

## What's Next?

### Phase 3: Natural Language with Claude API

Soon you'll be able to:

```
> "Compare all W13 devices at 5ml/hr"
┌─────────────────────────────────────────┐
│ Claude AI is analyzing your request...  │
│ • Identified: Device comparison         │
│ • Filters: device_type=W13, flow=5      │
│ • Executing analysis...                 │
│ ✓ Complete!                             │
└─────────────────────────────────────────┘
```

The AI will:
- Understand natural language queries
- Route to appropriate analysis methods
- Ask clarifying questions when needed
- Generate custom analyses on-the-fly
- Save successful patterns for reuse

---

## Support

**Issues?**
- Check troubleshooting section above
- Review error messages carefully
- Try simpler queries first
- Test with known-good inputs

**Feature Requests?**
- Natural language queries (Phase 3)
- Custom plot styles
- Export reports to PDF/HTML
- Batch analysis mode
- Comparison across multiple conditions

---

**Dashboard Version:** 2.0 (Phase 2 Complete)
**Last Updated:** 2025-10-29
**Status:** Production Ready ✓
