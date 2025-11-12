# Prompt for Claude: Design JSON Plot Configs for My TUI Plotting System

I have a codebase with:

- A **TUI** that:
  - Filters a large measurement database.
  - Can **export the filtered data as a tidy CSV**.
  - Has a `plot` command and a half-finished `plotws` “workspace” idea that I’d like to rebuild properly.

My goal with you:

> We will design a **small library of JSON plot config files** that describe the plots I commonly want to make.  
> My code will later read these JSON configs and use them to generate plots from *any* compatible CSV (same schema, different filters).

I **do not** want you to write a whole plotting engine, just the **configs and their schema**.

---

## 1. Data model (what the CSV looks like)

Assume that for each filtered result, I can export a CSV in a **tidy** format.  
Each row = one measurement.

Typical columns (these names might need to be adjusted after I show you a real sample):

- `device_id` – e.g. `"W13_S1_R2"`
- `test_id` – distinguishes multiple tests/runs on the same device (possibly different days)
- `dfu_index` – an integer index or position (DFU number)
- `flowrate_ml_hr`
- `pressure_mbar`
- `fluid` – e.g. `"SDS_SO"`
- `droplet_size` – numeric (µm)
- `frequency` – numeric (Hz)
- `run_timestamp` – ISO timestamp or date
- maybe other numeric variables later

Everything we do should **only reference column names** that are actually present in the data.  
Configs should be **data-agnostic**: they must work for any subset/filter of this schema, not just one specific device or fluid.

---

## 2. PlotConfig JSON schema

We’ll define a **PlotConfig** object in JSON. My plotting code will later do something like:

```python
df = load_filtered_csv(...)
cfg = load_json("some_preset.json")
plot_from_config(df, cfg)
```

I want you to help me:

1. Refine the **schema** (which keys exist, what they mean).
2. Design **5–6 “preset” configs** for my most common plots.

### Initial PlotConfig idea

Let’s start with this schema (you can refine it, but keep it simple and consistent):

```json
{
  "name": "short_machine_readable_name",
  "description": "One sentence human description of the plot.",

  "x": "column_name_for_x_axis",
  "y": ["one_or_more_y_columns"],

  "group": "column_to_use_for_series_or_color (or null)",
  "facet_row": "column_for_row_facets (or null)",
  "facet_col": "column_for_column_facets (or null)",

  "plot_type": "line | scatter | line+markers",

  "aggregate": "none | mean | median",
  "error": "none | std | sem",

  "x_scale": "linear | log",
  "y_scale": "linear | log",

  "title": "Optional plot title template string",
  "x_label": "Optional x-axis label",
  "y_label": "Optional y-axis label"
}
```

Constraints / Notes:

- `name` should be a stable identifier (e.g. `"dfu_vs_droplet_size_by_test"`).
- `description` is just for humans, but please include it.
- If `aggregate = "none"`, treat each row as a raw point.
- If `aggregate` is `mean`/`median`, the intention is roughly:  
  group by `[x, group]` (or `[x]` if no group) → aggregate y’s, and `error` describes what error bars could be drawn.
- Don’t invent extra fields unless needed; if you add some, document them clearly.
- Don’t hard-code specific values like `"W13_S1_R2"` or `"SDS_SO"` inside configs; filtering is done *before* plotting.

---

## 3. The kinds of plots I want

We will iteratively design ~5 presets.  
Here are the **types of plots** I care about:

1. **DFU sweep plot**  
   - X: `dfu_index`  
   - Y: `droplet_size` (and `frequency` in a sep plot)  
   - Series: separate line per `test_id` (or `device_id` or 'pressure')  
   - No aggregation (show every DFU measurement).

2. **Pressure vs droplet size (per device)**  
   - X: `pressure_mbar`  
   - Y: `droplet_size`  
   - Group: `device_id` (each device gets a line)  
   - Optionally aggregate multiple rows at same pressure by mean + std.

3. **Flowrate vs droplet size**  
   - X: `flowrate_ml_hr`  
   - Y: `droplet_size`  
   - Group: maybe `device_id` or `fluid`.  
   - Often aggregated by mean per flowrate.

4. **Frequency vs pressure**  
   - X: `pressure_mbar`  
   - Y: `frequency`  
   - Group: `device_id` or `test_id`.

5. **Stability over time** (if `run_timestamp` is available)  
   - X: `run_timestamp` (or derived time index)  
   - Y: `droplet_size` or `frequency`  
   - Group: `device_id` or `test_id`.  
   - Often scatter or line+markers.

You can suggest better choices for axes/grouping/title/labels based on this.

---

## 4. How I want you to work

For each preset we design, please:

1. **Restate the intent**  
   - In plain English: what this plot shows and why.

2. **Specify the JSON PlotConfig**  
   - Using the schema above.
   - Only reference real column names (we can adjust names once I show you a CSV sample).
   - Use a fenced code block with language `json`.

3. **Add usage notes**  
   - “This preset expects columns: …”
   - “Works well when the TUI has already filtered to a single fluid and flowrate” etc.

4. **Keep configs reusable**  
   - No hard-coded filters inside the JSON.  
   - All filtering is done outside, in my TUI.  
   - The config should be usable with any filtered subset of the data that still has the required columns.

### Output format for each preset

Please use this structure for each preset you propose:

```markdown
## Preset: <human readable name>

**Intent:** Short description of what this plot is for.

**Assumptions / required columns:**
- `...`
- `...`

**PlotConfig JSON:**

```json
{
  "...": "..."
}
```
```

---

## 5. First task

1. First, **review and improve** the PlotConfig schema if you see obvious issues, but keep it reasonably small and simple.
2. Then, design **at least 5 presets** based on the plot types I listed:
   - DFU sweep
   - Pressure vs droplet size
   - Flowrate vs droplet size
   - Frequency vs pressure
   - Stability over time

we can work on more presets later on. 

there may be already some plot preset type code relating to 'plot' in tui and 'plotws' we can rego over some of these if theya re still valubale. i was just having issues with these features. 

All csv imports will ahve the same columns as the main database.csv (the plots will jsut be amde froma  small portio of filtered data)

Remember:  
You are **not** writing the plotting code, only the **JSON configs + clear descriptions** so I can wire them into my TUI’s plotting system.


The primary importantce here is to get teh pliots visualy and functioanlk very nice, save the configs and allow new data to be introduced and everything fix iteslef so ic an have plots formated int eh same manner with minimal inmtervention by giving making new filtered data. for example dfu sweep: one plot could be showing the behavious of all W1 devices (many data points/series, another plot could be just teh w14 decvices testered at 5mlhr but still shwoing DFU index on teh x and droplet size on the y and splitting each series into its onw colour/line with or wthout error bars etc . If it helps i can copy in some code/pngs of plots i like the look of during out planning session 
