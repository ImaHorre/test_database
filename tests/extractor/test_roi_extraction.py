"""
Test ROI Extraction - Verify ROI parsing works correctly with area/timepoint
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from src.extractor import MetadataExtractor

# Sample file names with ROI
ROI_TEST_FILES = [
    ("DFU1_roi1.txt", {"dfu": 1, "roi": 1, "area": None, "timepoint": None}),
    ("DFU2_roi5.txt", {"dfu": 2, "roi": 5, "area": None, "timepoint": None}),
    ("DFU3_B_t0_ROI1_frequency_analysis.txt", {"dfu": 3, "roi": 1, "area": "B", "timepoint": 0}),
    ("DFU4_C_t1_ROI4_frequency_analysis.txt", {"dfu": 4, "roi": 4, "area": "C", "timepoint": 1}),
    ("DFU5_A_t2_ROI2_frequency_analysis.txt", {"dfu": 5, "roi": 2, "area": "A", "timepoint": 2}),
    ("1408_2308_w13_s1_r1_30mlhr100mbar_DFU6_B_t0_ROI5_frequency_analysis.txt",
     {"dfu": 6, "roi": 5, "area": "B", "timepoint": 0}),
]

def test_roi_extraction():
    """Test ROI extraction with various file name patterns."""
    extractor = MetadataExtractor()

    print("\n" + "="*80)
    print("ROI EXTRACTION TEST")
    print("="*80)

    passed = 0
    failed = 0

    for file_name, expected in ROI_TEST_FILES:
        print(f"\nFile: {file_name}")
        result = extractor.parse_file_name(file_name)

        if not result:
            print(f"  [FAIL] Could not parse file name")
            failed += 1
            continue

        # Check expected values
        checks = []
        checks.append(("DFU Row", result.get('dfu_row'), expected['dfu']))
        checks.append(("ROI", result.get('roi'), expected['roi']))
        checks.append(("Area", result.get('measurement_area'), expected['area']))
        checks.append(("Timepoint", result.get('timepoint'), expected['timepoint']))

        all_correct = True
        for field_name, actual, expect in checks:
            match = actual == expect
            status = "[OK]" if match else "[MISMATCH]"
            print(f"  {status} {field_name}: {actual} (expected: {expect})")
            if not match:
                all_correct = False

        if all_correct:
            passed += 1
            print(f"  [PASS]")
        else:
            failed += 1
            print(f"  [FAIL]")

    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"Passed: {passed}/{passed + failed}")
    print(f"Failed: {failed}/{passed + failed}")
    print(f"Success Rate: {100 * passed / (passed + failed):.1f}%")

    return passed == len(ROI_TEST_FILES)

if __name__ == "__main__":
    success = test_roi_extraction()
    sys.exit(0 if success else 1)
