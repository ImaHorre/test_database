# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project: OneDrive File System Scanner & Analysis Tool

This is a data management application designed to scan OneDrive directory structures, extract metadata from file/folder names and hierarchies, maintain a CSV database, and provide AI-assisted querying and analysis capabilities.

**Current Status:** Requirements gathering complete. Folder structure documented. Ready to begin agent development. Technology stack selection in progress.

## Project Context

See `project_outline_plan.md` for complete architectural planning and implementation phases.

### Core Purpose
- Scan OneDrive file systems and extract embedded metadata
- Maintain auto-updating CSV database (never directly viewed by users)
- Enable natural language queries via Claude Code for reports and analysis
- Handle evolving file naming conventions (legacy and modern formats)
- Use folder hierarchy itself as organizational metadata for older files

### Planned Architecture Components

The system will be organized into specialized agents:

1. **OneDrive Scanner** - Authentication, file system traversal, metadata collection
2. **Metadata Extractor** - Parse file/folder names to extract structured data
3. **CSV Manager** - Maintain database, handle incremental updates, detect changes
4. **Analysis & Reporting** - Process natural language queries, generate visualizations
5. **Data Validation** - Ensure consistency and flag anomalies

### Data Flow
```
OneDrive → Scanner → Extractor → CSV Manager → CSV Database → Analysis Agent → User Reports
```

## OneDrive Folder Structure

The application scans a 7-8 level deep directory hierarchy with the following structure:

1. **Device ID**: `W13_S1_R4` (Wafer_Shim_Replica)
   - Two device types: W13 and W14
   - Comparison primarily by device type (W13 vs W14), but shim/replica tracked for defect analysis
2. **Bonding Date**: `25092025` or `2509`
3. **Testing Date**: `25092025` or `2509` (sometimes absent)
4. **Fluids**: `SDS_SO`, `NaCas_SO` (aqueous_oil, not always present)
5. **Flow Parameters**: `5mlhr500mbar` (aqueous_flowrate + oil_pressure)
6. **Measurement Folders**:
   - `dfu_measure/` → CSV files per DFU row (DFU1, DFU2, etc.) with droplet sizes
   - `freq_analysis/` → TXT files per ROI (DFU1_roi1.txt, DFU1_roi2.txt, etc.)

**Note:** Frequency analysis files will be consolidated to one file per DFU row (matching dfu_measure structure) by updates to external analysis script.

## Critical Design Considerations

### File Naming Flexibility
- Newer files may have more data embedded in naming structure
- Older files may rely on folder organization for metadata
- Parsing logic must handle both patterns gracefully
- User acknowledges file names may have inconsistencies

### Update Strategy
- **On-demand only**: Update CSV when user makes a query
- Workflow: User prompt → Run scan → Update CSV → Return answer
- Timestamp tracking to optimize scanning (check what changed since last update)
- No background processing - ensures data freshness only when needed

### CSV Database
- Primary data store (consideration for SQLite as parallel query layer)
- Schema will capture: Device ID, Wafer, Shim, Replica, Bonding Date, Testing Date, Fluids, Flow Parameters, DFU measurements, Frequency data
- Not for direct human viewing - accessed via AI queries only
- Small file volume (few TXT/CSV files per branch) makes processing efficient

### OneDrive Access Requirements
- **Must support both access methods:**
  - Local synced folders (lab PC)
  - OneDrive Online via Office 365 API (home PC without local sync)
- Microsoft Graph API will be needed for online access

### AI Integration Strategy
- **Primary:** Claude Code for interactive queries and analysis
- **Secondary:** ChatGPT, Gemini, and other LLMs for:
  - Additional token capacity
  - Team collaboration (different team members may have different subscriptions)
  - Cost optimization
- Multi-LLM architecture for flexibility

## Analysis Priorities & Use Cases

### Device Comparison
- Compare flow parameters within device types (all W13 devices vs all W14 devices)
- Device type (W13/W14) is primary comparison axis
- Shim and replica tracked but not primary comparison criteria (except for defect tracking)

