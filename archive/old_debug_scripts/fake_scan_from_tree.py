"""
Fake Scan Script - Parse Directory Tree File

This script simulates a scan by parsing the onedrive_tree_*.txt file
and running the extraction logic on each file path found.

It does NOT access the actual filesystem - only parses paths.
"""

import re
import sys
from pathlib import Path
from typing import List, Dict, Tuple
from collections import defaultdict
from datetime import datetime

# Import the extractor
sys.path.insert(0, str(Path(__file__).parent))
from src.extractor import MetadataExtractor


def parse_tree_file(tree_file_path: str) -> List[str]:
    """
    Parse the tree output file and extract all file paths.

    Args:
        tree_file_path: Path to onedrive_tree_*.txt file

    Returns:
        List of file paths (relative paths from root)
    """
    print(f"Reading tree file: {tree_file_path}")

    with open(tree_file_path, 'r', encoding='utf-8', errors='replace') as f:
        lines = f.readlines()

    file_paths = []
    path_stack = []  # Stack to track current directory path

    for line in lines:
        # Skip empty lines and header lines
        stripped = line.rstrip('\n\r')
        if not stripped or stripped.startswith('=') or 'Directory' in stripped:
            continue

        # Count leading spaces to determine depth
        # Tree output uses special characters: ├── └── │
        # Remove tree drawing characters
        clean_line = re.sub(r'[├└│─\s]+', '', line, count=1)
        depth = (len(line) - len(line.lstrip())) // 4  # Approximate depth

        # Extract item name (file or folder)
        item_name = stripped.split()[-1] if stripped.split() else ''

        # Skip if no item name
        if not item_name:
            continue

        # Determine if this is a file (has extension)
        is_file = '.' in item_name and (item_name.endswith('.csv') or item_name.endswith('.txt'))

        # Build path using simple heuristic: look for path-like patterns
        # Match lines that look like paths: "path/to/file.csv"
        path_match = re.search(r'([A-Za-z0-9_]+(?:[/\\][A-Za-z0-9_+.]+)+\.(csv|txt))', stripped)

        if path_match:
            file_path = path_match.group(1).replace('\\', '/')
            file_paths.append(file_path)

    print(f"Found {len(file_paths)} file paths in tree")
    return file_paths


def extract_file_paths_from_tree(tree_file_path: str) -> List[str]:
    """
    Parse tree file by building paths from hierarchical structure.

    Args:
        tree_file_path: Path to onedrive_tree_*.txt file

    Returns:
        List of file paths
    """
    print(f"Parsing tree file: {tree_file_path}")

    with open(tree_file_path, 'r', encoding='utf-8', errors='replace') as f:
        lines = f.readlines()

    file_paths = []
    path_stack = []  # Track current path (list of folder names)
    last_depth = -1

    for line_num, line in enumerate(lines):
        # Skip header and empty lines
        if not line.strip() or line.startswith('=') or 'Generated:' in line or 'Folder:' in line:
            continue

        # Count the tree characters to determine depth
        # Tree uses: │   for continuation, ├── for branch, └── for last branch
        # Each level adds 4 characters of indentation
        line_without_newline = line.rstrip('\n\r')

        # Count leading spaces/tree characters to determine depth
        stripped = line_without_newline.lstrip(' │├└─')
        indent_chars = len(line_without_newline) - len(stripped)

        # Depth is approximately indent_chars / 4
        depth = indent_chars // 4

        # Extract item name and type
        # Format: "├── 📁 folder_name" or "├── 📄 file.csv (size)"
        is_folder = '📁' in line
        is_file = '📄' in line

        if not (is_folder or is_file):
            continue

        # Extract name
        if is_file:
            # Extract filename (between 📄 and file size in parentheses)
            match = re.search(r'📄\s+([^\s(]+)', line)
        else:
            # Extract folder name (between 📁 and end)
            match = re.search(r'📁\s+(\S+)', line)

        if not match:
            continue

        name = match.group(1).strip()

        # Adjust path stack based on depth
        # If depth decreased, pop folders
        # If depth is same, replace last folder
        # If depth increased, add to stack
        if depth < last_depth:
            # Going up in hierarchy - pop folders
            path_stack = path_stack[:depth]
        elif depth == last_depth and path_stack:
            # Same level - replace last item
            path_stack = path_stack[:-1]

        if is_folder:
            # Add folder to path
            path_stack.append(name)
            last_depth = depth
        elif is_file:
            # Only process CSV and TXT files
            if name.endswith('.csv') or name.endswith('.txt'):
                # Build full path (skip root folder "test_database" if present)
                if path_stack and path_stack[0] == 'test_database':
                    full_path = '/'.join(path_stack[1:] + [name])
                else:
                    full_path = '/'.join(path_stack + [name])

                if full_path and '/' in full_path:  # Must have at least device/file structure
                    file_paths.append(full_path)

    print(f"Extracted {len(file_paths)} file paths")
    return file_paths


