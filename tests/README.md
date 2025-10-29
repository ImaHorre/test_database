# Test Suite Documentation

This directory contains all test scripts and utilities for the OneDrive Database Scanner project.

## Test Files

### 1. test_full_pipeline.py
**Purpose:** End-to-end integration test of the complete pipeline

**What it tests:**
- Scanner → Extractor → CSV Manager full workflow
- Processing of the fake_onedrive_database directory
- Data integrity and completeness validation
- Schema verification
- Duplicate prevention
- Parse quality tracking
- Area/timepoint field population
- Droplet measurement extraction

**Usage:**
```bash
.venv\Scripts\python.exe test_full_pipeline.py
```

**Expected output:**
- Processes 612+ measurement files
- Creates/updates `data/test_database.csv`
- Validates all critical fields are populated
- Reports 100% success rate for data integrity checks

---

### 2. test_scanner_local.py
**Purpose:** Tests local filesystem scanning functionality

**What it tests:**
- Discovery of CSV and TXT files in directory structures
- Recursive traversal of nested folders
- Path extraction and file metadata collection
- File count validation

**Usage:**
```bash
.venv\Scripts\python.exe test_scanner_local.py
```

**Tests against:** `fake_onedrive_database/` directory

---

### 3. test_extractor_area_timepoint.py
**Purpose:** Tests metadata extraction with area and timepoint parsing

**What it tests:**
- File name parsing for DFU rows, areas (A-C), and timepoints (t0, t1, etc.)
- Full path metadata extraction
- Backwards compatibility with simple file names
- Device ID, date, fluid, and flow parameter extraction

**Usage:**
```bash
.venv\Scripts\python.exe test_extractor_area_timepoint.py
```

**Key features tested:**
- Pattern: `DFU1_B_t0_droplet_annotations.csv`
- Optional area field (`_B`, `_C`)
- Optional timepoint field (`_t0`, `_t1`)
- ROI extraction for frequency analysis files

---

### 4. test_roi_extraction.py
**Purpose:** Focused testing of ROI (Region of Interest) extraction

**What it tests:**
- ROI number extraction from frequency analysis files
- Combined parsing of DFU + Area + Timepoint + ROI patterns
- Case-insensitive ROI matching (`_roi` and `_ROI`)

**Usage:**
```bash
.venv\Scripts\python.exe test_roi_extraction.py
```

**Example patterns tested:**
- `DFU3_B_t0_ROI1_frequency_analysis.txt`
- `DFU4_C_t1_ROI4_frequency_analysis.txt`

---

### 5. test_csv_integration.py
**Purpose:** Tests CSV Manager integration and database operations

**What it tests:**
- CSV database creation and updates
- Record deduplication
- Schema consistency
- Incremental updates
- Data merge operations

**Usage:**
```bash
.venv\Scripts\python.exe test_csv_integration.py
```

---

## Utilities

### generate_fake_database.py
**Purpose:** Creates realistic test data structure for development and testing

**What it creates:**
- `fake_onedrive_database/` directory structure
- Multiple device IDs (W13 and W14 variants)
- Multiple bonding and testing date combinations
- Various flow parameters
- DFU measurement CSV files with droplet data
- Frequency analysis TXT files with ROI data
- Files with area suffixes (_B, _C) and timepoints (_t0)

**Usage:**
```bash
.venv\Scripts\python.exe generate_fake_database.py
```

**Output:**
- Creates 600+ test files across 7-8 directory levels
- Mirrors real OneDrive folder structure
- Generates realistic file names matching production patterns

---

## Sample Files

### 0610_2310_W13_S1_R2_5mlhr150mbar_NaCasSO_DFU1_B_t0_droplet_annotations_20251024_102722.csv
Example droplet measurement file showing:
- Bonding date: 06/10
- Testing date: 23/10
- Device: W13_S1_R2
- Flow params: 5ml/hr, 150mbar
- Fluids: NaCas (aqueous), SO (oil)
- DFU row: 1
- Area: B
- Timepoint: t0

### 0610_2310_W13_S1_R2_5mlhr150mbar_NaCasSO_DFU1_B_t0_ROI1_frequency_analysis.txt
Example frequency analysis file with ROI data

---

## Running All Tests

To run the complete test suite in sequence:

```bash
# 1. Generate fresh test data
.venv\Scripts\python.exe tests\generate_fake_database.py

# 2. Test individual components
.venv\Scripts\python.exe tests\test_scanner_local.py
.venv\Scripts\python.exe tests\test_extractor_area_timepoint.py
.venv\Scripts\python.exe tests\test_roi_extraction.py
.venv\Scripts\python.exe tests\test_csv_integration.py

# 3. Test full pipeline
.venv\Scripts\python.exe tests\test_full_pipeline.py
```

---

## Test Data Location

**Fake Database:** `fake_onedrive_database/` (in project root)
**Output Database:** `data/test_database.csv`
**Backup Database:** `data/test_database.csv.backup`

---

## Debugging Tips

1. **If test_full_pipeline.py fails:**
   - Check that `fake_onedrive_database/` exists
   - Verify `data/` directory is writable
   - Review console output for specific validation failures

2. **If parsing tests fail:**
   - Check file naming patterns match expected format
   - Verify regex patterns in `src/extractor.py`
   - Test with sample files in this directory

3. **If scanner fails to find files:**
   - Ensure paths use Windows backslashes or raw strings
   - Verify directory exists and is accessible
   - Check for permission issues

---

## Expected Test Results

All tests should achieve:
- 100% file discovery rate
- 100% parse success for properly formatted files
- Zero duplicate records
- Complete schema coverage
- Proper area/timepoint extraction

If tests consistently fail, regenerate test data with `generate_fake_database.py`.
