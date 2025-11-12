# Integration Tests

This directory contains integration tests that verify the **full pipeline** works correctly end-to-end.

## Purpose

Integration tests validate that all agents work together seamlessly:
- Scanner → Extractor → CSV Manager → Analyst

These tests ensure:
- Data flows correctly between components
- Each agent's output is compatible with the next
- The complete workflow produces expected results
- Edge cases are handled gracefully across the pipeline

## Files in this Directory

### Test Files
- **test_full_pipeline.py** - Complete pipeline integration test
  - Tests full data flow from OneDrive scan to analysis
  - Validates all agent interactions
  - Checks end-to-end data consistency
  - Generates test report with validation results

## Running Integration Tests

```bash
# Activate virtual environment
.venv\Scripts\activate

# Run full pipeline test
python tests\integration\test_full_pipeline.py
```

The test will:
1. Scan the fake OneDrive database
2. Extract metadata from files and folders
3. Update the CSV database
4. Verify data consistency
5. Generate a summary report

## Pipeline Flow

```
┌──────────────┐
│   Scanner    │  Identifies files and folder structure
└──────┬───────┘
       │
       v
┌──────────────┐
│  Extractor   │  Parses filenames and extracts metadata
└──────┬───────┘
       │
       v
┌──────────────┐
│ CSV Manager  │  Updates database with extracted data
└──────┬───────┘
       │
       v
┌──────────────┐
│   Analyst    │  Processes queries and generates reports
└──────────────┘
```

## Test Environment

Integration tests use:
- **Test Data:** `fake_onedrive_database/` directory
- **Test Database:** Temporary CSV file (cleaned up after test)
- **Test Output:** `outputs/` directory for plots and reports

## Related Components

- **Individual Agent Tests:**
  - `tests/scanner/` - Scanner-specific tests
  - `tests/extractor/` - Extractor-specific tests
  - `tests/csv_manager/` - CSV Manager-specific tests
  - `tests/analyst/` - Analyst-specific tests

- **Main Application:** `main.py` (root directory)

## Notes

- Run integration tests after making changes to any agent
- Integration tests catch issues that unit tests might miss
- These tests validate the complete user workflow
- Keep test data realistic to catch real-world edge cases
