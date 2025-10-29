# Natural Language Query Guide

Complete guide for using natural language queries to interact with the microfluidic device database.

## Quick Start

### Using the CLI

**Interactive Mode** (recommended for exploratory analysis):
```bash
python query_cli.py
```

**One-Shot Mode** (for single queries or scripting):
```bash
python query_cli.py "your query here"
```

**Get Help**:
```bash
python query_cli.py "help"
```

### Using the Dashboard

1. Launch the dashboard:
   ```bash
   python dashboard.py
   ```

2. Click **[Q] Ask a Question (Natural Language)**

3. Enter your query in plain English

4. Click **Run Analysis**

5. View results in the right panel

## Query Examples by Category

### Comparisons
Compare devices, device types, or parameters:

```
"Compare W13 and W14 devices"
"Compare devices at 5 ml/hr flowrate"
"Show me the difference between W13 and W14"
"Compare all devices at 500 mbar pressure"
```

**What happens:**
- Filters data based on your criteria
- Generates comparison plot
- Shows statistical summary
- Saves plot to `outputs/analyst/plots/`

### Filtering
Find specific devices or conditions:

```
"Show me all W13 devices"
"Filter by flowrate 5 ml/hr"
"Find devices with NaCas fluid"
"Show me devices at 5 ml/hr and 500 mbar"
```

**What happens:**
- Filters database by criteria
- Returns matching records
- Displays data preview
- Shows count of matches

### Analysis
Analyze parameter effects and correlations:

```
"Analyze flowrate effects for W13"
"What's the effect of pressure on droplet size?"
"Show correlation between flowrate and droplet size"
"Analyze parameter effects for W14"
```

**What happens:**
- Statistical analysis of parameter effects
- Generates scatter plot or correlation plot
- Shows correlation coefficient
- Provides insights

### Tracking
Monitor device performance over time:

```
"Track W13_S1_R1 over time"
"Show device history for W13_S1_R2"
"Monitor W14_S1_R1 performance"
"How has W13_S1_R1 performed over time?"
```

**What happens:**
- Filters data for specific device
- Generates time-series plot
- Shows date range
- Calculates mean and std deviation

### Plotting
Generate visualizations:

```
"Plot device type comparison"
"Visualize flowrate effects"
"Create a graph of W13 vs W14"
"Plot DFU row performance"
```

**What happens:**
- Routes to appropriate plot type
- Generates high-quality PNG
- Saves to outputs folder
- Displays file path

### Reporting
Generate summary reports:

```
"Generate a summary report"
"Create a report"
"Summarize the data"
```

**What happens:**
- Creates comprehensive text report
- Includes statistics for all devices
- Lists all measurements
- Saves to `outputs/` folder

### Listing
View available data:

```
"List all devices"
"What devices are available?"
"Show me all device types"
"Which devices have been tested?"
```

**What happens:**
- Lists all unique devices
- Shows test counts
- Displays date ranges
- Provides device type breakdown

## Tips for Better Queries

### Be Specific
**Good:** "Compare W13 devices at 5 ml/hr"
**Less specific:** "Compare devices"

### Include Units
**Good:** "Filter by flowrate 5 ml/hr"
**Also works:** "Filter by flowrate 5"

### Use Device IDs for Tracking
**Good:** "Track W13_S1_R1 over time"
**Won't work:** "Track device 1" (ambiguous)

### Combine Criteria
**Good:** "Show me W13 devices at 5 ml/hr and 500 mbar"
**Also works:** Individual filters

### Ask for Clarification
If your query is unclear, the system will ask:
```
Query> "Analyze something"
[Clarification Needed]
Which device type would you like to analyze? (W13 or W14)
```

## Understanding Results

### Success Response
```
[Success]
Comparison complete! Found 3 devices.
Device type: W13

Plot saved: outputs/analyst/plots/nl_query_compare_20251029_233000.png
```

### Clarification Needed
```
[Clarification Needed]
Which device type would you like to analyze? (W13 or W14)
```

### Error Response
```
[Error]
No data found for device W99_S1_R1
```

## Advanced Usage

### Scripting with One-Shot Mode

Create a batch script to run multiple queries:

