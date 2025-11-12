"""
Generate filtered test CSV files for plot config testing.

This script creates sample datasets for each plot preset by filtering
the main database.csv with appropriate criteria.
"""

import pandas as pd
from pathlib import Path
import sys

# Fix Windows console encoding for Unicode characters
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')


def main():
    """Generate all test datasets."""

    # Load main database
    db_path = Path("data/database.csv")
    if not db_path.exists():
        print(f"❌ Database not found: {db_path}")
        return 1

    df = pd.read_csv(db_path)
    print(f"✓ Loaded database: {len(df)} rows")

    output_dir = Path("data/test_plots")
    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. DFU Sweep - W13 devices at 5ml/hr, 300mbar with droplet measurements
    print("\n1. Generating DFU sweep test data...")
    dfu_df = df[
        (df['device_type'] == 'W13') &
        (df['aqueous_flowrate'] == 5.0) &
        (df['oil_pressure'] == 300.0) &
        (df['measurement_type'] == 'dfu_measure') &
        (df['droplet_size_mean'].notna())
    ].copy()

    if len(dfu_df) > 0:
        output_path = output_dir / "dfu_sweep_w13_5mlhr_300mbar.csv"
        dfu_df.to_csv(output_path, index=False)
        print(f"   ✓ Saved: {output_path} ({len(dfu_df)} rows)")
        print(f"   Devices: {dfu_df['device_id'].unique().tolist()}")
        print(f"   DFU rows: {sorted(dfu_df['dfu_row'].dropna().unique().tolist())}")
    else:
        print("   ⚠ No data found for DFU sweep")

    # 2. Pressure vs Droplet - Multiple pressures, W13 devices
    print("\n2. Generating pressure vs droplet test data...")
    pressure_df = df[
        (df['device_type'] == 'W13') &
        (df['measurement_type'] == 'dfu_measure') &
        (df['droplet_size_mean'].notna()) &
        (df['oil_pressure'].notna())
    ].copy()

    if len(pressure_df) > 0:
        output_path = output_dir / "pressure_vs_droplet_w13.csv"
        pressure_df.to_csv(output_path, index=False)
        print(f"   ✓ Saved: {output_path} ({len(pressure_df)} rows)")
        print(f"   Devices: {pressure_df['device_id'].unique().tolist()}")
        print(f"   Pressures: {sorted(pressure_df['oil_pressure'].unique().tolist())}")
    else:
        print("   ⚠ No data found for pressure analysis")

    # 3. Flowrate vs Droplet - Multiple flowrates, W13 devices
    print("\n3. Generating flowrate vs droplet test data...")
    flowrate_df = df[
        (df['device_type'] == 'W13') &
        (df['measurement_type'] == 'dfu_measure') &
        (df['droplet_size_mean'].notna()) &
        (df['aqueous_flowrate'].notna())
    ].copy()

    if len(flowrate_df) > 0:
        output_path = output_dir / "flowrate_vs_droplet_w13.csv"
        flowrate_df.to_csv(output_path, index=False)
        print(f"   ✓ Saved: {output_path} ({len(flowrate_df)} rows)")
        print(f"   Devices: {flowrate_df['device_id'].unique().tolist()}")
        print(f"   Flowrates: {sorted(flowrate_df['aqueous_flowrate'].unique().tolist())}")
    else:
        print("   ⚠ No data found for flowrate analysis")

    # 4. Frequency vs Pressure - Frequency measurements with pressure variation
    print("\n4. Generating frequency vs pressure test data...")
    freq_df = df[
        (df['measurement_type'] == 'freq_analysis') &
        (df['frequency_mean'].notna()) &
        (df['oil_pressure'].notna())
    ].copy()

    if len(freq_df) > 0:
        output_path = output_dir / "frequency_vs_pressure.csv"
        freq_df.to_csv(output_path, index=False)
        print(f"   ✓ Saved: {output_path} ({len(freq_df)} rows)")
        print(f"   Devices: {freq_df['device_id'].unique().tolist()}")
        print(f"   Pressures: {sorted(freq_df['oil_pressure'].unique().tolist())}")
    else:
        print("   ⚠ No data found for frequency analysis")

    # 5. Stability Over Time - Multiple testing dates
    print("\n5. Generating stability over time test data...")
    stability_df = df[
        (df['measurement_type'] == 'dfu_measure') &
        (df['droplet_size_mean'].notna()) &
        (df['testing_date'].notna())
    ].copy()

    # Filter to devices with multiple test dates
    date_counts = stability_df.groupby('device_id')['testing_date'].nunique()
    multi_date_devices = date_counts[date_counts > 1].index.tolist()

    if len(multi_date_devices) > 0:
        stability_df = stability_df[stability_df['device_id'].isin(multi_date_devices)]
        output_path = output_dir / "stability_over_time.csv"
        stability_df.to_csv(output_path, index=False)
        print(f"   ✓ Saved: {output_path} ({len(stability_df)} rows)")
        print(f"   Devices: {multi_date_devices}")
        print(f"   Date range: {stability_df['testing_date'].min()} to {stability_df['testing_date'].max()}")
    else:
        # Fallback: use all data even if single dates
        if len(stability_df) > 0:
            output_path = output_dir / "stability_over_time.csv"
            stability_df.to_csv(output_path, index=False)
            print(f"   ✓ Saved: {output_path} ({len(stability_df)} rows)")
            print(f"   ⚠ Note: May have single test dates per device")
        else:
            print("   ⚠ No data found for stability analysis")

    # 6. Device Type Comparison - W13 vs W14
    print("\n6. Generating device type comparison test data...")
    comparison_df = df[
        (df['device_type'].isin(['W13', 'W14'])) &
        (df['measurement_type'] == 'dfu_measure') &
        (df['droplet_size_mean'].notna()) &
        (df['oil_pressure'].notna())
    ].copy()

    if len(comparison_df) > 0:
        # Check if we have both types
        types_available = comparison_df['device_type'].unique()
        output_path = output_dir / "device_type_comparison.csv"
        comparison_df.to_csv(output_path, index=False)
        print(f"   ✓ Saved: {output_path} ({len(comparison_df)} rows)")
        print(f"   Device types: {types_available.tolist()}")

        for dtype in types_available:
            type_df = comparison_df[comparison_df['device_type'] == dtype]
            print(f"   {dtype}: {type_df['device_id'].nunique()} devices, {len(type_df)} measurements")
    else:
        print("   ⚠ No data found for device comparison")

    print("\n" + "="*60)
    print("✓ Test data generation complete!")
    print(f"Output directory: {output_dir.absolute()}")
    print("="*60)

    return 0


if __name__ == '__main__':
    exit(main())
