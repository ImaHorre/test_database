# Test Suite Documentation

This directory contains all test scripts and utilities for the OneDrive Database Scanner project, organized by agent/component.

## Directory Structure

Tests are organized by the agent they relate to:

```
tests/
├── scanner/          - Scanner Agent tests
├── extractor/        - Extractor Agent tests
├── csv_manager/      - CSV Manager Agent tests
├── analyst/          - Analyst Agent tests and phase documentation
└── integration/      - Full pipeline integration tests
```

Each subdirectory has its own README.md explaining:
- The agent's responsibility
- What the tests cover
- How to run the tests
- Related components

## Quick Start

### Running Tests by Agent

```bash
# Activate virtual environment
.venv\Scripts\activate

# Scanner tests
python tests\scanner\test_scanner_local.py

# Extractor tests
python tests\extractor\test_extractor_area_timepoint.py
python tests\extractor\test_roi_extraction.py

# CSV Manager tests
python tests\csv_manager\test_csv_integration.py

# Analyst tests
python tests\analyst\test_phase1_methods.py

# Integration tests (full pipeline)
python tests\integration\test_full_pipeline.py
```

### Running All Tests in Sequence

```bash
# 1. Generate fresh test data (if needed)
python tests\scanner\generate_fake_database.py

# 2. Test individual components
python tests\scanner\test_scanner_local.py
python tests\extractor\test_extractor_area_timepoint.py
python tests\extractor\test_roi_extraction.py
python tests\csv_manager\test_csv_integration.py

# 3. Test full pipeline
python tests\integration\test_full_pipeline.py
```

## Agent Overview

### Scanner Agent
**Responsibility:** Traverse OneDrive directories and identify measurement files

**Tests:** `tests/scanner/`
- `test_scanner_local.py` - File discovery and traversal
- `generate_fake_database.py` - Test data generator

**Source:** `src/scanner.py`

---

### Extractor Agent
**Responsibility:** Parse filenames and extract structured metadata

**Tests:** `tests/extractor/`
- `test_extractor_area_timepoint.py` - Area suffix and timepoint parsing
- `test_roi_extraction.py` - Frequency analysis ROI extraction

**Source:** `src/extractor.py`

---

### CSV Manager Agent
**Responsibility:** Maintain database and handle incremental updates

**Tests:** `tests/csv_manager/`
- `test_csv_integration.py` - Database operations and integrity

**Source:** `src/csv_manager.py`

---

### Analyst Agent
**Responsibility:** Process queries and generate reports/visualizations

**Tests:** `tests/analyst/`
- `test_phase1_methods.py` - Basic plotting and analysis methods

**Documentation:** `tests/analyst/phase_completion/`
- Phase completion milestones and feature documentation

**Source:** `src/analyst.py`

---

### Integration Tests
**Responsibility:** Validate full pipeline end-to-end

**Tests:** `tests/integration/`
- `test_full_pipeline.py` - Complete workflow validation

**Pipeline Flow:** Scanner → Extractor → CSV Manager → Analyst

---

## Test Data Location

- **Fake Database:** `fake_onedrive_database/` (project root)
- **Test Output Database:** `data/test_database.csv`
- **Test Backup:** `data/test_database.csv.backup`

## Sample Test Files

The `extractor/` directory contains sample files for testing:
- **CSV file:** Example droplet measurement with area/timepoint metadata
- **TXT file:** Example frequency analysis with ROI data

## Expected Test Results

All tests should achieve:
- 100% file discovery rate (Scanner)
- 100% parse success for properly formatted files (Extractor)
- Zero duplicate records (CSV Manager)
- Complete schema coverage (CSV Manager)
- Proper area/timepoint extraction (Extractor)
- Valid data flow end-to-end (Integration)

## Debugging Tips

### Scanner Issues
- Check that `fake_onedrive_database/` exists
- Verify directory permissions
- Ensure paths use correct format for Windows

### Extractor Issues
- Verify file naming matches expected patterns
- Check regex patterns in `src/extractor.py`
- Test with sample files in `tests/extractor/`

### CSV Manager Issues
- Ensure `data/` directory is writable
- Check for CSV schema consistency
- Verify timestamp tracking is working

### Integration Issues
- Run individual agent tests first to isolate problems
- Check console output for specific validation failures
- Regenerate test data if files are corrupted

## Additional Documentation

- **Project Overview:** `README.md` (root)
- **Agent Slash Commands:** `.claude/commands/`
- **Phase Documentation:** `tests/analyst/phase_completion/`
- **Dashboard Guide:** `docs/analyst/DASHBOARD_USER_GUIDE.md`
- **Output Plots:** `outputs/analyst/plots/`

## Notes

- Tests use the fake database to avoid modifying production data
- Each agent can be tested independently
- Integration tests validate the complete workflow
- Generate fresh test data if you modify the database structure
