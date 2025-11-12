"""Check if files from line 614+ actually exist"""
import pandas as pd
import os

# Load database
df = pd.read_csv('data/database.csv')

print("="*80)
print("FILE EXISTENCE CHECK")
print("="*80)

# Check rows 612-620 (the ones without measurements)
print("\nChecking rows 612-620 (first rows without measurements):")
for idx in range(612, 620):
    row = df.iloc[idx]
    raw_path = row['raw_path']
    file_name = row['file_name']

    print(f"\nRow {idx}: {file_name}")
    print(f"  Raw path: {raw_path}")

    # Try to find the actual file
    # The raw_path is relative, need to find base directory
    possible_base_dirs = [
        'fake_onedrive_database',
        'C:/Users/conor/Documents/Code Projects/test_database/fake_onedrive_database',
        '.'
    ]

    file_found = False
    full_path = None

    for base in possible_base_dirs:
        test_path = os.path.join(base, raw_path)
        if os.path.exists(test_path):
            file_found = True
            full_path = test_path
            break

    if file_found:
        print(f"  FILE EXISTS at: {full_path}")
        # Try to check file size
        try:
            size = os.path.getsize(full_path)
            print(f"  File size: {size} bytes")

            # For CSV files, try to read first few lines
            if file_name.endswith('.csv'):
                try:
                    with open(full_path, 'r') as f:
                        lines = f.readlines()[:5]
                    print(f"  CSV has {len(lines)} lines (showing first 5)")
                    for i, line in enumerate(lines):
                        print(f"    Line {i}: {line.strip()[:100]}")
                except Exception as e:
                    print(f"  Could not read CSV: {e}")

        except Exception as e:
            print(f"  Error checking file: {e}")
    else:
        print(f"  FILE NOT FOUND in any of: {possible_base_dirs}")

# Also check one file that DID get measurements extracted (for comparison)
print("\n" + "="*80)
print("COMPARISON: Check a file that DID get measurements (row 1):")
print("="*80)
row = df.iloc[0]
raw_path = row['raw_path']
file_name = row['file_name']

print(f"\nRow 0: {file_name}")
print(f"  Raw path: {raw_path}")
print(f"  Has droplet_size_mean: {pd.notna(row['droplet_size_mean'])}")

for base in possible_base_dirs:
    test_path = os.path.join(base, raw_path)
    if os.path.exists(test_path):
        print(f"  FILE EXISTS at: {test_path}")
        size = os.path.getsize(test_path)
        print(f"  File size: {size} bytes")
        break
