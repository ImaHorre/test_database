======================================================================
MICROFLUIDIC DEVICE ANALYSIS DASHBOARD
======================================================================

Total Records:     612
Unique Devices:    5

Device Types:
  • W13: 396 measurements
  • W14: 216 measurements

Measurement Files:
  • CSV (droplet data):    102
  • TXT (frequency data):  510

Date Range:        2025-08-23 to 2025-10-01

Last updated:      2025-11-02 17:22:22
======================================================================

QUICK ACTIONS:
  [1] Compare Devices at Same Parameters
  [2] Analyze Flow Parameter Effects
  [3] Track Device Over Time
  [4] Compare DFU Row Performance
  [5] Compare Fluid Types
  [6] View All Available Devices

  [R] Refresh Database
  [H] Help - Show all commands
  [Q] Quit

SESSION COMMANDS:
  show filters, clear filters, history, repeat last
  cache stats, clear cache (performance monitoring)

Or type a command/query (e.g., 'show w13 at 5mlhr 200mbar')
----------------------------------------------------------------------
>>> show w13

Records for W13:
Total: 396 measurements

Devices (3):
  • W13_S1_R1: 216 measurements
  • W13_S1_R2: 72 measurements
  • W13_S2_R2: 108 measurements

>>> show w13 5mlhr

Records for W13:
Total: 396 measurements

Devices (3):
  • W13_S1_R1: 216 measurements
  • W13_S1_R2: 72 measurements
  • W13_S2_R2: 108 measurements

>>> show w13 at 5mlhr

Filter: device_type=W13, flowrate=5mlhr
Found: 2 complete droplet analysises, 2 complete frequency analysises

Matching Devices:
  1. W13_S1_R1:
     • 5ml/hr + 200mbar (SDS_SO): 6 DFU rows, 30 frequency measurements
  2. W13_S2_R2:
     • 5ml/hr + 300mbar (SDS_SO): 6 DFU rows, 30 frequency measurements

Flow Parameter Combinations in Results:
  1. 5ml/hr + 200mbar (SDS_SO): 1 devices
  2. 5ml/hr + 300mbar (SDS_SO): 1 devices

Droplet Size: 24.88 ± 0.52 µm
Frequency:    9.22 ± 5.51 Hz

>>> [W13@5mlhr] plot

Processing query...
Using active filters: {'device_type': 'W13', 'flowrate': 5}

============================================================
PLOT GENERATION PREVIEW
============================================================
Query: plot

Data to be plotted:
  • 72 total measurements
  • 2 unique devices
  • 2 complete droplet analyses
  • 2 complete frequency analyses

Devices to be included:
  • W13_S1_R1: 5ml/hr+200mbar
  • W13_S2_R2: 5ml/hr+300mbar

⚠️  Potential issues:
  • More than 50% of measurements missing droplet size data

============================================================

Generate plot? (y/n): y
INFO:src.analyst:Processing natural language query: plot
INFO:src.query_processor:Processing query: plot
INFO:src.query_processor:Detected intent: plot (confidence: 0.50)
INFO:src.query_processor:Extracted entities: {}

[Clarification Needed]

What would you like to plot? Try specifying a device type, device ID, or parameters.

>>> [W13@5mlhr] plot drop_measure

Processing query...
Using active filters: {'device_type': 'W13', 'flowrate': 5}

============================================================
PLOT GENERATION PREVIEW
============================================================
Query: plot drop_measure

Data to be plotted:
  • 72 total measurements
  • 2 unique devices
  • 2 complete droplet analyses
  • 2 complete frequency analyses

Devices to be included:
  • W13_S1_R1: 5ml/hr+200mbar
  • W13_S2_R2: 5ml/hr+300mbar

⚠️  Potential issues:
  • More than 50% of measurements missing droplet size data

============================================================

Generate plot? (y/n): y
INFO:src.analyst:Processing natural language query: plot drop_measure
INFO:src.query_processor:Processing query: plot drop_measure
INFO:src.query_processor:Detected intent: plot (confidence: 0.50)
INFO:src.query_processor:Extracted entities: {}

[Clarification Needed]

What would you like to plot? Try specifying a device type, device ID, or parameters.

>>> [W13@5mlhr] 5mlhr

Processing query...
INFO:src.analyst:Processing natural language query: 5mlhr
INFO:src.query_processor:Processing query: 5mlhr
INFO:src.query_processor:Detected intent: help (confidence: 0.00)
INFO:src.query_processor:Extracted entities: {'flowrate': 5}
WARNING:src.query_handlers.router:Unknown intent type: help

