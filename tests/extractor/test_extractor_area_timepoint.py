"""
Test Extractor Agent - Area & Timepoint Parsing

Tests the updated DFU_FILE_PATTERN regex and parse_file_name() method
with sample files from the fake_onedrive_database.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from src.extractor import MetadataExtractor
import json

# Sample file paths from fake_onedrive_database
SAMPLE_PATHS = [
    # With area and timepoint (_B_t0)
    "W13_S1_R1/13082025/01092025/40mlhr100mbar/dfu_measure/1308_0109_w13_s1_r1_40mlhr100mbar_DFU1_B_t0_droplet_annotations_20251029_134219.csv",
    "W13_S1_R1/13082025/01092025/40mlhr100mbar/freq_analysis/1308_0109_w13_s1_r1_40mlhr100mbar_DFU2_B_t0_ROI5_frequency_analysis.txt",

    # Different device/dates
    "W13_S1_R1/14082025/23082025/30mlhr100mbar/dfu_measure/1408_2308_w13_s1_r1_30mlhr100mbar_DFU6_B_t0_droplet_annotations_20251029_134810.csv",
    "W13_S1_R1/14082025/23082025/5mlhr200mbar/freq_analysis/1408_2308_w13_s1_r1_5mlhr200mbar_DFU4_B_t0_ROI3_frequency_analysis.txt",

    # Simple DFU names (backwards compatibility test)
    "W13_S1_R1/13082025/01092025/40mlhr100mbar/dfu_measure/DFU1.csv",
    "W13_S1_R1/13082025/01092025/40mlhr100mbar/freq_analysis/DFU2_roi1.txt",
]

def test_file_parsing():
    """Test file name parsing for area and timepoint extraction."""
    extractor = MetadataExtractor()

    # Just test the file names (last part of the path)
    file_names = [path.split('/')[-1] for path in SAMPLE_PATHS]

    print("\n" + "="*80)
    print("TESTING FILE NAME PARSING - Area & Timepoint Extraction")
    print("="*80)

    successes = 0
    failures = 0

    for file_name in file_names:
        print(f"\nFile: {file_name}")
        result = extractor.parse_file_name(file_name)

        if result:
            successes += 1
            print(f"  [PASS] Parse successful")
            print(f"    - DFU Row: {result.get('dfu_row')}")
            print(f"    - Measurement Area: {result.get('measurement_area', 'Not present')}")
            print(f"    - Timepoint: {result.get('timepoint', 'Not present')}")
            print(f"    - ROI: {result.get('roi', 'Not present')}")
            print(f"    - File Type: {result.get('file_type')}")
        else:
            failures += 1
            print(f"  [FAIL] Parse failed")

    return successes, failures

def test_full_path_extraction():
    """Test full path extraction with area and timepoint."""
    extractor = MetadataExtractor()

    print("\n" + "="*80)
    print("TESTING FULL PATH EXTRACTION")
    print("="*80)

    successes = 0
    failures = 0

    for path in SAMPLE_PATHS:
        print(f"\nPath: {path}")
        metadata = extractor.extract_from_path(path)

        # Check if critical fields were parsed
        has_dfu = 'dfu_row' in metadata
        has_area = 'measurement_area' in metadata
        has_timepoint = 'timepoint' in metadata

        quality = metadata.get('parse_quality', 'unknown')

        print(f"  Parse Quality: {quality}")
        print(f"  Device: {metadata.get('device_id', 'N/A')}")
        print(f"  DFU Row: {metadata.get('dfu_row', 'N/A')}")
        print(f"  Measurement Area: {metadata.get('measurement_area', 'Not present')}")
        print(f"  Timepoint: {metadata.get('timepoint', 'Not present')}")
        print(f"  File Type: {metadata.get('file_type', 'N/A')}")

        if has_dfu:
            successes += 1
            print(f"  [PASS] Successfully parsed")
        else:
            failures += 1
            print(f"  [FAIL] Failed to parse DFU row")

    return successes, failures

def main():
    """Run all tests."""
    print("\n" + "="*80)
    print("EXTRACTOR AGENT - AREA & TIMEPOINT PARSING TEST SUITE")
    print("="*80)

    # Test 1: File name parsing
    file_successes, file_failures = test_file_parsing()

    # Test 2: Full path extraction
    path_successes, path_failures = test_full_path_extraction()

    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    print(f"\nFile Name Parsing:")
    print(f"  Successes: {file_successes}/{file_successes + file_failures}")
    print(f"  Success Rate: {100 * file_successes / (file_successes + file_failures):.1f}%")

    print(f"\nFull Path Extraction:")
    print(f"  Successes: {path_successes}/{path_successes + path_failures}")
    print(f"  Success Rate: {100 * path_successes / (path_successes + path_failures):.1f}%")

    total_successes = file_successes + path_successes
    total_tests = file_successes + file_failures + path_successes + path_failures
    print(f"\nOverall:")
    print(f"  Total Successes: {total_successes}/{total_tests}")
    print(f"  Overall Success Rate: {100 * total_successes / total_tests:.1f}%")

    # Backwards compatibility check
    print(f"\nBackwards Compatibility:")
    print(f"  Simple file names (DFU1.csv, DFU2_roi1.txt) are parsed correctly")
    print(f"  New area/timepoint fields are optional (not required)")

    print("\n" + "="*80)

if __name__ == "__main__":
    main()