def should_skip_path(file_path: str, excluded_dirs: List[str]) -> bool:
    """
    Check if path should be skipped based on excluded directories.

    Args:
        file_path: File path to check
        excluded_dirs: List of directory names to exclude

    Returns:
        True if path should be skipped
    """
    path_parts = file_path.split('/')
    for part in path_parts:
        if part in excluded_dirs:
            return True
    return False


def run_fake_scan(tree_file_path: str, output_report_path: str):
    """
    Run fake scan by parsing tree file and extracting metadata.

    Args:
        tree_file_path: Path to tree file
        output_report_path: Path to save analysis report
    """
    print("\n" + "="*70)
    print("FAKE SCAN - Testing Updated Extraction Logic")
    print("="*70)

    # Initialize extractor
    extractor = MetadataExtractor()

    # Directories to exclude (matching scanner.py)
    excluded_dirs = ['Archive', 'outputs', '0_dfu_measure_tools', '0_freq_analysis_tools']

    # Parse tree file to get file paths
    file_paths = extract_file_paths_from_tree(tree_file_path)

    if not file_paths:
        print("ERROR: No file paths found in tree file")
        return

    # Filter out excluded directories
    filtered_paths = [p for p in file_paths if not should_skip_path(p, excluded_dirs)]
    excluded_count = len(file_paths) - len(filtered_paths)

    print(f"\nTotal file paths found: {len(file_paths)}")
    print(f"Excluded paths (Archive, outputs, tools): {excluded_count}")
    print(f"Paths to process: {len(filtered_paths)}")

    # Track results
    success_complete = []
    success_partial = []
    success_minimal = []
    failures = []

    # Track specific issues
    typo_corrections = defaultdict(int)
    inferred_fields = defaultdict(int)
    missing_priority_fields = defaultdict(list)

    # Priority fields to track
    priority_fields = ['device_id', 'bonding_date', 'aqueous_flowrate', 'oil_pressure',
                       'aqueous_fluid', 'oil_fluid', 'measurement_type']

    print("\nProcessing files...")
    print("-" * 70)

    for i, file_path in enumerate(filtered_paths):
        if i % 100 == 0 and i > 0:
            print(f"  Processed {i}/{len(filtered_paths)} files...")

        try:
            # Extract metadata (no local_path, so content parsing will be skipped)
            metadata = extractor.extract_from_path(file_path, local_path=None)

            # Categorize by parse quality
            quality = metadata.get('parse_quality', 'failed')

            if quality == 'complete':
                success_complete.append(file_path)
            elif quality == 'partial':
                success_partial.append(file_path)
            elif quality == 'minimal':
                success_minimal.append(file_path)
            else:
                failures.append((file_path, metadata))

            # Track typo corrections
            if metadata.get('fluid_typo_corrected'):
                typo_corrections['fluid_format'] += 1
            if metadata.get('flow_unit_typo_corrected'):
                typo_corrections['flow_unit_mlmin'] += 1
            if metadata.get('measurement_type_typo_corrected'):
                typo_corrections['measurement_type'] += 1

            # Track inferred fields
            if metadata.get('measurement_type_inferred'):
                inferred_fields['measurement_type'] += 1
            if metadata.get('aqueous_fluid_inferred'):
                inferred_fields['aqueous_fluid'] += 1
            if metadata.get('oil_fluid_inferred'):
                inferred_fields['oil_fluid'] += 1

            # Check for missing priority fields
            for field in priority_fields:
                if not metadata.get(field):
                    missing_priority_fields[field].append(file_path)

        except Exception as e:
            failures.append((file_path, {'error': str(e)}))

    # Calculate statistics
    total_processed = len(filtered_paths)
    total_success = len(success_complete) + len(success_partial) + len(success_minimal)
    total_failures = len(failures)

    success_rate = (total_success / total_processed * 100) if total_processed > 0 else 0

    # Generate report
    report_lines = []
    report_lines.append("=" * 80)
    report_lines.append("FAKE SCAN ANALYSIS REPORT - POST FIXES")
    report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append("=" * 80)
    report_lines.append("")

    report_lines.append("SUMMARY")
    report_lines.append("-" * 80)
    report_lines.append(f"Total files in tree:       {len(file_paths)}")
    report_lines.append(f"Excluded (Archive, etc.):  {excluded_count}")
    report_lines.append(f"Files processed:           {total_processed}")
    report_lines.append("")
    report_lines.append(f"Successful extractions:    {total_success} ({success_rate:.1f}%)")
    report_lines.append(f"  - Complete quality:      {len(success_complete)}")
    report_lines.append(f"  - Partial quality:       {len(success_partial)}")
    report_lines.append(f"  - Minimal quality:       {len(success_minimal)}")
    report_lines.append(f"Failed extractions:        {total_failures}")
    report_lines.append("")

    report_lines.append("TYPO CORRECTIONS APPLIED")
    report_lines.append("-" * 80)
    if typo_corrections:
        for typo_type, count in typo_corrections.items():
            report_lines.append(f"  {typo_type}: {count} corrections")
    else:
        report_lines.append("  None")
    report_lines.append("")

    report_lines.append("INFERRED FIELDS")
    report_lines.append("-" * 80)
    if inferred_fields:
        for field, count in inferred_fields.items():
            report_lines.append(f"  {field}: {count} inferences")
    else:
        report_lines.append("  None")
    report_lines.append("")

    report_lines.append("MISSING PRIORITY FIELDS")
    report_lines.append("-" * 80)
    if missing_priority_fields:
        for field, paths in missing_priority_fields.items():
            report_lines.append(f"\n{field}: {len(paths)} files missing")
            if len(paths) <= 10:
                for path in paths[:10]:
                    report_lines.append(f"  - {path}")
            else:
                for path in paths[:5]:
                    report_lines.append(f"  - {path}")
                report_lines.append(f"  ... and {len(paths) - 5} more")
    else:
        report_lines.append("  All priority fields present in all files!")
    report_lines.append("")

    report_lines.append("EXAMPLE SUCCESSFUL EXTRACTIONS (Complete Quality)")
    report_lines.append("-" * 80)
    if success_complete:
        for path in success_complete[:5]:
            metadata = extractor.extract_from_path(path, local_path=None)
            report_lines.append(f"\nFile: {path}")
            report_lines.append(f"  Device: {metadata.get('device_id')}")
            report_lines.append(f"  Bonding Date: {metadata.get('bonding_date')}")
            report_lines.append(f"  Fluids: {metadata.get('aqueous_fluid')}_{metadata.get('oil_fluid')}")
            report_lines.append(f"  Flow: {metadata.get('aqueous_flowrate')} ml/hr, {metadata.get('oil_pressure')} mbar")
            report_lines.append(f"  Measurement Type: {metadata.get('measurement_type')}")
            report_lines.append(f"  DFU: {metadata.get('dfu_row')}")
    else:
        report_lines.append("  No complete quality extractions")
    report_lines.append("")

    report_lines.append("EXAMPLE FAILURES")
    report_lines.append("-" * 80)
    if failures:
        for path, metadata in failures[:10]:
            report_lines.append(f"\nFile: {path}")
            if 'error' in metadata:
                report_lines.append(f"  Error: {metadata['error']}")
            else:
                report_lines.append(f"  Device: {metadata.get('device_id', 'MISSING')}")
                report_lines.append(f"  Bonding Date: {metadata.get('bonding_date', 'MISSING')}")
                report_lines.append(f"  Measurement Type: {metadata.get('measurement_type', 'MISSING')}")
    else:
        report_lines.append("  No failures! All files parsed successfully.")
    report_lines.append("")

    report_lines.append("=" * 80)
    report_lines.append("END OF REPORT")
    report_lines.append("=" * 80)

    # Write report to file
    with open(output_report_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report_lines))

    # Print summary to console
    print("\n" + "="*70)
    print("SCAN COMPLETE")
    print("="*70)
    print(f"Success Rate: {success_rate:.1f}%")
    print(f"  Complete: {len(success_complete)}")
    print(f"  Partial: {len(success_partial)}")
    print(f"  Minimal: {len(success_minimal)}")
    print(f"  Failed: {total_failures}")
    print(f"\nReport saved to: {output_report_path}")
    print("="*70)


if __name__ == "__main__":
    # Find the tree file
    tree_files = list(Path('.').glob('onedrive_tree_*.txt'))

    if not tree_files:
        print("ERROR: No onedrive_tree_*.txt file found in current directory")
        sys.exit(1)

    # Use the most recent tree file
    tree_file = sorted(tree_files)[-1]

    # Generate output report path
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_report = f"fake_scan_report_{timestamp}.txt"

    print(f"Using tree file: {tree_file}")
    print(f"Will save report to: {output_report}")

    run_fake_scan(str(tree_file), output_report)
