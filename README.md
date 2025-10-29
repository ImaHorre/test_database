# Local OneDrive Database Scanner

Automated system for scanning locally synced OneDrive directories, extracting metadata from folder structures, and maintaining a CSV database of microfluidic device measurements.

## Project Overview

This tool scans structured OneDrive folder hierarchies (synced to local filesystem) containing microfluidic device test data and automatically extracts metadata to create a searchable database.

**Folder Structure (7-8 levels):**
```
W13_S1_R2/              # Device ID (Wafer_Shim_Replica)
  06102025/             # Bonding Date
    23102025/           # Testing Date (sometimes absent)
      NaCas_SO/         # Fluids: Aqueous_Oil (sometimes absent)
        5mlhr150mbar/   # Flow Parameters
          dfu_measure/  # Measurement Type
            DFU1_B_t0.csv    # Data Files (with area/timepoint)
          freq_analysis/
            DFU1_B_t0_ROI1.txt
```

## Features

- **Local filesystem scanning** - Works with OneDrive folders synced to your computer
- **Metadata extraction** - Parses folder names and file names for structured data
- **CSV database** - Maintains searchable database with all device measurements
- **Flexible parsing** - Handles old and new file naming conventions
- **Area/timepoint tracking** - Extracts measurement areas (A-C) and timepoints (t0, t1, etc.)
- **ROI support** - Tracks regions of interest for frequency analysis
- **Data quality tracking** - Flags parse quality and validation issues

## Architecture - Agent System

The system uses specialized agents that communicate to create a complete data pipeline:

### 1. Scanner Agent (`src/scanner.py`)
- Traverses local directory structure recursively
- Discovers CSV and TXT measurement files
- Tracks file metadata (paths, timestamps)

### 2. Extractor Agent (`src/extractor.py`)
- Parses folder names to extract metadata
- Handles flexible naming conventions (old/new formats)
- Extracts: device IDs, dates, fluids, flow parameters, areas, timepoints
- Validates data quality

### 3. CSV Manager Agent (`src/csv_manager.py`)
- Maintains single CSV database
- Performs incremental updates
- Handles data consistency and deduplication
- Creates automatic backups

## Setup

### 1. Install Dependencies

```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # macOS/Linux

# Install requirements
pip install -r requirements.txt
```

### 2. Configure Paths

The scanner works with locally synced OneDrive folders. Configure the path to scan in `main.py`:

```python
# Path to your locally synced OneDrive folder
LOCAL_ONEDRIVE_PATH = r"C:\Users\YourName\OneDrive\Product\test_database"
```

## Usage

### Full Scan

Scan local OneDrive folder, extract all metadata, and update database:

```bash
python main.py
```

This will:
1. Discover all measurement files in the specified directory
2. Extract metadata from folder structure and file names
3. Update CSV database with new/changed files
4. Generate summary report

### Output Files

**Database:**
- `data/database.csv` - Main CSV database with all metadata
- `data/test_database.csv` - Test database (for development)

**Reports:**
- `outputs/summary_report.txt` - Text summary of database contents

## CSV Database Schema

The database contains the following columns:

**Device Information:**
- `device_type`, `device_id`, `wafer`, `shim`, `replica`

**Temporal Data:**
- `bonding_date`, `testing_date`

**Experimental Conditions:**
- `aqueous_fluid`, `oil_fluid`
- `aqueous_flowrate`, `aqueous_flowrate_unit`
- `oil_pressure`, `oil_pressure_unit`

**Measurement Details:**
- `measurement_type` (dfu_measure or freq_analysis)
- `dfu_row`, `roi`
- `measurement_area` (A, B, or C)
- `timepoint` (0, 1, 2, etc.)
- `file_name`, `file_type`

**Droplet Measurements:**
- `droplet_size_mean`, `droplet_size_std`, `droplet_size_min`, `droplet_size_max`
- `droplet_count`

**Frequency Measurements:**
- `frequency_mean`, `frequency_min`, `frequency_max`, `frequency_count`

**Metadata:**
- `raw_path` - Original file path
- `scan_timestamp` - When file was last scanned
- `extraction_timestamp` - When metadata was extracted
- `parse_quality` - Quality of metadata extraction (complete/partial/incomplete)
- `validation_warning` - Any data quality warnings

## Development

### Running Tests

All test files are in the `tests/` directory:

```bash
# Generate test data
python tests\generate_fake_database.py

# Test scanner
python tests\test_scanner_local.py

# Test extractor
python tests\test_extractor_area_timepoint.py

# Test full pipeline
python tests\test_full_pipeline.py
```

See `tests/README.md` for detailed test documentation.

### Project Structure

```
test_database/
├── src/                     # Source code
│   ├── __init__.py
│   ├── scanner.py          # Local filesystem scanner
│   ├── extractor.py        # Metadata extractor
│   └── csv_manager.py      # CSV database manager
├── utils/                   # Utilities
│   └── __init__.py
├── data/                    # Database files
│   ├── database.csv
│   └── test_database.csv
├── outputs/                 # Reports and visualizations
├── tests/                   # Test suite
│   ├── README.md
│   ├── test_full_pipeline.py
│   ├── test_scanner_local.py
│   ├── test_extractor_area_timepoint.py
│   ├── test_roi_extraction.py
│   ├── test_csv_integration.py
│   └── generate_fake_database.py
├── fake_onedrive_database/  # Test data (generated)
├── .claude/                 # Claude Code configuration
├── main.py                  # Main entry point
├── requirements.txt         # Python dependencies
├── .env.template            # Environment template
├── .gitignore
├── CLAUDE.md               # Project context for Claude Code
├── project_outline_plan.md # Complete project specifications
└── README.md               # This file
```

## Data Flow

```
Local OneDrive Folder
        ↓
[Scanner Agent] - Discovers files
        ↓
[Extractor Agent] - Parses folder structure
        ↓
[CSV Manager Agent] - Updates database
        ↓
CSV Database → Analysis & Reports
```

## Device Types

Currently supports two device designs:

- **W13** - Device design W13 (all shims and replicas)
- **W14** - Device design W14 (all shims and replicas)

Device type is the primary comparison axis. Shim and replica numbers are tracked for defect analysis.

## File Naming Conventions

### Modern Format (with area/timepoint):
```
BBDD_TTDD_deviceid_flowparams_fluids_DFUx_area_timepoint_type_timestamp.csv

Example:
0610_2310_w13_s1_r2_5mlhr150mbar_nacasso_DFU1_B_t0_droplet_annotations_20251024_102722.csv
```

### Legacy Format (simple):
```
DFU1.csv
DFU2_roi1.txt
```

The extractor handles both formats gracefully, with optional area (`_B`, `_C`) and timepoint (`_t0`, `_t1`) fields.

## Update Strategy

**On-demand with timestamp tracking:**
- Database updates when scan is run
- Processes changed files since last scan
- No background processing
- Ensures data freshness only when needed

## Contributing

See `project_outline_plan.md` for complete project specifications and development phases.

See `CLAUDE.md` for guidance when working with Claude Code.

## License

Internal use - Peak Emulsions

## Support

For development questions, consult:
- `CLAUDE.md` - Project context and guidelines
- `project_outline_plan.md` - Complete specifications
- `tests/README.md` - Test suite documentation
