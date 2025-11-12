# Local OneDrive Database Scanner & Analysis Tool - Project Outline

## Project Overview
A comprehensive application to scan locally synced OneDrive directories, extract metadata from directory structures, maintain an up-to-date CSV database, and provide AI-assisted analysis, reporting, and data retrieval capabilities.

## Core Objectives
1. Scan and index locally synced OneDrive directory structures
2. Extract data from file names and folder hierarchies
3. Maintain a dynamic, auto-updating CSV database
4. Enable AI-assisted search, analysis, and reporting
5. Handle varying file naming conventions (legacy vs. modern)
6. Support folder-based data organization for older files

## System Architecture

### Phase 1: Data Extraction & Indexing
**Components:**
- Local filesystem scanner
- Metadata extraction engine
- File naming pattern recognition
- Folder hierarchy parser

### Phase 2: Data Storage & Management
**Components:**
- CSV database structure design
- Update mechanism (periodic/on-access/on-demand)
- Version control for data changes
- Data validation and integrity checks

### Phase 3: AI-Assisted Interface
**Components:**
- Claude Code integration for natural language queries
- Multi-LLM support: ChatGPT, Gemini, and other free LLMs (for additional tokens and team collaboration)
- Report generation system
- Data analysis engine
- Visualization/plotting capabilities

## Proposed Agents

### 1. **Local Scanner Agent**
- **Purpose:** Handle local filesystem traversal and data discovery
- **Responsibilities:**
  - Scan locally synced OneDrive directories
  - Traverse directory structures recursively
  - Extract file/folder metadata
  - Track file timestamps and changes

### 2. **Metadata Extractor Agent**
- **Purpose:** Parse file names and folder structures to extract embedded data
- **Responsibilities:**
  - Identify naming patterns (old vs. new formats)
  - Extract structured data from file names
  - Parse folder hierarchy for organizational data
  - Handle edge cases and malformed names

### 3. **CSV Manager Agent**
- **Purpose:** Maintain and update the CSV database
- **Responsibilities:**
  - Design optimal CSV schema
  - Handle incremental updates
  - Detect changes (new/modified/deleted files)
  - Ensure data consistency
  - Implement update triggers (time-based, event-based)

### 4. **Analysis & Reporting Agent**
- **Purpose:** Process natural language queries and generate insights
- **Responsibilities:**
  - Interpret user queries about the data
  - Search and filter CSV data
  - Generate reports and summaries
  - Create visualizations and plots
  - Identify patterns and anomalies

### 5. **Data Validation Agent**
- **Purpose:** Ensure data quality and consistency
- **Responsibilities:**
  - Validate extracted data
  - Flag inconsistencies or errors
  - Suggest corrections for malformed data
  - Monitor data quality metrics

## Technical Stack

### Backend
- **Python:** Selected for data processing, CSV handling, and filesystem operations
  - Libraries: `pandas`, `pathlib`, `csv`
  - No external APIs required - local filesystem only

### Data Storage
- **Primary:** CSV file (as specified)
- **Consideration:** SQLite for complex queries (parallel database)

### AI Integration
- Claude API for natural language processing and interactive queries via Claude Code
- ChatGPT/Gemini support for additional token capacity and team collaboration
- Multi-LLM architecture for flexibility and cost optimization

### Automation
- Scheduled tasks (cron jobs, Windows Task Scheduler)
- File system watchers
- Event-driven updates

## Update Mechanisms

### Option 1: Periodic Scanning
- Schedule regular scans (hourly, daily, weekly)
- Background process updates CSV
- **Pros:** Simple, reliable
- **Cons:** May have stale data between scans

### Option 2: On-Access Check
- Check for updates when CSV is opened/accessed
- **Pros:** Always current when needed
- **Cons:** Potential delay when opening

### Option 3: Real-time Monitoring
- Watch OneDrive folder for changes
- Update CSV immediately
- **Pros:** Always current
- **Cons:** More complex, resource-intensive

### Recommended Approach
**On-demand trigger with timestamp tracking:**
- Update CSV only when actively being queried
- Workflow: User makes prompt → Run update scan → Return prompt answer
- Maintains timestamps to track last update and optimize scanning
- **Pros:** Ensures data is always current when needed, no wasted background processing
- **Cons:** Small delay on first query after changes (acceptable trade-off)

## Data Flow

