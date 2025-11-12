# Interactive Plotting System - Feature Plan

## Executive Summary

**Goal**: Build a live, interactive plotting interface that allows users to dynamically adjust plot parameters, apply filters, detect outliers, and modify series grouping before exporting publication-ready figures.

**Problem Statement**:
- Current JSON config system requires pre-defined configurations
- When same device tested multiple times, plots become confusing (overlapping points)
- No way to explore data visually before committing to a plot
- Users need to iterate: plot → adjust → re-plot → adjust...

**Solution**:
Interactive web-based plotting dashboard with live preview, dynamic controls, and intelligent defaults.

---

## Technology Stack Recommendation

### Primary Choice: **Plotly Dash**

**Why Plotly Dash?**
- ✅ Python-based (integrates with existing codebase)
- ✅ Publication-quality interactive plots (Plotly.js)
- ✅ Rich component library (dropdowns, sliders, checkboxes)
- ✅ Live callbacks for instant updates
- ✅ Can run locally or deploy to web
- ✅ Built-in zoom, pan, hover, export
- ✅ Professional appearance out-of-the-box

**Alternative: Streamlit** (simpler but less flexible)
- Easier to learn, faster to prototype
- Good for MVP, harder to scale for complex interactions

**Why NOT Matplotlib widgets?**
- Desktop-only, no web deployment
- Limited interactivity
- Harder to make professional-looking

---

## Core Features

### Phase 1: MVP - Basic Interactive Plotting (Week 1-2)

#### 1.1 Data Loading & Preview
- Load exported CSV from TUI (or browse for file)
- Display data table with sortable columns
- Show data summary: row count, unique devices, parameter ranges
- Quick data validation (missing values, outliers preview)

#### 1.2 Plot Configuration Panel
**Left Sidebar Controls:**

```
┌─────────────────────────┐
│ PLOT CONFIGURATION      │
├─────────────────────────┤
│ Plot Type:              │
│ [Dropdown: DFU Sweep ▼] │
│                         │
│ X-Axis:                 │
│ [Dropdown: dfu_row   ▼] │
│                         │
│ Y-Axis:                 │
│ [Dropdown: droplet_size▼]│
│                         │
│ Group By:               │
│ [Dropdown: device_id ▼] │
│ ☑ Show error bars       │
│                         │
│ [Apply] [Reset]         │
└─────────────────────────┘
```

#### 1.3 Live Plot Preview
**Main Canvas:**
- Plotly interactive plot (zoom, pan, hover)
- Real-time update on any control change
- Export buttons: PNG, SVG, PDF

#### 1.4 Series Management
**Bottom Panel:**

```
┌──────────────────────────────────────────┐
│ SERIES LEGEND                             │
├──────────────────────────────────────────┤
│ ☑ W13_S1_R2  (10ml/hr, 200mbar) [Edit]  │
│ ☑ W13_S2_R6  (5ml/hr, 200mbar)  [Edit]  │
│ ☐ W13_S2_R6  (10ml/hr, 200mbar) [Edit]  │
│ ☑ W13_S4_R12 (5ml/hr, 300mbar)  [Edit]  │
│                                          │
│ [Show All] [Hide All] [Smart Group]      │
└──────────────────────────────────────────┘
```

**Features:**
- Check/uncheck to show/hide series
- Click [Edit] to change color, marker, label
- [Smart Group] button: auto-detect repeated devices and suggest grouping by flowrate/pressure/date

---

### Phase 2: Advanced Filtering & Outlier Detection (Week 3-4)

#### 2.1 Dynamic Filters
**Filter Panel (collapsible):**

```
┌─────────────────────────┐
│ FILTERS                 │
├─────────────────────────┤
│ Device Type:            │
│ ☑ W13  ☑ W14           │
│                         │
│ Flowrate (ml/hr):       │
│ [====|======] 1-40      │
│                         │
│ Pressure (mbar):        │
│ [=====|=====] 50-800    │
│                         │
│ Testing Date:           │
│ [2025-10-07] to         │
│ [2025-11-03]            │
│                         │
│ ☐ Exclude DFU 4 defects│
│                         │
│ [Apply] [Clear All]     │
└─────────────────────────┘
```

**Features:**
- Sliders for numeric ranges
- Multi-select checkboxes for categories
- Date range pickers
- Preview affected row count before applying

#### 2.2 Outlier Detection & Removal
**Outlier Panel:**

