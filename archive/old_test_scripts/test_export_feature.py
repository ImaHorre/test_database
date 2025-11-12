"""
Test script to verify CSV export functionality in dashboard_v2.py
"""

import sys
import pandas as pd
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from dashboard_v2 import SimpleDashboard

def test_export_feature():
    """Test the CSV export feature with different filter scenarios."""

    print("=" * 70)
    print("TESTING CSV EXPORT FEATURE")
    print("=" * 70)
    print()

    # Initialize dashboard
    print("[1] Initializing dashboard...")
    dashboard = SimpleDashboard()
    print("[OK] Dashboard initialized")
    print()

    # Test 1: Export with device type filter
    print("-" * 70)
    print("TEST 1: Export with device_type filter (W13)")
    print("-" * 70)
    dashboard.session_state['current_filters'] = {'device_type': 'W13'}
    dashboard._cmd_export_csv()

    # Test 2: Export with device type + flowrate filter
    print("-" * 70)
    print("TEST 2: Export with device_type + flowrate filter (W13 at 5mlhr)")
    print("-" * 70)
    dashboard.session_state['current_filters'] = {'device_type': 'W13', 'flowrate': 5}
    dashboard._cmd_export_csv()

    # Test 3: Export with device type + flowrate + pressure filter
    print("-" * 70)
    print("TEST 3: Export with device_type + flowrate + pressure filter (W13 at 10mlhr 200mbar)")
    print("-" * 70)
    dashboard.session_state['current_filters'] = {'device_type': 'W13', 'flowrate': 10, 'pressure': 200}
    dashboard._cmd_export_csv()

    # Test 4: Export with no filters (entire database)
    print("-" * 70)
    print("TEST 4: Export entire database (no filters)")
    print("-" * 70)
    dashboard.session_state['current_filters'] = {}
    dashboard._cmd_export_csv()

    # Verify exports exist
    print()
    print("=" * 70)
    print("VERIFICATION: Checking exported files")
    print("=" * 70)
    output_dir = Path('outputs')
    export_files = sorted(output_dir.glob('*_export_*.csv'))

    if export_files:
        print(f"\n[OK] Found {len(export_files)} export files:")
        for i, file in enumerate(export_files[-4:], 1):  # Show last 4 files
            size_kb = file.stat().st_size / 1024
            print(f"  {i}. {file.name} ({size_kb:.1f} KB)")

            # Verify CSV is valid
            try:
                df = pd.read_csv(file)
                print(f"     -> Valid CSV with {len(df)} rows, {len(df.columns)} columns")
            except Exception as e:
                print(f"     -> [ERROR] Could not read CSV: {e}")
    else:
        print("\n[WARNING] No export files found in outputs/ directory")

    print()
    print("=" * 70)
    print("TEST COMPLETE")
    print("=" * 70)

if __name__ == "__main__":
    test_export_feature()
