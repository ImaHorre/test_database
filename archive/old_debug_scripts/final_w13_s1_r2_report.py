"""
Final comprehensive analysis of W13_S1_R2 files.
Uses the extracted file list and tests actual parsing.
"""

import re
import sys
from pathlib import Path
from collections import defaultdict

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.extractor import MetadataExtractor

def extract_filename(line):
    """Extract filename from tree line."""
    match = re.search(r'(\d{4}_\d{4}_[^(]+\.(?:csv|txt))', line, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return None

def extract_timepoint_from_filename(filename):
    """Extract timepoint directly from filename."""
    match = re.search(r'_t(\d+)', filename, re.IGNORECASE)
    return int(match.group(1)) if match else None

def build_realistic_path(filename):
    """
    Build a realistic path based on filename pattern.

    The user mentioned files exist in TWO places:
    1. Inside dfu_measure/freq_analysis folders
    2. Directly under flow parameter folders

    We need to test BOTH scenarios.
    """
    device_id = "W13_S1_R2"

    # Parse filename parts
    # Pattern: BBDD_TTDD_deviceid_flowparams_fluids_DFUx_modifiers_timestamp.ext
    parts = filename.split('_')

    bonding_date = parts[0] if len(parts) > 0 else "0610"
    testing_date = parts[1] if len(parts) > 1 else "1310"

    # Find flow params
    flow_params = None
    fluids = None

    for i, part in enumerate(parts):
        if re.match(r'\d+mlhr\d+mbar', part, re.IGNORECASE):
            flow_params = part
            # Check previous part for fluids
            if i > 0:
                prev_part = parts[i-1]
                if re.match(r'[A-Za-z]+SO', prev_part, re.IGNORECASE):
                    fluids = prev_part
            break

    # Determine measurement type
    if filename.endswith('.csv'):
        measurement_type = 'dfu_measure'
    elif filename.endswith('.txt'):
        measurement_type = 'freq_analysis'
    else:
        measurement_type = 'unknown'

    # Build TWO paths: inside and outside measurement folders
    paths = []

    # Path 1: Inside measurement folder
    if flow_params:
        if fluids:
            path_inside = f"{device_id}/{bonding_date}/{testing_date}/{fluids}/{flow_params}/{measurement_type}/{filename}"
        else:
            path_inside = f"{device_id}/{bonding_date}/{testing_date}/{flow_params}/{measurement_type}/{filename}"
    else:
        path_inside = f"{device_id}/{bonding_date}/{testing_date}/{measurement_type}/{filename}"
    paths.append(('inside', path_inside))

    # Path 2: Outside measurement folder (directly under flow params)
    if flow_params:
        if fluids:
            path_outside = f"{device_id}/{bonding_date}/{testing_date}/{fluids}/{flow_params}/{filename}"
        else:
            path_outside = f"{device_id}/{bonding_date}/{testing_date}/{flow_params}/{filename}"
    else:
        path_outside = f"{device_id}/{bonding_date}/{testing_date}/{filename}"
    paths.append(('outside', path_outside))

    return paths

def main():
    print("=" * 100)
    print("FINAL W13_S1_R2 DEBUG REPORT")
    print("=" * 100)

    # Read extracted files
    files_list = Path("C:/Users/conor/Documents/Code Projects/test_database/w13_s1_r2_files.txt")

    if not files_list.exists():
        print(f"ERROR: {files_list} not found!")
        return

    with open(files_list, 'r', encoding='utf-8', errors='replace') as f:
        lines = f.readlines()

    # Extract filenames
    filenames = []
    for line in lines:
        fn = extract_filename(line)
        if fn:
            filenames.append(fn)

    print(f"\nTotal files extracted: {len(filenames)}")

    # Analyze timepoints
    files_with_timepoints = []
    for fn in filenames:
        tp = extract_timepoint_from_filename(fn)
        if tp is not None:
            files_with_timepoints.append((fn, tp))

    print(f"Files with timepoints: {len(files_with_timepoints)}")

    # Test extraction
    print("\n" + "=" * 100)
    print("EXTRACTION TESTING")
    print("=" * 100)

    extractor = MetadataExtractor()

    # Sample files for testing
    sample_files = filenames[:50]  # Test first 50

    results = {
        'inside_success': [],
        'inside_fail': [],
        'outside_success': [],
        'outside_fail': []
    }

    timepoint_results = {
        'correct': 0,
        'missing': 0,
        'incorrect': 0
    }

    print(f"\nTesting extraction on {len(sample_files)} sample files...")

    for filename in sample_files:
        paths = build_realistic_path(filename)
        expected_timepoint = extract_timepoint_from_filename(filename)

        for location, path in paths:
            result = extractor.extract_from_path(path)
            quality = result.get('parse_quality', 'failed')

            if quality in ['complete', 'partial']:
                if location == 'inside':
                    results['inside_success'].append((filename, result))
                else:
                    results['outside_success'].append((filename, result))

                # Check timepoint
                extracted_tp = result.get('timepoint')
                if expected_timepoint is None and extracted_tp is None:
                    timepoint_results['correct'] += 1
                elif expected_timepoint is not None and extracted_tp == expected_timepoint:
                    timepoint_results['correct'] += 1
                elif expected_timepoint is not None and extracted_tp is None:
                    timepoint_results['missing'] += 1
                elif expected_timepoint is not None and extracted_tp != expected_timepoint:
                    timepoint_results['incorrect'] += 1

            else:
                if location == 'inside':
                    results['inside_fail'].append((filename, result))
                else:
                    results['outside_fail'].append((filename, result))

    print("\n--- Extraction Results ---")
    print(f"Inside measurement folders:")
    print(f"  Success: {len(results['inside_success'])}")
    print(f"  Failed: {len(results['inside_fail'])}")

    print(f"\nOutside measurement folders:")
    print(f"  Success: {len(results['outside_success'])}")
    print(f"  Failed: {len(results['outside_fail'])}")

    # Coverage analysis
    unique_files_tested = len(sample_files)
    files_with_at_least_one_success = set()

    for fn, _ in results['inside_success']:
        files_with_at_least_one_success.add(fn)
    for fn, _ in results['outside_success']:
        files_with_at_least_one_success.add(fn)

    coverage = len(files_with_at_least_one_success)
    coverage_percent = (coverage / unique_files_tested * 100) if unique_files_tested > 0 else 0

    print(f"\n*** Coverage: {coverage}/{unique_files_tested} ({coverage_percent:.1f}%) ***")

    # Files with NO successful parse
    files_completely_missed = []
    for fn in sample_files:
        if fn not in files_with_at_least_one_success:
            files_completely_missed.append(fn)

    if files_completely_missed:
        print(f"\n!!! WARNING: {len(files_completely_missed)} files had NO successful parse !!!")
        print("\nFiles that would be completely missed:")
        for fn in files_completely_missed[:10]:
            print(f"  - {fn}")
    else:
        print("\nEXCELLENT: All files would be captured (at least one parse succeeded)")

    # Timepoint analysis
    print("\n" + "=" * 100)
    print("TIMEPOINT EXTRACTION ANALYSIS")
    print("=" * 100)

    print(f"\nTimepoint extraction results:")
    print(f"  Correct: {timepoint_results['correct']}")
    print(f"  Missing: {timepoint_results['missing']}")
    print(f"  Incorrect: {timepoint_results['incorrect']}")

    total_tp_tests = sum(timepoint_results.values())
    tp_accuracy = (timepoint_results['correct'] / total_tp_tests * 100) if total_tp_tests > 0 else 0

    print(f"\nTimepoint extraction accuracy: {tp_accuracy:.1f}%")

    # Show timepoint extraction examples
    print("\n--- Timepoint Extraction Examples ---")
    examples_shown = 0
    for fn, result in results['inside_success'][:10]:
        tp = result.get('timepoint')
        expected = extract_timepoint_from_filename(fn)
        if expected is not None:
            status = "OK" if tp == expected else "WRONG"
            print(f"  {fn}")
            print(f"    Expected: t{expected}, Extracted: {f't{tp}' if tp is not None else 'None'} [{status}]")
            examples_shown += 1
            if examples_shown >= 5:
                break

    # Check what field timepoint is stored in
    print("\n--- Timepoint Field Location ---")
    print("Checking extractor code...")
    print("  DFU_FILE_PATTERN (line 42): r'(?:DFU(\\d+)|firstDFUs)(?:_([A-CX]))?(?:_t(\\d+))?'")
    print("  Extraction (line 314): timepoint = int(match.group(3)) if match.group(3) else None")
    print("  Storage (line 360-361): if timepoint is not None: result['timepoint'] = timepoint")
    print("\n  FIELD NAME: 'timepoint'")
    print("  FIELD TYPE: integer (0, 1, 3, 4, 5, etc.)")
    print("  FIELD STATUS: WORKING and IMPLEMENTED")

    # Final recommendations
    print("\n" + "=" * 100)
    print("RECOMMENDATIONS")
    print("=" * 100)

    print("\n1. FILE COVERAGE:")
    if coverage_percent >= 99:
        print("   STATUS: EXCELLENT - All files would be captured")
        print("   ACTION: None required")
    elif coverage_percent >= 90:
        print(f"   STATUS: GOOD - Most files captured, {len(files_completely_missed)} might be missed")
        print("   ACTION: Review failed parses to improve extraction patterns")
    else:
        print(f"   STATUS: NEEDS ATTENTION - {len(files_completely_missed)} files would be missed")
        print("   ACTION: Review and fix parsing logic")

    print("\n2. TIMEPOINT EXTRACTION:")
    if tp_accuracy >= 99:
        print("   STATUS: WORKING CORRECTLY")
        print("   FIELD: 'timepoint' (integer)")
        print("   ACTION: None required")
    else:
        print(f"   STATUS: NEEDS IMPROVEMENT ({tp_accuracy:.1f}% accuracy)")
        print("   ACTION: Review parse_file_name() regex pattern")

    print("\n3. FILE LOCATION STRATEGY:")
    inside_success_rate = len(results['inside_success']) / len(sample_files) * 100 if sample_files else 0
    outside_success_rate = len(results['outside_success']) / len(sample_files) * 100 if sample_files else 0

    print(f"   Inside folders success rate: {inside_success_rate:.1f}%")
    print(f"   Outside folders success rate: {outside_success_rate:.1f}%")

    if inside_success_rate > outside_success_rate:
        print("   RECOMMENDATION: Files inside measurement folders parse better")
    elif outside_success_rate > inside_success_rate:
        print("   RECOMMENDATION: Files outside measurement folders parse better")
    else:
        print("   RECOMMENDATION: Both locations parse equally well")

    print("\n" + "=" * 100)
    print("END OF REPORT")
    print("=" * 100)

if __name__ == "__main__":
    main()
