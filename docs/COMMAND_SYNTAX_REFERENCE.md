# Dashboard Command Syntax Reference

**Quick reference for standard command patterns in the microfluidic device analysis terminal UI**

---

## Basic Syntax Patterns

### 1. Device Filtering

**Pattern:** `show <device_type> [at <flowrate>mlhr] [<pressure>mbar]`

```bash
show w13                    # All W13 devices
show w14                    # All W14 devices
show w13 at 5mlhr           # W13 at 5ml/hr (any pressure)
show w13 at 200mbar         # W13 at 200mbar (any flow rate)
show w13 at 5mlhr 200mbar   # W13 at specific conditions
```

**Behavior:**
- Sets active filters shown in prompt: `>>> [W13@5mlhr]`
- Filters persist until cleared
- Subsequent commands can build on these filters

---

### 2. Statistics

**Pattern:** `stats <device_type> [at <flowrate>mlhr] [<pressure>mbar]`

```bash
stats w13                   # Statistics for all W13 data
stats w13 at 5mlhr          # W13 at 5ml/hr only
stats w13 at 5mlhr 200mbar  # Specific experimental condition
```

**Output Includes:**
- Analysis summary (complete/partial counts)
- Device breakdown by experimental condition
- Droplet size statistics (mean, std, min, max)
- Frequency statistics (if available)
- Flow parameters tested

**Known Issue:** `stats` (no parameters) doesn't work yet - must specify device type

---

### 3. Parameter Discovery

**Pattern:** `show params for <device_type>` OR `show all flow parameter combinations`

```bash
show params for w13                    # All parameters tested for W13
show params for w14                    # All parameters tested for W14
show all flow parameter combinations   # All params across all devices
```

**Output Shows:**
- Flow rate + pressure combinations
- Number of complete analyses per combination
- Number of devices tested at each condition

---

### 4. Listing Commands

**Pattern:** `list <what>`

```bash
list devices        # Show all device IDs with measurement counts
list types          # Show device types (W13, W14, etc.)
list params         # Show all flow parameters across all devices
```

---

### 5. Session Management

**Pattern:** Single keyword commands

```bash
show filters        # Display currently active filters
clear filters       # Clear all active filters
history             # Show recent command history with timestamps
repeat last         # Repeat the last executed command
repeat              # Shorthand for repeat last
```

**Filter Display:**
```
Active filters:
  • device_type: W13
  • flowrate: 5
```

---

### 6. Performance Monitoring

**Pattern:** Debug/admin commands

```bash
cache stats         # Show query cache statistics
clear cache         # Clear query cache (forces fresh queries)
```

**Cache Stats Output:**
```
Cache Statistics:
  • DataFrame cache entries: 3
  • Cache size limit: 30
  • TTL: 15.0 minutes
  • Current data hash: a3f2c8b1...
```

---

## Natural Language Queries (Experimental)

The system also accepts natural language queries, but with lower reliability:

```bash
compare w13 and w14 devices
show me w13 devices at 5ml/hr
track w13_s1_r1 over time
analyze flowrate effects for w13
plot droplet sizes for w13
```

**Important:**
- NL queries go through intent detection (may misinterpret)
- Simple commands (above) are more reliable
- When in doubt, use explicit command syntax

---

## Command Workflow Examples

### Example 1: Explore W13 Devices

```bash
>>> show w13
Records for W13:
Total: 396 measurements
...

>>> show params for w13
Flow Parameter Combinations for W13:
  1. 5ml/hr + 200mbar: 1 partial, 1 devices
  2. 5ml/hr + 300mbar: no complete analyses, 1 devices
  ...

>>> show w13 at 5mlhr
[Sets filters: W13@5mlhr]
Filter: device_type=W13, flowrate=5mlhr
Found: 1 partial analysis
...

>>> stats w13 at 5mlhr
[Uses existing filters + new parameter]
Statistics for device_type=W13, flowrate=5mlhr:
Analysis Summary:
  Partial Analyses:             1
  Total Raw Measurements:       72
  ...
```

