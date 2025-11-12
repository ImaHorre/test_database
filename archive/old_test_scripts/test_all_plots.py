"""
Quick test script to generate all plots from test data.

Run this to verify all configs and test data are working correctly.
"""

from src.plot_from_config import plot_from_config
from pathlib import Path


def main():
    """Generate all test plots."""

    test_cases = [
        {
            "csv": "data/test_plots/dfu_sweep_w13_5mlhr_300mbar.csv",
            "config": "configs/plots/dfu_sweep.json",
            "output": "outputs/plots/test_dfu_sweep.png",
            "name": "DFU Sweep"
        },
        {
            "csv": "data/test_plots/pressure_vs_droplet_w13.csv",
            "config": "configs/plots/pressure_vs_droplet.json",
            "output": "outputs/plots/test_pressure_vs_droplet.png",
            "name": "Pressure vs Droplet"
        },
        {
            "csv": "data/test_plots/flowrate_vs_droplet_w13.csv",
            "config": "configs/plots/flowrate_vs_droplet.json",
            "output": "outputs/plots/test_flowrate_vs_droplet.png",
            "name": "Flowrate vs Droplet"
        },
        {
            "csv": "data/test_plots/frequency_vs_pressure.csv",
            "config": "configs/plots/frequency_vs_pressure.json",
            "output": "outputs/plots/test_frequency_vs_pressure.png",
            "name": "Frequency vs Pressure"
        },
        {
            "csv": "data/test_plots/stability_over_time.csv",
            "config": "configs/plots/stability_over_time.json",
            "output": "outputs/plots/test_stability_over_time.png",
            "name": "Stability Over Time"
        },
        {
            "csv": "data/test_plots/device_type_comparison.csv",
            "config": "configs/plots/device_type_comparison.json",
            "output": "outputs/plots/test_device_type_comparison.png",
            "name": "Device Type Comparison"
        }
    ]

    print("="*60)
    print("Testing All Plot Configs")
    print("="*60)

    success_count = 0
    failed = []

    for i, test in enumerate(test_cases, 1):
        print(f"\n[{i}/{ len(test_cases)}] {test['name']}...")

        try:
            # Check if CSV exists
            if not Path(test['csv']).exists():
                print(f"   ⚠ CSV not found: {test['csv']}")
                failed.append(test['name'])
                continue

            # Check if config exists
            if not Path(test['config']).exists():
                print(f"   ⚠ Config not found: {test['config']}")
                failed.append(test['name'])
                continue

            # Generate plot
            plot_from_config(
                csv_path=test['csv'],
                config_path=test['config'],
                output_path=test['output']
            )

            success_count += 1
            print(f"   ✓ Success: {test['output']}")

        except Exception as e:
            print(f"   ✗ Failed: {e}")
            failed.append(test['name'])

    # Summary
    print("\n" + "="*60)
    print(f"Results: {success_count}/{len(test_cases)} plots generated successfully")

    if failed:
        print(f"\nFailed: {', '.join(failed)}")
    else:
        print("\n✓ All plots generated successfully!")

    print("="*60)

    return 0 if success_count == len(test_cases) else 1


if __name__ == '__main__':
    import sys
    sys.exit(main())
