# Parsing Failure Point Analysis

## The Problem: 407 Files (44.3%) Failing to Extract Metadata

### Example Failed File Path
```
5mlhr250mbar/dfu_measure/0610_2310_W13_S1_R2_5mlhr250mbar_NaCasSO_DFU1_B_t5_droplet_annotations_20251024_143119.csv
```

### What's Missing?
- **device_id**: Missing
- **bonding_date**: Missing
- **testing_date**: Missing
- **fluids**: Missing (partially - NaCasSO in filename but not extracted)
- **aqueous_flowrate/oil_pressure**: Missing

## Step-by-Step: How Current Parsing Works

### Current Code Flow in `extractor.py`

The `extract_from_path()` method (lines 515-653) processes paths using folder hierarchy:

```python
def extract_from_path(self, file_path: str, local_path: Optional[str] = None) -> Dict:
    parts = file_path.split('/')
    metadata = {'raw_path': file_path, 'path_parts': parts}

    # Step 1: Parse folder hierarchy levels
    if len(parts) >= 1:
        device_data = self.parse_device_id(parts[0])  # EXPECTS: W13_S1_R2

    if len(parts) >= 2:
        bonding_date = self.parse_date(parts[1])      # EXPECTS: 06102025 or 0610

    if len(parts) >= 3:
        testing_date = self.parse_date(parts[2])      # EXPECTS: 23102025 or 2310

    # Step 2: Parse remaining parts (fluids, flow, measurement type)
    for part in remaining_parts:
        if part in ['dfu_measure', 'freq_analysis']:
            metadata['measurement_type'] = part

        fluid_data = self.parse_fluids(part)          # EXPECTS: SDS_SO, NaCas_SO
        flow_data = self.parse_flow_parameters(part)  # EXPECTS: 5mlhr150mbar

    # Step 3: Parse filename (only for DFU row, area, timepoint)
    if last_part_is_file:
        file_data = self.parse_file_name(part)        # Extracts: DFU1, _B, _t5
```

### Why the Example File Fails

**Path breakdown:**
```
parts[0] = "5mlhr250mbar"        ← Flow parameters, NOT device ID!
parts[1] = "dfu_measure"          ← Measurement type, NOT bonding date!
parts[2] = "0610_2310_W13_S1_R2_5mlhr250mbar_NaCasSO_DFU1_B_t5_droplet_annotations_20251024_143119.csv"
```

**What happens at each step:**

1. **Line 535: Parse device_id from parts[0]**
   ```python
   device_data = self.parse_device_id("5mlhr250mbar")
   # FAILS: "5mlhr250mbar" doesn't match pattern "W\d+_S\d+_R\d+"
   # Returns: None
   # Result: device_id remains MISSING
   ```

2. **Line 540: Parse bonding_date from parts[1]**
   ```python
   bonding_date = self.parse_date("dfu_measure")
   # FAILS: "dfu_measure" doesn't match date patterns
   # Returns: None
   # Result: bonding_date remains MISSING
   ```

3. **Line 552: Try to parse testing_date from parts[2]**
   ```python
   testing_date = self.parse_date("0610_2310_W13_S1_R2_5mlhr250mbar_NaCasSO_DFU1_B_t5_droplet_annotations_20251024_143119.csv")
   # FAILS: Filename doesn't match date patterns
   # Returns: None
   ```

4. **Lines 571-597: Parse remaining parts**
   - The code finds "dfu_measure" as measurement_type (✓)
   - But it never looks at the filename for device_id, dates, or fluids

5. **Lines 599-604: Parse filename**
   ```python
   file_data = self.parse_file_name(filename)
   # ONLY extracts: DFU row (1), area (B), timepoint (5)
   # DOES NOT extract: device_id, bonding_date, testing_date, fluids, flow params
   ```

### The Core Problem

**The extractor assumes metadata comes from folder hierarchy, NOT filenames.**

When files are organized like this:
```
flowparams/measurement_type/detailed_filename.csv
```

Instead of the expected:
```
device_id/bonding_date/testing_date/fluids/flowparams/measurement_type/simple_filename.csv
```

All the metadata extraction fails because:
- `parse_device_id()` looks at parts[0] (expects "W13_S1_R2", gets "5mlhr250mbar")
- `parse_date()` looks at parts[1] (expects "0610", gets "dfu_measure")
- `parse_fluids()` looks at remaining parts (expects folder names, not embedded in filename)

### Why 407 Files Fail

These files all follow the pattern:
```
<flow_params>/<measurement_type>/<BBDD_TTDD_DeviceID_FlowParams_Fluids_DFUx_Area_Timepoint_type_timestamp.ext>
```

The folder hierarchy is shallow (2 levels), and ALL metadata is embedded in the filename itself.

## The Solution: Filename Fallback Extraction

We need to:
1. Keep the existing folder hierarchy parsing (works for 510 files)
2. Add NEW logic to extract from filenames when hierarchy parsing fails
3. Use filename extraction as a fallback when core fields are missing

### Pattern in Failing Files

Filename structure:
```
0610_2310_W13_S1_R2_5mlhr250mbar_NaCasSO_DFU1_B_t5_droplet_annotations_20251024_143119.csv
│    │    │          │              │       │   │  │
│    │    │          │              │       │   │  └─ Timepoint
│    │    │          │              │       │   └──── Measurement area
│    │    │          │              │       └──────── DFU row
│    │    │          │              └──────────────── Fluids
│    │    │          └─────────────────────────────── Flow parameters
│    │    └────────────────────────────────────────── Device ID
│    └─────────────────────────────────────────────── Testing date (DDMM)
└──────────────────────────────────────────────────── Bonding date (DDMM)
```

### What We'll Extract from Filenames

1. **Bonding date**: `^\d{4}` (first 4 digits: BBDD)
2. **Testing date**: `^\d{4}_(\d{4})` (second 4 digits after underscore: TTDD)
3. **Device ID**: `W\d+_S\d+_R\d+` (W13_S1_R2 pattern)
4. **Fluids**: `(?:SDS|NaCas)[_+]?SO` (SDS_SO, NaCasSO, NaCas_SO patterns)
5. **Flow parameters**: `\d+mlhr\d+mbar` (5mlhr250mbar pattern)

### Implementation Strategy

Add new method:
```python
def extract_from_filename(self, file_name: str) -> Dict:
    """Fallback: extract metadata from filename when folder hierarchy fails"""
```

Modify `extract_from_path()` to:
```python
# After folder hierarchy extraction
if not metadata.get('device_id'):
    # Try filename extraction
    filename_metadata = self.extract_from_filename(file_name)
    if filename_metadata:
        metadata.update(filename_metadata)
        metadata['extracted_from_filename'] = True
```

This way:
- Files with proper folder hierarchy still work (primary method)
- Files with shallow hierarchy fall back to filename extraction
- We track which method was used for quality assessment