```
Local OneDrive Directory (Synced)
        ↓
[Local Scanner Agent]
        ↓
[Metadata Extractor Agent]
        ↓
[CSV Manager Agent]
        ↓
    CSV Database
        ↓
[Analysis & Reporting Agent]
        ↓
Reports, Queries, Visualizations
```

## Implementation Phases

### Phase 1: Foundation
- [x] Document folder structure and naming conventions
- [x] Design CSV schema based on data layers
- [x] Create local filesystem scanner
- [x] Implement basic metadata extraction

### Phase 2: Core Functionality
- [x] Implement metadata extraction logic
- [x] Build CSV population system
- [x] Create update mechanism
- [x] Handle edge cases (old vs. new naming)

### Phase 3: Intelligence Layer
- [ ] Integrate Claude Code for queries
- [ ] Build report generation templates
- [ ] Implement data analysis functions
- [ ] Add visualization capabilities

### Phase 4: Optimization & Polish
- [ ] Performance tuning
- [ ] Error handling and logging
- [ ] Documentation
- [ ] Testing and validation

## Next Steps

1. **Await folder structure documentation** - User will provide details about:
   - Directory hierarchy layers
   - Data available at each layer
   - File naming conventions (old and new formats)
   - Examples of embedded data in names/paths

2. **Design CSV schema** - Once folder structure is known

3. **Select technology stack** - Based on requirements and preferences

4. **Begin agent development** - Can proceed with OneDrive integration in parallel

## Directory Structure & Data Organization

### Folder Hierarchy (in order):
1. **Device ID** - Format: `W13_S1_R4` (Wafer number, Shim number, Replica number)
2. **Bonding Date** - Format: `25092025` or `2509`
3. **Testing Date** - Format: `25092025` or `2509` (may be absent, proceeding directly to next folder)
4. **Fluids** - Format: `SDS_SO` or `NaCas_SO` (aqueous and oil fluids, not always present)
5. **Flow Parameters** - Format: `5mlhr500mbar` (aqueous flowrate and oil pressure)
6. **Measurement Folders:**
   - `dfu_measure/` - Contains CSV files for each DFU row (DFU1, DFU2, DFU3, etc.) with droplet size measurements
   - `freq_analysis/` - Contains TXT files with droplet frequency data per ROI (e.g., `DFU1_roi1.txt`, `DFU1_roi2.txt`)

**Note:** Analysis script in another repo will be updated to consolidate all frequency data for each DFU row into single files (TXT or CSV format), matching the `dfu_measure` structure.

### Directory Depth
**Answer:** 7-8 levels deep (Device ID → Bonding Date → Testing Date → Fluids → Flow Parameters → Measurement Type → Data Files)

### File Volume
**Answer:** Currently small scale. Each branch terminates with a few TXT and CSV files containing measurement data to be extracted.

## Analysis Requirements & Priorities

### Device Types
- **Two device designs:** W13 and W14
- All W13 devices (regardless of shim/replica) can be compared against each other
- All W14 devices (regardless of shim/replica) can be compared against each other
- Shim and replica numbers stored for potential defect tracking but not primary comparison criteria

### Priority Analysis Types

**1. Flow Parameter Comparison (Same Device Type):**
- Compare various flow parameters for W13 or W14 devices
- Interactive LLM guidance: "Do you want to see separate plots for every parameter tested >2 times on the same device type?"
- Device-specific highlighting: "Do you want to highlight the same device ID (e.g., W13_S1_R1) with the same color to compare individual device performance across test dates?"

**2. Cross-Device Comparison:**
- Compare all devices (W13 or W14) tested at the same parameters
- Export filtered results based on matching parameters

**3. Dynamic Plotting Methods:**
- LLM can ask clarifying questions about visualization preferences
- Generate new plotting methods on-the-fly (create new versions of plotting methods `.py` files)
- Store successful plotting configurations for future reuse
- Build library of plotting approaches over time

### OneDrive Access Requirements
**Local filesystem only:**
- Scans locally synced OneDrive folders
- Works on any PC with OneDrive sync enabled
- No API authentication required

### Historical Tracking
**Status:** To be determined based on use case development

## Open Questions Remaining
- Final decision on consolidated frequency data format (TXT vs CSV)
- Historical tracking requirements (version control of changes vs. snapshots only)
- Additional device types beyond W13/W14 expected?

## Notes

- File naming may vary between old and new formats - need flexible parsing
- Folder structure itself may contain organizational data for older files
- CSV should be machine-readable but not directly viewed by users
- Primary interface will be AI-assisted queries via Claude Code
