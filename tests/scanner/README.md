# Scanner Agent Tests

This directory contains tests and utilities for the **Scanner Agent**, which is responsible for traversing the OneDrive directory structure and identifying all relevant files for processing.

## Agent Responsibility

The Scanner Agent:
- Traverses local OneDrive folder structure (no API authentication required)
- Identifies measurement files (CSV and TXT formats)
- Extracts directory hierarchy metadata
- Tracks last scan timestamp for incremental updates

## Files in this Directory

### Test Files
- **test_scanner_local.py** - Core scanner functionality tests
  - Tests directory traversal
  - Validates file identification
  - Checks metadata extraction from folder structure

### Utilities
- **generate_fake_database.py** - Test data generator
  - Creates realistic fake OneDrive folder structure
  - Generates sample CSV and TXT files
  - Used for testing without accessing real data

## Running Scanner Tests

```bash
# Activate virtual environment
.venv\Scripts\activate

# Run scanner tests
python tests\scanner\test_scanner_local.py
```

## Related Components

- **Source Code:** `src/scanner.py`
- **Slash Command:** `.claude/commands/scanner.md`
- **Dependencies:** Uses Python's `pathlib` for filesystem operations

## Notes

- Scanner works on locally synced OneDrive folders only
- No cloud API authentication needed
- Supports incremental scanning via timestamp tracking
