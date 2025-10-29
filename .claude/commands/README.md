# Agent Slash Commands

This directory contains specialized agent configurations for the OneDrive File System Scanner & Analysis Tool.

## Available Agents

### `/scanner` - OneDrive Scanner Agent
**Purpose:** Connect to OneDrive and traverse directory structures

**Use when:**
- Setting up OneDrive authentication
- Implementing directory traversal logic
- Building change detection system
- Working on file discovery and inventory

**Key capabilities:**
- Dual access (local folders + Online via Office 365 API)
- Timestamp-based change detection
- Handles 7-8 level folder hierarchy
- Error handling for network/permissions

---

### `/extractor` - Metadata Extractor Agent
**Purpose:** Parse folder/file names to extract structured data

**Use when:**
- Designing parsing logic for folder hierarchy
- Extracting device IDs, dates, fluids, flow parameters
- Handling old vs new naming conventions
- Reading measurement data from CSV/TXT files

**Key capabilities:**
- Flexible regex-based parsing
- Handles missing folder levels
- Date format standardization
- Validation and error flagging

---

### `/csv-manager` - CSV Manager Agent
**Purpose:** Design and maintain the CSV database

**Use when:**
- Designing CSV schema
- Implementing data population logic
- Building incremental update system
- Managing timestamps and versioning

**Key capabilities:**
- Schema design for measurement data
- Incremental updates (only modified records)
- Data consistency validation
- On-demand update workflow

---

### `/analyst` - Analysis & Reporting Agent
**Purpose:** Process queries, analyze data, generate visualizations

**Use when:**
- Building query processing logic
- Creating visualization and plotting code
- Generating reports and insights
- Developing interactive guidance system

**Key capabilities:**
- Natural language query interpretation
- Device comparison analysis (W13 vs W14)
- Dynamic plotting method generation
- Interactive clarifying questions
- Reusable plotting library management

---

## How to Use Agents

### Invoke an agent:
```
/scanner
/extractor
/csv-manager
/analyst
```

### When to use which agent:

**Starting development?** Use `/scanner` or `/csv-manager` to begin with foundational components

**Working on data parsing?** Use `/extractor`

**Building analysis features?** Use `/analyst`

**Multi-agent tasks?** Invoke agents sequentially as needed, they're designed to work together

## Agent Integration

Agents are designed to work in sequence:

```
OneDrive Data
     ↓
[/scanner] - Discovers files and folders
     ↓
[/extractor] - Parses and extracts structured data
     ↓
[/csv-manager] - Stores data in CSV database
     ↓
[/analyst] - Answers user queries and generates insights
```

## Important Notes

- Each agent has specific responsibilities - consult their individual docs for details
- Agents reference `project_outline_plan.md` and `CLAUDE.md` for current requirements
- All agents account for flexible folder structure (some levels may be absent)
- Agents are designed for small dataset - prioritize clarity over performance

## Living Documents

These agent configurations are living documents. Update them as:
- Requirements evolve
- New features are added
- Edge cases are discovered
- Technology stack decisions are finalized

## Next Steps

1. Choose technology stack (Python vs Node.js)
2. Begin development with `/scanner` or `/csv-manager`
3. Build incrementally, testing each agent's functionality
4. Integrate agents into complete workflow
5. Test with real OneDrive data

For overall project context, always refer to:
- `project_outline_plan.md` - Complete project specifications
- `CLAUDE.md` - Development guidelines and context