### Interactive Plotting with LLM Guidance
- LLM should ask clarifying questions: "Do you want separate plots for parameters tested >2 times on the same device type?"
- Device-specific highlighting: "Do you want to highlight the same device ID (e.g., W13_S1_R1) in the same color across test dates?"
- **Dynamic method generation:** LLM can create new plotting methods on-the-fly, save them as `.py` files, and reuse in future
- Build a library of proven plotting approaches over time

### Priority Query Types
1. Compare all W13 (or W14) devices at specific flow parameters
2. Track individual device performance over multiple test dates
3. Identify patterns across fluid types
4. Analyze DFU row performance metrics

## Technology Stack (TBD)

Likely candidates:
- **Python:** Strong for data processing (`pandas`, OneDrive SDK, `schedule`)
- **Node.js:** Alternative for Microsoft Graph API integration

Decision pending user requirements and folder structure complexity.

## Development Workflow (To Be Established)

Once technology stack is chosen, this section will include:
- Setup and installation commands
- How to run the scanner
- How to update the CSV
- How to query the data
- Testing procedures

## Next Steps for Development

1. **Awaiting Input:** User will provide OneDrive folder structure details including:
   - Directory hierarchy layers and depth
   - Data embedded at each layer
   - Examples of old vs. new file naming patterns
   - Volume of files to process

2. **Schema Design:** Create CSV structure based on folder documentation

3. **Stack Selection:** Choose Python vs. Node.js based on requirements

4. **Agent Development:** Begin implementing core components per project outline

## Important Notes for Future Claude Instances

- **Folder structure is documented** - see "OneDrive Folder Structure" section above
- **Flexible parsing is critical** - file naming conventions vary over time, some levels may be absent
- **User prefers AI interaction** - build for natural language queries, not manual CSV inspection
- **Windows environment** - consider platform-specific commands and file paths
- **No git repository yet** - initialize when appropriate during development
- **Dynamic plotting library** - save successful plotting methods for reuse
- **Small file volume** - optimize for clarity over performance
- **External analysis script** - frequency data format standardization happening in separate repo

## Living Documents

Both `project_outline_plan.md` and `CLAUDE.md` are living documents:
- Consult them frequently during development
- Update them as requirements evolve or decisions are made
- Both user and Claude have freedom to make edits
- Keep information synchronized between both files

## Global Instructions (Always Reference These)

**IMPORTANT:** At the start of every session, read these global files from AppData:

1. **Git Workflow Template**
   - Location: `C:\Users\conor\AppData\Roaming\Claude\templates\git_workflow.md`
   - Contains: Commit reminders, branch management, commit message guidelines
   - **To update:** Edit this file directly, changes apply to all projects immediately
   - Use `/git-help` command to view current git workflow instructions

2. **Custom Instructions** (project-specific, like microfluidic analysis)
   - Location: `C:\Users\conor\AppData\Roaming\Claude\custom_instructions.md`
   - Contains: Plotting standards, data analysis standards (specific to other projects)
   - Not all instructions apply to this project - focus on git workflow

### Git Workflow Summary
- **Commit reminders:** After 3+ file changes, completed tasks, before major switches, every 30-40 min
- **Commit format:** `[type] [description]` where type = Add/Fix/Update/Refactor/Docs/Test
- **Branch management:** Suggest new branches for features, experiments, major refactors, complex fixes
- **Proactive git status checks** when user asks about changes or before major features

### When User Wants to Change Git Workflow

**Simple text commands (no slash needed):**
- User says: `"update global git workflow: [instruction]"`
- Claude edits: `C:\Users\conor\AppData\Roaming\Claude\templates\git_workflow.md`
- User says: `"show me the global git workflow"`
- Claude displays current template

**Examples:**
- "update global git workflow: add reminder about .env files"
- "update global git workflow: change commit frequency to 20 minutes"

Changes apply to ALL projects immediately (global file is source of truth)