**Windows (batch.bat):**
```batch
@echo off
python query_cli.py "list all devices" > devices.txt
python query_cli.py "compare W13 and W14 devices"
python query_cli.py "generate a summary report"
```

**Linux/Mac (batch.sh):**
```bash
#!/bin/bash
python query_cli.py "list all devices" > devices.txt
python query_cli.py "compare W13 and W14 devices"
python query_cli.py "generate a summary report"
```

### Redirecting Output

Save query results to file:
```bash
python query_cli.py "list all devices" > device_list.txt
```

Suppress logging (show only results):
```bash
python query_cli.py "list all devices" 2>/dev/null  # Linux/Mac
python query_cli.py "list all devices" 2>nul        # Windows
```

## Troubleshooting

### "No data found"
**Problem:** Query returned empty result
**Solution:**
- Check device ID spelling (case sensitive: W13_S1_R1)
- Verify device exists: `python query_cli.py "list all devices"`
- Try broader query first, then filter

### "Clarification needed"
**Problem:** Query too ambiguous
**Solution:**
- Add more details (device type, parameters)
- Follow the clarifying question
- See examples above for proper syntax

### Unicode errors on Windows
**Problem:** Character encoding issues
**Solution:**
- Already fixed in current version
- If issues persist, use `--no-color` flag:
  ```bash
  python query_cli.py --no-color "your query"
  ```

### Plots not generating
**Problem:** No plot file created
**Solution:**
- Check `outputs/analyst/plots/` directory exists
- Ensure matplotlib backend is working
- Try simpler query first (e.g., "list all devices")

## File Outputs

### Plot Files
- **Location:** `outputs/analyst/plots/`
- **Format:** PNG (300 DPI)
- **Naming:** `nl_query_{type}_{timestamp}.png`
- **Example:** `nl_query_compare_20251029_233000.png`

### Report Files
- **Location:** `outputs/`
- **Format:** TXT
- **Naming:** `nl_query_report_{timestamp}.txt`
- **Example:** `nl_query_report_20251029_233000.txt`

## Integration with Other Tools

### From Python Code
```python
from src import DataAnalyst

analyst = DataAnalyst()
result = analyst.process_natural_language_query("compare W13 and W14 devices")

print(result['message'])
print(result['status'])
if result.get('plot_path'):
    print(f"Plot: {result['plot_path']}")
```

### From Other LLMs (ChatGPT, Gemini)
The CLI interface works independently of Claude Code, so you can:
1. Copy query syntax from this guide
2. Use in any LLM conversation
3. Run via command line as suggested by LLM
4. Share results across team with different LLM subscriptions

## Query Syntax Reference

### Device Types
- `W13`, `W14` (case insensitive)

### Device IDs
- Format: `W13_S1_R1`, `W14_S2_R3`
- Always specify full ID with shim and replica

### Flow Parameters
- **Flowrate:** "5 ml/hr", "30 mlhr", "flowrate of 5"
- **Pressure:** "500 mbar", "100 mbar", "pressure of 350"

### Fluids
- `NaCas`, `SDS`, `SO` (case insensitive)

### Metrics
- `droplet size`, `droplet`, `size` → droplet_size_mean
- `frequency`, `freq` → frequency_mean

### Keywords by Intent
- **Compare:** compare, comparison, versus, vs, difference, between
- **Filter:** filter, show me, give me, find, only, with, having
- **Analyze:** analyze, analysis, effect, impact, correlation, relationship
- **Track:** track, monitor, follow, history, over time, temporal
- **Plot:** plot, graph, chart, visualize, visualization
- **Report:** report, summary, summarize
- **List:** list, show all, what are, available, which devices

## Related Documentation

- **Phase 3 Completion:** `tests/analyst/phase_completion/PHASE3_COMPLETE.md`
- **Analyst README:** `tests/analyst/README.md`
- **Dashboard Guide:** `docs/analyst/DASHBOARD_USER_GUIDE.md`
- **Project Overview:** `README.md`

## Support

For issues or questions:
1. Check this guide first
2. Try the `help` command
3. Review example queries above
4. Check Phase 3 documentation for technical details

---

**Happy Querying!**
