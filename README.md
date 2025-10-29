# OneDrive Database Scanner

Automated system for scanning SharePoint/OneDrive directories, extracting metadata from folder structures, and maintaining a CSV database of microfluidic device measurements.

## Project Overview

This tool scans a structured SharePoint folder hierarchy containing microfluidic device test data and automatically extracts metadata to create a searchable database.

**Folder Structure (7-8 levels):**
```
W13_S1_R2/              # Device ID (Wafer_Shim_Replica)
  06102025/             # Bonding Date
    23102025/           # Testing Date (sometimes absent)
      NaCas_SO/         # Fluids: Aqueous_Oil (sometimes absent)
        5mlhr150mbar/   # Flow Parameters
          dfu_measure/  # Measurement Type
            DFU1.csv    # Data Files
          freq_analysis/
            DFU1_roi1.txt
```

## Architecture - Agent System

The system uses specialized agents that communicate to create a complete data pipeline:

### 1. Scanner Agent (`agents/scanner.py`)
- Connects to SharePoint via Microsoft Graph API
- Traverses directory structure recursively
- Discovers CSV and TXT measurement files
- Tracks changes via timestamps

### 2. Extractor Agent (`agents/extractor.py`)
- Parses folder names to extract metadata
- Handles flexible naming conventions (old/new formats)
- Extracts: device IDs, dates, fluids, flow parameters
- Validates data quality

### 3. CSV Manager Agent (`agents/csv_manager.py`)
- Maintains single CSV database
- Performs incremental updates
- Tracks scan timestamps
- Handles data consistency

### 4. Analyst Agent (`agents/analyst.py`)
- Processes natural language queries
- Generates visualizations
- Compares device types (W13 vs W14)
- Creates summary reports

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure SharePoint Access

Follow the detailed guide in [SETUP_SHAREPOINT.md](SETUP_SHAREPOINT.md):

1. Register app in Azure AD
2. Get Client ID, Client Secret, Tenant ID
3. Grant API permissions (Sites.Read.All, Files.Read.All)
4. Get admin consent

### 3. Create Environment File

```bash
cp .env.template .env
```

Edit `.env` with your credentials:
```env
CLIENT_ID=your-client-id
CLIENT_SECRET=your-client-secret
TENANT_ID=your-tenant-id
SHAREPOINT_SITE_URL=https://peakemulsions.sharepoint.com/sites/Techteam
SHAREPOINT_ROOT_PATH=Shared Documents/Product/test_database
```

## Usage

### Full Scan

Scan SharePoint, extract all metadata, and update database:

```bash
python main.py scan
```

This will:
1. Discover all measurement files
2. Extract metadata from folder structure
3. Update CSV database
4. Generate summary reports and visualizations

### Incremental Update

Update database with only changed files since last scan:

```bash
python main.py update
```

### Query Database

Filter and search the database:

```bash
# Query by device type
python main.py query --device-type W13

# Query by flow parameters
python main.py query --device-type W13 --flowrate 5 --pressure 150

# Query specific conditions
python main.py query --flowrate 5
```

### Generate Reports

Create summary report without scanning:

```bash
python main.py report
```

## Output Files

### Database
- `data/database.csv` - Main CSV database with all metadata
- `data/last_scan.txt` - Timestamp of last scan

### Reports
- `outputs/summary_report.txt` - Text summary of database
- `outputs/device_comparison.png` - Device type comparison plots
- `outputs/flow_analysis_W13.png` - Flow parameter analysis per device type

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
- `file_name`, `file_type`

**Metadata:**
- `raw_path` - Original SharePoint path
- `scan_timestamp` - When file was last scanned
- `extraction_timestamp` - When metadata was extracted
- `parse_quality` - Quality of metadata extraction (complete/partial/incomplete)

## Development

### Testing Individual Agents

Each agent can be run independently for testing:

```bash
# Test Scanner
python -m agents.scanner

# Test Extractor
python -m agents.extractor

# Test CSV Manager
python -m agents.csv_manager

# Test Analyst
python -m agents.analyst
```

### Claude Code Agents

For development with Claude Code, specialized agent contexts are available:

- `/scanner` - Work on SharePoint scanning
- `/extractor` - Work on metadata extraction
- `/csv-manager` - Work on database management
- `/analyst` - Work on analysis and reporting

## Project Structure

```
test_database/
├── agents/                  # Agent modules
│   ├── __init__.py
│   ├── scanner.py          # SharePoint Scanner
│   ├── extractor.py        # Metadata Extractor
│   ├── csv_manager.py      # CSV Database Manager
│   └── analyst.py          # Data Analyst
├── utils/                   # Utilities
│   ├── __init__.py
│   └── auth.py             # SharePoint authentication
├── data/                    # Database and timestamps
│   ├── database.csv
│   └── last_scan.txt
├── outputs/                 # Reports and visualizations
├── .claude/                 # Claude Code configuration
│   └── commands/            # Agent slash commands
├── main.py                  # Main orchestration script
├── requirements.txt         # Python dependencies
├── .env.template            # Environment template
├── .gitignore
├── CLAUDE.md               # Project context for Claude Code
├── project_outline_plan.md # Complete project specifications
├── SETUP_SHAREPOINT.md     # SharePoint setup guide
└── README.md               # This file
```

## Data Flow

```
SharePoint/OneDrive
        ↓
[Scanner Agent] - Discovers files
        ↓
[Extractor Agent] - Parses folder structure
        ↓
[CSV Manager Agent] - Updates database
        ↓
[Analyst Agent] - Generates insights
        ↓
Reports & Visualizations
```

## Device Types

Currently supports two device designs:

- **W13** - Device design W13 (all shims and replicas)
- **W14** - Device design W14 (all shims and replicas)

Device type is the primary comparison axis. Shim and replica numbers are tracked for defect analysis but not primary comparison.

## Update Strategy

**On-demand with timestamp tracking:**
- Database updates when explicitly requested
- Timestamp tracking optimizes scanning
- Incremental updates only process changed files
- No background processing

## Contributing

See `project_outline_plan.md` for complete project specifications and development phases.

## License

Internal use - Peak Emulsions

## Support

For issues or questions, consult:
- `CLAUDE.md` - Project context and guidelines
- `project_outline_plan.md` - Complete specifications
- `SETUP_SHAREPOINT.md` - SharePoint setup help