```
┌─────────────────────────────────┐
│ OUTLIER DETECTION               │
├─────────────────────────────────┤
│ Method:                         │
│ [Dropdown: Modified Z-Score ▼] │
│                                 │
│ Threshold: [3.5]  [Detect]      │
│                                 │
│ Detected Outliers: 3            │
│ ─────────────────────────────  │
│ • W13_S2_R6, DFU 1: 45.2 µm    │
│   [✓ Remove] [Keep]             │
│ • W13_S4_R12, DFU 5: 15.1 µm   │
│   [✓ Remove] [Keep]             │
│ • W14_S1_R4, DFU 3: 38.9 µm    │
│   [✓ Remove] [Keep]             │
│                                 │
│ [Remove All] [Keep All]         │
└─────────────────────────────────┘
```

**Features:**
- Multiple detection methods: Modified Z-Score, IQR, Isolation Forest
- Visual highlighting of outliers on plot (different color/shape)
- Individual or batch removal
- Undo/redo outlier removal

---

### Phase 3: Smart Series Grouping (Week 5-6)

#### 3.1 Auto-Detect Repeated Devices
**Algorithm:**
```python
# When user loads data:
1. Group by device_id
2. For each device, check if multiple parameter combinations exist
3. If yes, suggest alternative grouping:
   - If multiple flowrates: "Group by flowrate?"
   - If multiple pressures: "Group by pressure?"
   - If multiple test dates: "Group by test date?"
   - If multiple fluids: "Group by fluid?"
```

#### 3.2 Dynamic Series Builder
**Smart Group Modal:**

```
┌──────────────────────────────────────────┐
│ SMART SERIES GROUPING                    │
├──────────────────────────────────────────┤
│ ⚠ Detected: W13_S2_R6 tested at         │
│   multiple conditions                    │
│                                          │
│ Current grouping: device_id              │
│ Result: Overlapping points               │
│                                          │
│ Suggested grouping:                      │
│ ○ Group by flowrate                     │
│   → 2 series: 5ml/hr, 10ml/hr           │
│                                          │
│ ○ Group by pressure                     │
│   → 2 series: 200mbar, 300mbar          │
│                                          │
│ ○ Group by test date                    │
│   → 3 series: Oct 13, Oct 20, Oct 27    │
│                                          │
│ ○ Custom: device_id + flowrate          │
│   → 5 series with unique combos         │
│                                          │
│ [Apply] [Cancel]                         │
└──────────────────────────────────────────┘
```

#### 3.3 Series Color Management
**Advanced Color Panel:**
- Color palette selector (vibrant, pastel, dark, earth, custom)
- Auto-generate shades for related series (e.g., blue family for one device)
- Manual color picker per series
- Preview color blindness simulation

---

### Phase 4: Visual Customization (Week 7-8)

#### 4.1 Style Editor
**Appearance Tab:**

```
┌─────────────────────────┐
│ VISUAL STYLE            │
├─────────────────────────┤
│ Marker Size: [==|==] 6  │
│ Line Width:  [=|===] 1.5│
│ Transparency:[===|=] 0.9│
│                         │
│ Marker Style:           │
│ [Dropdown: Circle ▼]    │
│                         │
│ Color Scheme:           │
│ [Dropdown: Vibrant ▼]   │
│                         │
│ ☑ Show grid            │
│ ☑ Show legend          │
│ ☐ Show error bars      │
│                         │
│ Font Size:              │
│ Title:    [==|==] 14    │
│ Axis:     [=|===] 12    │
│ Legend:   [=|===] 10    │
└─────────────────────────┘
```

#### 4.2 Dodge/Jitter Controls
```
┌─────────────────────────┐
│ POINT POSITIONING       │
├─────────────────────────┤
│ Horizontal Dodge:       │
│ [===|=====] 0.08        │
│                         │
│ Apply to:               │
│ ☑ All overlapping points│
│                         │
│ Order by:               │
│ [Dropdown: Legend ▼]    │
└─────────────────────────┘
```

#### 4.3 Label & Annotation
- Click plot to add text annotations
- Drag to reposition
- Arrow annotations for specific points
- Custom axis limits

---

### Phase 5: Workflow & Export (Week 9-10)

#### 5.1 Save/Load Plot Configurations
```
┌─────────────────────────┐
│ MY CONFIGURATIONS       │
├─────────────────────────┤
│ ☆ W13_DFU_Analysis      │
│ ☆ Pressure_Sweep_5mlhr  │
│ ☆ Device_Comparison     │
│                         │
│ [New] [Save] [Load]     │
└─────────────────────────┘
```

**Features:**
- Save current plot state as JSON
- Quick-load for repeated analysis
- Share configs with team

#### 5.2 Batch Export
```
┌──────────────────────────────────┐
│ EXPORT OPTIONS                   │
├──────────────────────────────────┤
│ Format:                          │
│ ☑ PNG (300 DPI)                 │
│ ☑ SVG (vector)                  │
│ ☐ PDF (publication)             │
│                                  │
│ Size:                            │
│ ○ Standard (12x7)               │
│ ○ Presentation (16x9)           │
│ ○ Custom: [__] x [__]           │
│                                  │
│ Include:                         │
│ ☑ Plot                          │
│ ☑ Legend                        │
│ ☐ Data table                    │
│                                  │
│ [Export] [Export All Configs]    │
└──────────────────────────────────┘
```

