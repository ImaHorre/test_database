"""
Detailed Extraction Analysis

Re-run extraction with detailed tracking to get complete statistics
on timepoints, area suffixes, device types, and other metadata fields.
"""

import sys
from pathlib import Path
from collections import Counter, defaultdict
from datetime import datetime
import re

# Import the extractor
sys.path.insert(0, str(Path(__file__).parent))
from src.extractor import MetadataExtractor


def extract_file_paths_from_tree(tree_file_path: str):
    """Parse tree file to extract file paths (using emoji markers)."""
    with open(tree_file_path, 'r', encoding='utf-8', errors='replace') as f:
        lines = f.readlines()

    file_paths = []
    path_stack = []
    last_depth = -1

    for line_num, line in enumerate(lines):
        # Skip header and empty lines
        if not line.strip() or line.startswith('=') or 'Generated:' in line or 'Folder:' in line:
            continue

        # Count leading spaces/tree characters to determine depth
        line_without_newline = line.rstrip('\n\r')
        stripped = line_without_newline.lstrip(' │├└─')
        indent_chars = len(line_without_newline) - len(stripped)
        depth = indent_chars // 4

        # Extract item name and type using emojis
        is_folder = '📁' in line
        is_file = '📄' in line

        if not (is_folder or is_file):
            continue

        # Extract name
        if is_file:
            match = re.search(r'📄\s+([^\s(]+)', line)
        else:
            match = re.search(r'📁\s+(\S+)', line)

        if not match:
            continue

        name = match.group(1).strip()

        # Adjust path stack based on depth
        if depth < last_depth:
            path_stack = path_stack[:depth]
        elif depth == last_depth and path_stack:
            path_stack = path_stack[:-1]

        if is_folder:
            path_stack.append(name)
            last_depth = depth
        elif is_file:
            # Only process CSV and TXT files
            if name.endswith('.csv') or name.endswith('.txt'):
                # Build full path (skip root if present)
                if path_stack and path_stack[0] == 'test_database':
                    full_path = '/'.join(path_stack[1:] + [name])
                else:
                    full_path = '/'.join(path_stack + [name])

                if full_path and '/' in full_path:
                    file_paths.append(full_path)

    return file_paths


