"""Test if pandas GroupBy skips NaN values."""
import pandas as pd
import numpy as np

# Create test dataframe with NaN in groupby column
df = pd.DataFrame({
    'device': ['A', 'B'],
    'test_date': ['2025-01-01', np.nan],
    'value': [1, 2]
})

print("DataFrame:")
print(df)
print()

# Group by device and test_date
groups = df.groupby(['device', 'test_date'])

print(f"Number of groups (len): {len(groups)}")
print(f"Groups keys: {list(groups.groups.keys())}")
print()

print("Iterating through groups:")
for i, (key, group) in enumerate(groups, 1):
    print(f"  Group {i}: {key}")

print("\nDone!")
