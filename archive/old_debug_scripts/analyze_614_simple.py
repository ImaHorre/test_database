"""Simplified analysis of line 614 issue"""
import pandas as pd

# Load database
df = pd.read_csv('data/database.csv')

print("="*80)
print("CRITICAL FINDINGS: LINE 614 ISSUE")
print("="*80)

# Check measurement data presence
df['has_measurements'] = (df['droplet_size_mean'].notna()) | (df['frequency_mean'].notna())

print("\n1. MEASUREMENT DATA SUMMARY:")
print(f"   Total rows: {len(df)}")
print(f"   Rows WITH measurements: {df['has_measurements'].sum()}")
print(f"   Rows WITHOUT measurements: {(~df['has_measurements']).sum()}")

print("\n2. CRITICAL DISCOVERY - SCAN TIMESTAMP PATTERN:")
# Group by scan timestamp and check if there are two different scan sessions
df['scan_date'] = pd.to_datetime(df['scan_timestamp']).dt.date
unique_dates = df['scan_date'].unique()
print(f"   Unique scan dates: {unique_dates}")

for date in unique_dates:
    subset = df[df['scan_date'] == date]
    with_data = subset[subset['has_measurements']]
    without_data = subset[~subset['has_measurements']]

    print(f"\n   Scan date: {date}")
    print(f"      Total rows: {len(subset)}")
    print(f"      With measurements: {len(with_data)}")
    print(f"      Without measurements: {len(without_data)}")

    if len(without_data) > 0:
        print(f"      First row without measurements: index {without_data.index[0]}")
        print(f"      Last row without measurements: index {without_data.index[-1]}")

print("\n3. EXACT LINE 614 ANALYSIS:")
print("   Rows 612-616:")
for idx in range(612, 617):
    row = df.iloc[idx]
    print(f"\n   Row {idx}:")
    print(f"      File: {row['file_name']}")
    print(f"      Device: {row['device_id']}")
    print(f"      Type: {row['measurement_type']}")
    print(f"      Has droplet data: {pd.notna(row['droplet_size_mean'])}")
    print(f"      Has freq data: {pd.notna(row['frequency_mean'])}")
    print(f"      Scan timestamp: {row['scan_timestamp']}")
    print(f"      Extraction timestamp: {row['extraction_timestamp']}")

print("\n4. DEVICE TRANSITION ANALYSIS:")
# Check if there's a device change around line 614
print("   Device IDs around line 614:")
for idx in range(609, 620):
    row = df.iloc[idx]
    print(f"   Row {idx}: {row['device_id']} - {row['file_name'][:50]}")

print("\n5. KEY FINDING:")
print("   " + "="*76)
# Find the exact cutoff point
first_without_data = df[~df['has_measurements']].index[0]
last_with_data = df[df['has_measurements']].index[-1]

print(f"   LAST row WITH measurement data: {last_with_data}")
print(f"   FIRST row WITHOUT measurement data: {first_without_data}")
print(f"   Data extraction stopped at row: {last_with_data + 1}")
print("   " + "="*76)
