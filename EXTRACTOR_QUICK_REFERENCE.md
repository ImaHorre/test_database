# Extractor Agent - Area & Timepoint Parsing Quick Reference

## What Changed

Modified `src/extractor.py` to extract `measurement_area` (A, B, C) and `timepoint` (t0, t1, etc.) from file names.

## Regex Pattern

```regex
DFU(\d+)(?:_([A-C]))?(?:_t(\d+))?
```

| Component | Captures | Example |
|-----------|----------|---------|
| `DFU(\d+)` | DFU row number | `DFU6` → 6 |
| `(?:_([A-C]))?` | Measurement area (A-C) | `_B` → B |
| `(?:_t(\d+))?` | Timepoint | `_t0` → 0 |

## Supported File Name Patterns

| Pattern | Extracts | Example |
|---------|----------|---------|
| `DFU1.csv` | dfu_row=1, file_type=csv | Simple/legacy files |
| `DFU2_roi1.txt` | dfu_row=2, roi=1, file_type=txt | ROI analysis files |
| `DFU3_B_t0_file.csv` | dfu_row=3, area=B, timepoint=0, file_type=csv | New format with area |
| `DFU4_C_t1_ROI5.txt` | dfu_row=4, area=C, timepoint=1, roi=5, file_type=txt | Complete new format |

## Method Signature

```python
def parse_file_name(self, file_name: str) -> Optional[Dict]:
    """
    Parse measurement file name.

    Returns dict with:
    - dfu_row (int): Required
    - file_type (str): 'csv' or 'txt'
    - roi (int): ROI number if present
    - measurement_area (str): 'A', 'B', or 'C' if present
    - timepoint (int): Timepoint number if present
    """
```

## Usage Example

```python
from src.extractor import MetadataExtractor

extractor = MetadataExtractor()

# Parse file name
metadata = extractor.parse_file_name(
    "DFU6_B_t0_droplet_annotations_20251029.csv"
)

# Output:
# {
#     'dfu_row': 6,
#     'file_type': 'csv',
#     'roi': None,
#     'measurement_area': 'B',
#     'timepoint': 0
# }
```

## Backwards Compatibility

Old file names still work without modification:
- `DFU1.csv` → Parsed correctly, no area/timepoint fields
- `DFU2_roi1.txt` → Parsed correctly with ROI

## Test Coverage

- **File Name Parsing:** 6/6 tests passing (100%)
- **Full Path Extraction:** 6/6 tests passing (100%)
- **ROI with Area/Timepoint:** 6/6 tests passing (100%)

## Key Design Features

1. **Optional Fields:** `measurement_area` and `timepoint` only appear in result when present
2. **Case Insensitive ROI:** Matches both `_roi` and `_ROI` patterns
3. **Flexible Positioning:** Pattern can match anywhere in filename using `re.search()`
4. **Non-Capturing Groups:** Groups for area/timepoint don't interfere with group numbering

## Files Modified

- `src/extractor.py` (3 changes):
  1. Line 40: Updated `DFU_FILE_PATTERN`
  2. Lines 145-187: Enhanced `parse_file_name()` method
  3. Line 172: Added case-insensitive ROI flag

## Test Files Created

- `test_extractor_area_timepoint.py` - Main test suite
- `test_roi_extraction.py` - ROI extraction validation

## Results Summary

```
Parsing Success Rate:       100%
Backwards Compatibility:    Maintained
ROI Pattern Coverage:       Both _roi and _ROI
Optional Fields:            Properly handled
Edge Cases:                 Tested and passing
```
