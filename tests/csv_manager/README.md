# CSV Manager Agent Tests

This directory contains tests for the **CSV Manager Agent**, which maintains the database and handles incremental updates.

## Agent Responsibility

The CSV Manager Agent:
- Maintains the master CSV database (`data/database.csv`)
- Handles incremental updates (only processes changed files)
- Manages timestamp tracking for efficient scanning
- Ensures data consistency and integrity
- Never directly viewed by users - accessed via AI queries only

## Files in this Directory

### Test Files
- **test_csv_integration.py** - CSV database integration tests
  - Tests database initialization
  - Validates incremental update logic
  - Checks data consistency
  - Tests timestamp tracking
  - Validates CSV schema compliance

## Running CSV Manager Tests

```bash
# Activate virtual environment
.venv\Scripts\activate

# Run CSV integration tests
python tests\csv_manager\test_csv_integration.py
```

## CSV Database Schema

The database captures:
- **Device Information:** Device ID, Wafer, Shim, Replica
- **Dates:** Bonding Date, Testing Date
- **Experimental Conditions:** Fluids, Flow Rate, Pressure
- **Measurements:** DFU row, Area suffix, Timepoint
- **Data:** Droplet sizes, Frequency analysis results
- **Metadata:** File paths, Last modified timestamps

## Update Strategy

The CSV Manager uses an **on-demand update** approach:
1. User makes a query
2. Scanner checks for changes since last scan
3. CSV Manager updates only modified/new entries
4. Analysis Agent processes the query
5. Returns results to user

This ensures data freshness only when needed, avoiding unnecessary background processing.

## Related Components

- **Source Code:** `src/csv_manager.py`
- **Slash Command:** `.claude/commands/csv-manager.md`
- **Database Location:** `data/database.csv`
- **Timestamp Tracking:** `data/last_scan.txt`
- **Dependencies:** `pandas` for CSV operations

## Notes

- Database is never directly viewed by users
- All access through AI-assisted queries
- Small file volume makes full scans efficient
- Timestamp tracking optimizes repeated scans
- Consider SQLite as parallel query layer in future