def main():
    # Find tree file
    tree_files = sorted(Path('.').glob('onedrive_tree_*.txt'))
    if not tree_files:
        print("ERROR: No tree file found")
        return

    tree_file = tree_files[-1]
    print(f"Analyzing: {tree_file}")
    print()

    # Parse tree file
    file_paths = extract_file_paths_from_tree(str(tree_file))
    print(f"Found {len(file_paths)} file paths")
    print()

    # Filter out excluded paths
    excluded_patterns = ['Archive', 'outputs', 'tools', 'Report']
    filtered_paths = [
        p for p in file_paths
        if not any(pattern in p for pattern in excluded_patterns)
    ]
    print(f"After filtering: {len(filtered_paths)} paths to analyze")
    print()

    # Initialize extractor and collect statistics
    extractor = MetadataExtractor()

    # Counters for detailed statistics
    device_types = Counter()
    timepoints = Counter()
    area_suffixes = Counter()
    dfu_numbers = Counter()
    roi_numbers = Counter()
    measurement_types = Counter()
    aqueous_fluids = Counter()
    oil_fluids = Counter()
    flow_combinations = Counter()
    bonding_dates = Counter()

    quality_counts = Counter()
    files_with_timepoint = 0
    files_with_area = 0

    successful_extractions = []
    failed_extractions = []

    # Process each file
    for i, file_path in enumerate(filtered_paths, 1):
        if i % 100 == 0:
            print(f"  Processing {i}/{len(filtered_paths)}...")

        # Extract metadata
        metadata = extractor.extract_from_path(file_path)

        # Quality assessment
        has_device = bool(metadata.get('device_id'))
        has_date = bool(metadata.get('bonding_date'))
        has_flow = bool(metadata.get('aqueous_flowrate')) and bool(metadata.get('oil_pressure'))
        has_meas_type = bool(metadata.get('measurement_type'))

        if has_device and has_date and has_flow and has_meas_type:
            quality = 'complete'
            successful_extractions.append((file_path, metadata))
        elif has_device and (has_date or has_flow):
            quality = 'partial'
            successful_extractions.append((file_path, metadata))
        elif has_device or has_meas_type:
            quality = 'minimal'
        else:
            quality = 'failed'
            failed_extractions.append((file_path, metadata))

        quality_counts[quality] += 1

        # Collect statistics
        if device_id := metadata.get('device_id'):
            device_types[device_id] += 1

        if timepoint := metadata.get('timepoint'):
            timepoints[timepoint] += 1
            files_with_timepoint += 1

        if area := metadata.get('area_suffix'):
            area_suffixes[area] += 1
            files_with_area += 1

        if dfu := metadata.get('dfu_number'):
            dfu_numbers[dfu] += 1

        if roi := metadata.get('roi_number'):
            roi_numbers[roi] += 1

        if mtype := metadata.get('measurement_type'):
            measurement_types[mtype] += 1

        if aq_fluid := metadata.get('aqueous_fluid'):
            aqueous_fluids[aq_fluid] += 1

        if oil := metadata.get('oil_fluid'):
            oil_fluids[oil] += 1

        flowrate = metadata.get('aqueous_flowrate')
        pressure = metadata.get('oil_pressure')
        if flowrate and pressure:
            flow_combinations[(flowrate, pressure)] += 1

        if date := metadata.get('bonding_date'):
            bonding_dates[date] += 1

    # Generate detailed report
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_path = f'detailed_extraction_statistics_{timestamp}.txt'

    with open(report_path, 'w', encoding='utf-8') as f:
        f.write('=' * 80 + '\n')
        f.write('DETAILED EXTRACTION STATISTICS REPORT\n')
        f.write(f'Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n')
        f.write('=' * 80 + '\n\n')

        # Overall quality
        total = len(filtered_paths)
        f.write('EXTRACTION QUALITY SUMMARY\n')
        f.write('-' * 80 + '\n')
        for quality in ['complete', 'partial', 'minimal', 'failed']:
            count = quality_counts[quality]
            pct = count / total * 100
            f.write(f'{quality.upper():10s}: {count:4d} ({pct:5.1f}%)\n')
        f.write('\n')

        # Device type breakdown
        f.write('DEVICE TYPE DISTRIBUTION\n')
        f.write('-' * 80 + '\n')
        w13_devices = {d: c for d, c in device_types.items() if d.startswith('W13')}
        w14_devices = {d: c for d, c in device_types.items() if d.startswith('W14')}

        w13_total = sum(w13_devices.values())
        w14_total = sum(w14_devices.values())

        f.write(f'W13 Devices: {w13_total} files across {len(w13_devices)} unique devices\n')
        f.write(f'W14 Devices: {w14_total} files across {len(w14_devices)} unique devices\n')
        f.write(f'\nTop 15 Devices by File Count:\n')
        for device, count in device_types.most_common(15):
            f.write(f'  {device:15s}: {count:4d} files\n')
        f.write('\n')

        # Timepoint statistics
        f.write('TIMEPOINT EXTRACTION STATISTICS\n')
        f.write('-' * 80 + '\n')
        f.write(f'Files with timepoint data: {files_with_timepoint} ({files_with_timepoint/total*100:.1f}%)\n')
        if timepoints:
            f.write(f'Unique timepoints found: {len(timepoints)}\n')
            f.write('Distribution:\n')
            for tp in sorted(timepoints.keys(), key=lambda x: int(x) if isinstance(x, (int, str)) and str(x).isdigit() else 0):
                count = timepoints[tp]
                f.write(f'  t{tp}: {count:4d} files\n')
        else:
            f.write('No timepoint data found\n')
        f.write('\n')

        # Area suffix statistics
        f.write('AREA SUFFIX EXTRACTION STATISTICS\n')
        f.write('-' * 80 + '\n')
        f.write(f'Files with area suffix: {files_with_area} ({files_with_area/total*100:.1f}%)\n')
        if area_suffixes:
            f.write(f'Unique area suffixes: {len(area_suffixes)}\n')
            f.write('Distribution:\n')
            for area in sorted(area_suffixes.keys()):
                count = area_suffixes[area]
                f.write(f'  _{area}: {count:4d} files\n')
        else:
            f.write('No area suffix data found\n')
        f.write('\n')

        # Measurement type
        f.write('MEASUREMENT TYPE DISTRIBUTION\n')
        f.write('-' * 80 + '\n')
        for mtype, count in measurement_types.most_common():
            pct = count / total * 100
            f.write(f'{mtype:20s}: {count:4d} ({pct:5.1f}%)\n')
        f.write('\n')

        # DFU distribution
        f.write('DFU NUMBER DISTRIBUTION\n')
        f.write('-' * 80 + '\n')
        for dfu in sorted(dfu_numbers.keys(), key=lambda x: int(x) if isinstance(x, (int, str)) and str(x).isdigit() else 0):
            count = dfu_numbers[dfu]
            pct = count / total * 100
            f.write(f'DFU{dfu}: {count:4d} ({pct:5.1f}%)\n')
        f.write('\n')

        # Fluid combinations
        f.write('FLUID COMBINATIONS\n')
        f.write('-' * 80 + '\n')
        fluid_pairs = defaultdict(int)
        for aq_fluid, count in aqueous_fluids.items():
            fluid_pairs[aq_fluid] += count
        for oil, count in oil_fluids.items():
            fluid_pairs[oil] += count

        f.write('Aqueous Fluids:\n')
        for fluid, count in aqueous_fluids.most_common():
            pct = count / total * 100
            f.write(f'  {fluid:25s}: {count:4d} ({pct:5.1f}%)\n')

        f.write('\nOil Fluids:\n')
        for fluid, count in oil_fluids.most_common():
            pct = count / total * 100
            f.write(f'  {fluid:25s}: {count:4d} ({pct:5.1f}%)\n')
        f.write('\n')

        # Flow parameters
        f.write('FLOW PARAMETER COMBINATIONS\n')
        f.write('-' * 80 + '\n')
        f.write('Top 20 flow combinations:\n')
        for (flowrate, pressure), count in flow_combinations.most_common(20):
            f.write(f'  {flowrate:4.1f} ml/hr, {pressure:4.0f} mbar: {count:4d} files\n')
        f.write('\n')

        # Sample successful extractions
        f.write('SAMPLE SUCCESSFUL EXTRACTIONS (Complete Quality)\n')
        f.write('-' * 80 + '\n')
        complete_examples = [(p, m) for p, m in successful_extractions if quality_counts['complete'] > 0][:5]
        for i, (path, metadata) in enumerate(complete_examples, 1):
            f.write(f'\n{i}. {path}\n')
            for key, value in metadata.items():
                if value:
                    f.write(f'   {key}: {value}\n')
        f.write('\n')

        # Sample failures
        f.write('SAMPLE FAILED EXTRACTIONS\n')
        f.write('-' * 80 + '\n')
        for i, (path, metadata) in enumerate(failed_extractions[:10], 1):
            f.write(f'\n{i}. {path}\n')
            f.write(f'   Extracted fields:\n')
            for key, value in metadata.items():
                if value:
                    f.write(f'     {key}: {value}\n')
            f.write(f'   Missing critical fields:\n')
            if not metadata.get('device_id'):
                f.write('     - device_id\n')
            if not metadata.get('bonding_date'):
                f.write('     - bonding_date\n')
            if not metadata.get('aqueous_flowrate') or not metadata.get('oil_pressure'):
                f.write('     - flow parameters\n')
        f.write('\n')

        f.write('=' * 80 + '\n')
        f.write('END OF DETAILED STATISTICS\n')
        f.write('=' * 80 + '\n')

    print(f"\nDetailed statistics saved to: {report_path}")
    print()
    print("Summary:")
    print(f"  Total files: {total}")
    print(f"  Complete: {quality_counts['complete']}")
    print(f"  Partial: {quality_counts['partial']}")
    print(f"  Minimal: {quality_counts['minimal']}")
    print(f"  Failed: {quality_counts['failed']}")
    print(f"  Files with timepoint: {files_with_timepoint}")
    print(f"  Files with area suffix: {files_with_area}")
    print(f"  Unique devices: {len(device_types)}")


if __name__ == '__main__':
    main()