---

### Example 2: Filter and Refine

```bash
>>> show w13 at 5mlhr
[Prompt changes to: >>> [W13@5mlhr]]

>>> show filters
Active filters:
  • device_type: W13
  • flowrate: 5

>>> stats w13 at 5mlhr 200mbar
[Adds pressure filter for this command only]
...

>>> clear filters
[Prompt returns to: >>>]

>>> show filters
No active filters.
```

---

### Example 3: Repeat and History

```bash
>>> show w13 at 5mlhr 200mbar
[Output...]

>>> repeat last
Repeating: show w13 at 5mlhr 200mbar
[Same output...]

>>> history
Recent queries:
   1. [12:30:15] show w13
   2. [12:30:45] show w13 at 5mlhr
   3. [12:31:20] show w13 at 5mlhr 200mbar
   4. [12:31:55] repeat last
```

---

## Common Issues and Solutions

### Issue: "Command not recognized"

**Problem:**
```bash
>>> stats
[ERROR] Command 'stats' not recognized.
```

**Solution:**
Must specify device type: `stats w13`

OR set filters first:
```bash
>>> show w13 at 5mlhr
>>> stats w13      # Now stats knows to look at W13
```

**Known Bug:** `stats` should use active filters but doesn't yet

---

### Issue: Filters not applying to subsequent commands

**Symptoms:** You set filters but next command ignores them

**Solution:**
- Only `show <type> at <params>` commands SET filters
- Other commands may or may not USE filters (inconsistent currently)
- Use `show filters` to verify what's active

**Workaround:** Repeat filter parameters in each command for now

---

### Issue: Incomplete device breakdown

**Symptoms:**
```
Unique Devices:               2
Device Breakdown:
  W13_S1_R1:        # Only shows 1 device!
```

**Known Bug:** Device breakdown iteration incomplete
**Workaround:** Check "Flow Parameter Combinations" section for full list

---

## Tips and Best Practices

### 1. Use Filters for Complex Workflows

Instead of:
```bash
stats w13 at 5mlhr 200mbar
stats w13 at 5mlhr 300mbar
stats w13 at 5mlhr 400mbar
```

Do:
```bash
show w13 at 5mlhr
# [Filters set, now can vary pressure easily]
stats w13 at 5mlhr 200mbar
stats w13 at 5mlhr 300mbar
```

### 2. Check Data Before Plotting

```bash
show w13 at 5mlhr           # See what devices match
stats w13 at 5mlhr          # Verify data completeness
plot w13 droplet sizes      # Then plot
```

### 3. Use `show params` for Discovery

When you don't know what parameters exist:
```bash
list types                  # What device types exist?
show params for w13         # What has been tested for W13?
list devices                # What specific devices do I have?
```

### 4. Monitor Performance with Cache Stats

```bash
cache stats                 # Check if queries are being cached
clear cache                 # Force fresh data if results seem stale
```

---

## Command Aliases

Some commands have shorthand forms:

| Full Command | Shorthand | Alias |
|--------------|-----------|-------|
| `repeat last` | `repeat` | - |
| - | `h` | `help` |
| - | `m` | `menu` |
| - | `q` | `quit`, `exit` |
| - | `r` | `refresh` |

---

## Exit Commands

```bash
q           # Quit dashboard
quit        # Quit dashboard
exit        # Quit dashboard
```

---

## Getting Help

```bash
help        # Show full command reference
menu        # Show quick action menu
h           # Shorthand for help
```

---

## Future Commands (Not Yet Implemented)

These commands are planned but not yet available:

```bash
stats                       # Use active filters (currently errors)
plot preview <...>          # Dry-run mode for plots
export <query> to csv       # Export filtered data
save query as <name>        # Save query templates
```

---

**Last Updated:** 2025-11-02
**Dashboard Version:** dashboard_v2.py
**Test Coverage:** 24/24 core tests passing
**Known Issues:** See TUI_ASSESSMENT_REPORT.md for details
