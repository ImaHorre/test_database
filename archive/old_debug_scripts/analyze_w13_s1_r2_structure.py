"""
Advanced analysis of W13_S1_R2 folder structure.
Reads the full tree output to understand file locations precisely.
"""

import re
from collections import defaultdict

def parse_tree_structure(tree_file):
    """
    Parse the tree output to understand exact file locations.

    Tree structure uses indentation to show hierarchy:
    - │   = continuation of tree branch
    - ├── = branch node
    - └── = final branch node
    - More indentation = deeper in hierarchy
    """
    with open(tree_file, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()

    # Split into lines
    lines = content.split('\n')

    # Find the W13_S1_R2 section
    w13_s1_r2_section = []
    in_section = False
    section_indent = None

    for i, line in enumerate(lines):
        if 'W13_S1_R2' in line and '📁' in line:
            in_section = True
            section_indent = len(line) - len(line.lstrip())
            w13_s1_r2_section.append((i, line))
            continue

        if in_section:
            current_indent = len(line) - len(line.lstrip())

            # Check if we've exited this section (back to same or less indentation with a folder marker)
            if '📁' in line and current_indent <= section_indent:
                # We've moved to the next top-level folder
                break

            w13_s1_r2_section.append((i, line))

    return w13_s1_r2_section

def analyze_file_context(section_lines):
    """
    Analyze each file's context by looking at preceding lines for folder names.
    """
    files_with_context = []

    for i, (line_num, line) in enumerate(section_lines):
        # Check if this is a CSV or TXT file
        if '📄' in line and ('.csv' in line.lower() or '.txt' in line.lower()):
            # Extract filename
            match = re.search(r'📄\s+(.+?)\s+\([\d.]+\s*[KMG]?B\)', line)
            if not match:
                continue

            filename = match.group(1).strip()

            # Determine indent level
            indent = len(line) - len(line.lstrip())

            # Look backwards to find parent folders
            folders_above = []
            for j in range(i-1, -1, -1):
                prev_line_num, prev_line = section_lines[j]
                prev_indent = len(prev_line) - len(prev_line.lstrip())

                # If we find a folder at a shallower indent, it's a parent
                if prev_indent < indent and '📁' in prev_line:
                    # Extract folder name
                    folder_match = re.search(r'📁\s+(.+?)(?:\s|$)', prev_line)
                    if folder_match:
                        folder_name = folder_match.group(1).strip()
                        folders_above.insert(0, (prev_indent, folder_name))
                        indent = prev_indent  # Update indent to continue looking for grandparents

            # Determine if file is inside measurement folders
            folder_names = [f[1] for f in folders_above]
            location = 'unknown'

            if 'dfu_measure' in folder_names or 'freq_analysis' in folder_names:
                location = 'inside_measurement_folders'
            elif any('mlhr' in f.lower() for f in folder_names):
                # Directly under flow parameter folder
                location = 'under_flow_param_folder'
            else:
                location = 'other'

            files_with_context.append({
                'filename': filename,
                'location': location,
                'folder_path': folder_names,
                'line_num': line_num
            })

    return files_with_context

def main():
    tree_file = "C:/Users/conor/Documents/Code Projects/test_database/onedrive_tree_20251107_134138.txt"

    print("=" * 100)
    print("W13_S1_R2 STRUCTURAL ANALYSIS")
    print("=" * 100)

    # Parse tree structure
    print("\nParsing tree structure...")
    section = parse_tree_structure(tree_file)
    print(f"Found W13_S1_R2 section with {len(section)} lines")

    # Analyze file contexts
    print("\nAnalyzing file contexts...")
    files = analyze_file_context(section)
    print(f"Found {len(files)} CSV/TXT files")

    # Categorize by location
    inside_measurement = [f for f in files if f['location'] == 'inside_measurement_folders']
    under_flow_param = [f for f in files if f['location'] == 'under_flow_param_folder']
    other = [f for f in files if f['location'] == 'other']

    print("\n" + "=" * 100)
    print("FILE LOCATION BREAKDOWN")
    print("=" * 100)

    print(f"\nFiles INSIDE dfu_measure/freq_analysis folders: {len(inside_measurement)}")
    print(f"Files UNDER flow parameter folders (outside measurement folders): {len(under_flow_param)}")
    print(f"Files in OTHER locations: {len(other)}")

    # Show examples
    if inside_measurement:
        print("\n--- Example files INSIDE measurement folders ---")
        for f in inside_measurement[:5]:
            path_str = ' -> '.join(f['folder_path'])
            print(f"  {f['filename']}")
            print(f"    Path: {path_str}")

    if under_flow_param:
        print("\n--- Example files UNDER flow parameter folders ---")
        for f in under_flow_param[:5]:
            path_str = ' -> '.join(f['folder_path'])
            print(f"  {f['filename']}")
            print(f"    Path: {path_str}")

    if other:
        print("\n--- Example files in OTHER locations ---")
        for f in other[:5]:
            path_str = ' -> '.join(f['folder_path'])
            print(f"  {f['filename']}")
            print(f"    Path: {path_str}")

    # Check for duplicate files (same name in different locations)
    print("\n" + "=" * 100)
    print("DUPLICATE DETECTION")
    print("=" * 100)

    filename_locations = defaultdict(list)
    for f in files:
        filename_locations[f['filename']].append(f['location'])

    duplicates = {k: v for k, v in filename_locations.items() if len(v) > 1}

    print(f"\nFiles appearing in multiple locations: {len(duplicates)}")

    if duplicates:
        print("\nExamples of duplicated files:")
        for i, (filename, locations) in enumerate(list(duplicates.items())[:10]):
            print(f"  {filename}")
            print(f"    Locations: {', '.join(set(locations))}")

    # Unique file check (by base name, ignoring timestamps)
    print("\n" + "=" * 100)
    print("UNIQUE FILE ANALYSIS (ignoring timestamps)")
    print("=" * 100)

    def get_base_name(filename):
        # Remove timestamp: _YYYYMMDD_HHMMSS
        base = re.sub(r'_\d{8}_\d{6}', '', filename)
        return base

    base_name_groups = defaultdict(lambda: {'inside': 0, 'outside': 0, 'other': 0})

    for f in files:
        base = get_base_name(f['filename'])
        if f['location'] == 'inside_measurement_folders':
            base_name_groups[base]['inside'] += 1
        elif f['location'] == 'under_flow_param_folder':
            base_name_groups[base]['outside'] += 1
        else:
            base_name_groups[base]['other'] += 1

    print(f"\nTotal unique files (by base name): {len(base_name_groups)}")

    # Count files in different scenarios
    only_inside = sum(1 for g in base_name_groups.values() if g['inside'] > 0 and g['outside'] == 0 and g['other'] == 0)
    only_outside = sum(1 for g in base_name_groups.values() if g['inside'] == 0 and g['outside'] > 0 and g['other'] == 0)
    both = sum(1 for g in base_name_groups.values() if g['inside'] > 0 and g['outside'] > 0)
    only_other = sum(1 for g in base_name_groups.values() if g['inside'] == 0 and g['outside'] == 0 and g['other'] > 0)

    print(f"\nFiles ONLY inside measurement folders: {only_inside}")
    print(f"Files ONLY outside (under flow param folders): {only_outside}")
    print(f"Files in BOTH locations: {both}")
    print(f"Files in OTHER locations only: {only_other}")

    # Calculate coverage
    total_unique = len(base_name_groups)
    covered = only_inside + only_outside + both  # All files except those only in 'other'
    coverage = (covered / total_unique * 100) if total_unique > 0 else 0

    print(f"\n*** COVERAGE: {covered}/{total_unique} ({coverage:.1f}%) ***")

    if only_other > 0:
        print(f"\n*** WARNING: {only_other} files only found in OTHER locations (may be missed!) ***")

    # Show files that would be missed (only in 'other' location)
    if only_other > 0:
        print("\n--- Files that might be missed ---")
        for base_name, counts in base_name_groups.items():
            if counts['inside'] == 0 and counts['outside'] == 0 and counts['other'] > 0:
                # Find examples
                examples = [f['filename'] for f in files if get_base_name(f['filename']) == base_name and f['location'] == 'other']
                print(f"  Base: {base_name}")
                for ex in examples[:2]:
                    print(f"    - {ex}")

    # Final summary
    print("\n" + "=" * 100)
    print("FINAL SUMMARY")
    print("=" * 100)

    print(f"\nTotal files in W13_S1_R2: {len(files)}")
    print(f"  Inside measurement folders: {len(inside_measurement)}")
    print(f"  Under flow param folders: {len(under_flow_param)}")
    print(f"  Other locations: {len(other)}")

    print(f"\nUnique files (by base name): {total_unique}")
    print(f"  Only inside: {only_inside}")
    print(f"  Only outside: {only_outside}")
    print(f"  In both: {both}")
    print(f"  Only other: {only_other}")

    print(f"\nCoverage: {coverage:.1f}%")

    if coverage >= 99.9:
        print("\n✓ All files would be captured by the scanner")
    elif coverage >= 90:
        print(f"\n⚠ Most files would be captured, but {total_unique - covered} might be missed")
    else:
        print(f"\n✗ Significant gaps: {total_unique - covered} files might be missed")

    print("\n" + "=" * 100)

if __name__ == "__main__":
    main()
