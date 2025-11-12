"""Debug why W13_S2_R2 isn't showing in device breakdown."""
import pandas as pd

# Load data directly
df = pd.read_csv('data/database.csv')

# Filter to W13 at 5mlhr (same as command: show w13 at 5mlhr)
filtered = df[(df['device_type'] == 'W13') & (df['aqueous_flowrate'] == 5)]

print(f"Total filtered records: {len(filtered)}")
print(f"Unique devices: {filtered['device_id'].unique()}")
print()

# Group by experimental condition (same as _count_complete_analyses)
condition_groups = filtered.groupby([
    'device_id', 'testing_date', 'aqueous_flowrate', 'oil_pressure',
    'aqueous_fluid', 'oil_fluid'
])

print(f"Number of condition groups: {len(condition_groups)}")
print()

all_conditions = list(condition_groups.groups.keys())
print(f"All condition keys: {all_conditions}")
print()

import sys

for i, (condition, group) in enumerate(condition_groups, 1):
    print(f"Processing group {i}...", flush=True)
    try:
        device_id, test_date, flowrate, pressure, aq_fluid, oil_fluid = condition
        print(f"  Device: {device_id}, Test Date: {test_date}", flush=True)

        # Count DFU rows
        droplet_files = group[
            (group['measurement_type'] == 'dfu_measure') &
            (group['file_type'] == 'csv') &
            (pd.notna(group['dfu_row']))
        ]
        unique_dfu_rows = droplet_files['dfu_row'].nunique()

        # Count frequency
        freq_files = group[
            (group['measurement_type'] == 'freq_analysis') &
            (group['file_type'] == 'txt')
        ]
        has_freq = len(freq_files) > 0

        aq_str = str(aq_fluid) if pd.notna(aq_fluid) else "None"
        oil_str = str(oil_fluid) if pd.notna(oil_fluid) else "None"

        print(f"{i}. {device_id} at {flowrate}ml/hr + {pressure}mbar ({aq_str}_{oil_str})")
        print(f"   DFU rows: {unique_dfu_rows}, Frequency: {has_freq}")
        print()
    except Exception as e:
        print(f"{i}. ERROR: {e}")
        print(f"   Condition: {condition}")
        print()

print("="*50)
print("SCRIPT COMPLETED SUCCESSFULLY")
print("="*50)
