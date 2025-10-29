# Extractor Agent Tests

This directory contains tests and test fixtures for the **Extractor Agent**, which parses file and folder names to extract structured metadata.

## Agent Responsibility

The Extractor Agent:
- Parses file names following the naming convention pattern
- Extracts metadata from folder hierarchy
- Handles both modern (full metadata in filename) and legacy (metadata in folders) formats
- Parses optional fields like area suffixes (`_B`, `_C`) and timepoints (`_t0`, `_t1`)
- Processes frequency analysis ROI data

## Files in this Directory

### Test Files
- **test_extractor_area_timepoint.py** - Tests area suffix and timepoint parsing
  - Validates optional field detection
  - Tests DFU area parsing (DFU1, DFU1_B, DFU1_C)
  - Tests temporal sequence parsing (t0, t1, t2)

- **test_roi_extraction.py** - Tests frequency analysis ROI data extraction
  - Validates ROI file parsing
  - Tests frequency analysis text file reading
  - Checks data structure correctness

### Test Fixtures
- **0610_2310_W13_S1_R2_5mlhr150mbar_NaCasSO_DFU1_B_t0_ROI1_frequency_analysis.txt**
  - Sample frequency analysis file for testing ROI extraction

- **0610_2310_W13_S1_R2_5mlhr150mbar_NaCasSO_DFU1_B_t0_droplet_annotations_20251024_102722.csv**
  - Sample droplet measurement CSV for testing metadata extraction

## Running Extractor Tests

```bash
# Activate virtual environment
.venv\Scripts\activate

# Run area/timepoint tests
python tests\extractor\test_extractor_area_timepoint.py

# Run ROI extraction tests
python tests\extractor\test_roi_extraction.py
```

## Naming Convention Pattern

Files follow this pattern:
```
BBDD_TTDD_deviceid_flowparams_fluids_DFUx_area_timepoint_type_timestamp.ext
```

Example:
```
0610_2310_w13_s1_r2_5mlhr150mbar_nacasso_DFU1_B_t0_droplet_annotations_20251024_102722.csv
```

### Optional Fields
- **Area suffix:** `_B`, `_C` etc. for multiple measurements on same DFU row
- **Timepoint:** `_t0`, `_t1`, `_t2` etc. for time-series measurements

## Related Components

- **Source Code:** `src/extractor.py`
- **Slash Command:** `.claude/commands/extractor.md`
- **Dependencies:** Python's `re` module for regex parsing

## Notes

- Extractor must handle inconsistent naming gracefully
- Older files may rely more on folder structure than filename
- Parsing logic is flexible to accommodate evolving conventions