#### 5.3 History & Undo
- Timeline of plot changes
- Click to restore previous state
- Compare two versions side-by-side

---

## Technical Architecture

### Backend (Python)
```
src/
  interactive_dash/
    app.py                   # Dash app entry point
    callbacks.py             # All Dash callbacks
    layout.py                # UI layout components
    plot_generator.py        # Plotly plot generation
    data_manager.py          # CSV loading, filtering
    series_analyzer.py       # Auto-detect repeated devices
    outlier_detector.py      # Outlier detection algorithms
    config_manager.py        # Save/load plot configs
```

### Frontend (Dash Components)
- `dash-core-components`: Graphs, dropdowns, sliders
- `dash-bootstrap-components`: Professional styling
- `dash-ag-grid`: Data table
- Custom CSS for branding

### Data Flow
```
User uploads CSV
     ↓
DataManager loads & validates
     ↓
SeriesAnalyzer detects grouping issues
     ↓
User adjusts controls → Callback fired
     ↓
PlotGenerator creates Plotly figure
     ↓
Live preview updates
     ↓
User satisfied → Export PNG/SVG
```

---

## Implementation Phases

### Phase 1: Foundation (2 weeks)
**Deliverables:**
- Basic Dash app structure
- Load CSV, display plot
- Simple controls: X/Y axis, grouping
- PNG export

**Test Criteria:**
- Can load existing exported CSVs
- Can change axes and see plot update
- Can export PNG

### Phase 2: Filtering & Outliers (2 weeks)
**Deliverables:**
- Filter panel with sliders/checkboxes
- Outlier detection integration
- Visual outlier highlighting

**Test Criteria:**
- Filters update plot in real-time
- Outliers detected and removable
- Filtered data matches TUI behavior

### Phase 3: Smart Grouping (2 weeks)
**Deliverables:**
- Auto-detect repeated devices
- Suggest alternative groupings
- Dynamic series builder

**Test Criteria:**
- Correctly identifies W13_S2_R6 multi-condition issue
- Suggests flowrate/pressure/date grouping
- Can split and re-color series

### Phase 4: Visual Polish (2 weeks)
**Deliverables:**
- Full style editor
- Dodge/jitter controls
- Annotation tools

**Test Criteria:**
- All visual parameters adjustable
- Overlapping points separate correctly
- Matches publication standards

### Phase 5: Workflow (2 weeks)
**Deliverables:**
- Save/load configurations
- Batch export
- History/undo

**Test Criteria:**
- Configs saved as JSON
- Can recreate exact plot from config
- Export multiple formats

---

## User Workflow Examples

### Example 1: Single Device, Multiple Flowrates

```
1. User exports: filter device W13_S2_R6 → export
2. Opens interactive plotter
3. Loads CSV
4. ⚠ Warning: "W13_S2_R6 tested at 3 flowrates - points overlap!"
5. User clicks [Smart Group]
6. Selects "Group by flowrate"
7. Plot updates: 3 distinct series (5ml/hr, 10ml/hr, 20ml/hr)
8. User adjusts colors to blue shades
9. Adds dodge to separate points
10. Exports PNG
```

### Example 2: Multi-Device Comparison with Outliers

```
1. User exports: filter device_type W13 → export
2. Opens interactive plotter
3. Loads CSV (5 devices)
4. Clicks [Detect Outliers]
5. 2 outliers found and highlighted in red
6. User reviews: 1 legitimate, 1 defect
7. Removes defect outlier
8. Adjusts pressure range slider: 200-400 mbar
9. Plot updates with filtered data
10. Saves configuration as "W13_Clean_Analysis"
11. Exports PNG + SVG
```

### Example 3: Parameter Sweep Analysis

```
1. User exports: filter device W13_S1_R2 → export (all pressures)
2. Opens interactive plotter
3. Loads CSV
4. Changes grouping from device_id to oil_pressure
5. Plot shows pressure sweep (6 colors, one per pressure)
6. Adds custom annotations: "Optimal range"
7. Adjusts dodge to separate points at DFU 4
8. Exports high-res PNG for paper
```

---

## Integration with Existing System

### Launching Interactive Plotter

**Option A: From TUI**
```bash
>>> export
[OK] Exported to: outputs/W13_export.csv

>>> plot interactive
[Opening interactive plotter in browser...]
http://localhost:8050
```