[Error]

Unknown query type 'help'. Available types: list, filter, compare, analyze, track, plot, plot_dfu, report

>>> [W13@5mlhr] h

======================================================================
COMMAND REFERENCE
======================================================================

QUICK COMMANDS:
  show [device_type]                 - Show all records for device type
    Example: show w13

  show [device_type] at [params]     - Filter by flow parameters
    Example: show w13 at 5mlhr 200mbar
    Example: show w14 at 5mlhr

  show params for [device_type]      - Show all parameter combinations
    Example: show params for w13

  list devices                       - List all devices
  list types                         - List all device types
  list params                        - List all flow parameters

  count [device_type]                - Count records
    Example: count w13

  stats [device_type]                - Show statistics
    Example: stats w13
  stats [device_type] at [params]    - Show filtered statistics
    Example: stats w13 at 5mlhr 200mbar

SESSION MANAGEMENT:
  show filters                       - Display active filters
  clear filters                      - Clear all active filters
  history                            - Show recent query history
  repeat last                        - Repeat the last query

PERFORMANCE:
  cache stats                        - Show query cache statistics
  clear cache                        - Clear query cache (debug)

  NOTE: Filter commands set active filters shown in prompt
  Example: 'show w13 at 5mlhr' sets [W13@5mlhr] filters

NATURAL LANGUAGE:
  You can also use natural language queries:
    - Compare W13 and W14 devices
    - Track W13_S1_R1 over time
    - Analyze flowrate effects for W13

PLOT COMMANDS:
  All plot commands now show preview and ask for confirmation
  Add --preview flag for dry-run mode (no plot generation)
    Example: plot W13 droplet sizes --preview

NUMBERED ACTIONS:
  Type 1-6 to run quick actions from the menu

======================================================================

>>> [W13@5mlhr] plot w13 5mlhr droplet sizes

Processing query...
Using active filters: {'device_type': 'W13', 'flowrate': 5}

============================================================
PLOT GENERATION PREVIEW
============================================================
Query: plot w13 5mlhr droplet sizes

Data to be plotted:
  • 72 total measurements
  • 2 unique devices
  • 2 complete droplet analyses
  • 2 complete frequency analyses

Devices to be included:
  • W13_S1_R1: 5ml/hr+200mbar
  • W13_S2_R2: 5ml/hr+300mbar

⚠️  Potential issues:
  • More than 50% of measurements missing droplet size data

============================================================

Generate plot? (y/n): y
INFO:src.analyst:Processing natural language query: plot w13 5mlhr droplet sizes
INFO:src.query_processor:Processing query: plot w13 5mlhr droplet sizes
INFO:src.query_processor:Detected intent: plot (confidence: 0.50)
INFO:src.query_processor:Extracted entities: {'device_type': 'W13', 'flowrate': 5, 'metric': 'droplet_size_mean'}
INFO:src.analyst:Filtered to W13: 396 records
INFO:src.analyst:Parameter effect plot saved: outputs/analyst/plots/nl_query_analysis_20251102_172423.png
INFO:src.analyst:Parameter effect analysis complete: correlation = 0.066

[Success]

Analysis complete for W13!

Parameter: aqueous_flowrate
Metric: droplet_size_mean
Correlation: 0.066
Total measurements: 66


Plot saved: outputs/analyst/plots/nl_query_analysis_20251102_172423.png

>>> [W13@5mlhr]




look at how i am intereacting with this tui. and ntoice hows its not doing as I want. we need better summaries and helpful command writing. the natrual language parsing is a good idea and should defiently be our way forward but maybe having knoweldgebale syntax and being able to navigate what we want is also good. 

exmpanple; i didnt tpe shiow w13 'at' 5mlhr, i missed that at and the terminal didnt run. how can we better handle things like this, the user not inputting exxacftgltyy teh right sysntax. is there a helpful return that can be offered instread when the parsing doesnt work. like 'did you mean' but realistically in this scenario the tui should have known what i wanted. 

next i have found some data 5mlhr w13. i type plot.  this shiuld and does initiante a plot and rightfully needs more info. great. lets offer options. what coudl the user possibly want to plot. remembering we have the w13 5mlhr in cache. we can look at droplet measuremnt or frequency measuremnt as our main outputs. does the user want to plot the two devices comparatively. does the user want both variables, and if so on seperate graphs? these can all be listeed in order with options of what to choose a, b,c etc. i want the user to do as little  tpying where he could type wrng and instead be offered a list of options for what is possible 
