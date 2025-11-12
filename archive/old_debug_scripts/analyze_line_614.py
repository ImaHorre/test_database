"""Quick analysis script to understand line 614 issue"""
import pandas as pd

# Load database
df = pd.read_csv('data/database.csv')

print("="*80)
print("ANALYSIS OF LINE 614 ISSUE")
print("="*80)

print("\n1. SCAN TIMESTAMPS COMPARISON:")
print("-" * 80)
print("\nLines 610-614 (before cutoff):")
print(df.iloc[609:614][['file_name', 'scan_timestamp', 'droplet_size_mean', 'frequency_mean']])

print("\nLines 614-620 (after cutoff):")
print(df.iloc[613:620][['file_name', 'scan_timestamp', 'droplet_size_mean', 'frequency_mean']])

print("\n\n2. MEASUREMENT DATA PRESENCE:")
print("-" * 80)
# Check which rows have measurement data
df['has_droplet_data'] = df['droplet_size_mean'].notna()
df['has_freq_data'] = df['frequency_mean'].notna()

print(f"\nTotal rows: {len(df)}")
print(f"Rows with droplet data: {df['has_droplet_data'].sum()}")
print(f"Rows with frequency data: {df['has_freq_data'].sum()}")
print(f"Rows with NO measurement data: {(~df['has_droplet_data'] & ~df['has_freq_data']).sum()}")

print("\n\n3. SCAN TIMESTAMP ANALYSIS:")
print("-" * 80)
unique_timestamps = df['scan_timestamp'].unique()
print(f"\nUnique scan timestamps found: {len(unique_timestamps)}")

for ts in unique_timestamps:
    subset = df[df['scan_timestamp'] == ts]
    has_measurements = subset[(subset['has_droplet_data']) | (subset['has_freq_data'])]
    no_measurements = subset[~((subset['has_droplet_data']) | (subset['has_freq_data']))]

    print(f"\nTimestamp: {ts}")
    print(f"  Total rows: {len(subset)}")
    print(f"  With measurements: {len(has_measurements)}")
    print(f"  Without measurements: {len(no_measurements)}")

    if len(no_measurements) > 0:
        print(f"  First row without measurements: {no_measurements.index[0]}")
        print(f"  Last row without measurements: {no_measurements.index[-1]}")

print("\n\n4. EXTRACTION TIMESTAMP ANALYSIS:")
print("-" * 80)
print("\nExtraction timestamps for rows 610-620:")
print(df.iloc[609:620][['file_name', 'extraction_timestamp', 'scan_timestamp']])

print("\n\n5. FILE TYPE ANALYSIS AROUND LINE 614:")
print("-" * 80)
print(df.iloc[609:620][['file_name', 'file_type', 'measurement_type', 'has_droplet_data', 'has_freq_data']])

print("\n\n6. DEVICE ID CHANGE ANALYSIS:")
print("-" * 80)
print("\nDevice IDs around line 614:")
print(df.iloc[609:620][['device_id', 'bonding_date', 'testing_date', 'file_name']])