**Option B: Standalone**
```bash
python src/interactive_dash/app.py

# Browser opens automatically
# User clicks "Load CSV" and browses to exports/
```

**Option C: Direct Launch**
```bash
python src/interactive_dash/app.py --csv outputs/W13_export.csv
# Launches with CSV pre-loaded
```

---

## Dependencies

```python
# requirements.txt additions
dash==2.14.2
dash-bootstrap-components==1.5.0
dash-ag-grid==2.4.0
plotly==5.18.0
kaleido==0.2.1  # For static image export
```

---

## Success Metrics

**User Experience:**
- ✅ Plot updates in <500ms after control change
- ✅ Zero learning curve for basic use
- ✅ Advanced features discoverable
- ✅ Can recreate any plot from saved config

**Technical:**
- ✅ Handles datasets up to 10,000 rows smoothly
- ✅ Responsive on 1080p and 4K displays
- ✅ Browser compatible: Chrome, Firefox, Edge
- ✅ Export quality: 300 DPI minimum

**Scientific:**
- ✅ Plots publication-ready (Nature, Science standards)
- ✅ Outlier detection matches statistical best practices
- ✅ Color schemes accessible (colorblind-friendly)

---

## Future Enhancements (Post-MVP)

### Phase 6+: Advanced Features
- **Statistical overlays**: Trend lines, confidence intervals, ANOVA
- **Faceted plots**: Grid of subplots (facet by device type, fluid, etc.)
- **3D plots**: For three-parameter visualizations
- **Animation**: Time-series progression videos
- **Collaborative**: Share plots via URL, real-time co-editing
- **AI suggestions**: "Users with similar data also plotted..."
- **Report generation**: Auto-generate PDF report with plots + text

---

## Risk Assessment

| Risk | Mitigation |
|------|-----------|
| Performance with large datasets | Implement data sampling for preview, full resolution on export |
| Complex UI overwhelming users | Collapsible panels, progressive disclosure, presets |
| Browser compatibility issues | Test on Chrome, Firefox, Edge; fallback for Safari |
| Save/load config conflicts | Version configs, migration scripts for breaking changes |
| Color scheme accessibility | Include colorblind simulation, WCAG compliance checker |

---

## Development Timeline

| Week | Phase | Deliverable |
|------|-------|-------------|
| 1-2  | Foundation | Basic Dash app, plot preview |
| 3-4  | Filters & Outliers | Dynamic filtering, outlier detection |
| 5-6  | Smart Grouping | Auto-detect, series management |
| 7-8  | Visual Polish | Style editor, annotations |
| 9-10 | Workflow | Save/load, batch export |

**Total: 10 weeks for full MVP**

**Accelerated: 4 weeks for Phase 1-2** (usable product)

---

## Getting Started (Phase 1 MVP)

### Minimal Working Example (1 day)

```python
# src/interactive_dash/simple_app.py
import dash
from dash import dcc, html, Input, Output
import plotly.express as px
import pandas as pd

app = dash.Dash(__name__)

app.layout = html.Div([
    html.H1("Interactive Plot Builder"),

    # File upload
    dcc.Upload(id='upload-data', children=html.Button('Upload CSV')),

    # Controls
    html.Label("X-Axis:"),
    dcc.Dropdown(id='x-axis', options=[], value=None),

    html.Label("Y-Axis:"),
    dcc.Dropdown(id='y-axis', options=[], value=None),

    html.Label("Group By:"),
    dcc.Dropdown(id='group-by', options=[], value=None),

    # Plot
    dcc.Graph(id='main-plot'),

    # Export
    html.Button('Export PNG', id='export-btn')
])

@app.callback(
    Output('main-plot', 'figure'),
    Input('x-axis', 'value'),
    Input('y-axis', 'value'),
    Input('group-by', 'value')
)
def update_plot(x, y, group):
    if not all([x, y]):
        return {}

    # Load data (simplified)
    df = pd.read_csv('outputs/last_export.csv')

    fig = px.scatter(df, x=x, y=y, color=group,
                    hover_data=['device_id', 'dfu_row'])
    return fig

if __name__ == '__main__':
    app.run_server(debug=True)
```

---

## Conclusion

This interactive plotting system addresses the core pain point: **the need to visually explore data and make adjustments before committing to a final plot**.

By implementing in phases, we can:
1. **Deliver value early** (Phase 1 in 2 weeks)
2. **Get user feedback** before building advanced features
3. **Avoid over-engineering** features that won't be used

The Plotly Dash framework provides the perfect balance of:
- Python integration (leverage existing code)
- Professional appearance (publication-ready)
- Rich interactivity (live updates)
- Extensibility (easy to add features)

**Recommendation**: Start with Phase 1 (2 weeks) to validate the approach, then decide on Phase 2+ based on user feedback.
