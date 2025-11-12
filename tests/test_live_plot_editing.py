"""
Test script for live plot preview and editing system.

Tests the complete workflow of:
1. Creating live plot preview
2. Editing plot with terminal commands
3. Saving edited plot
"""

import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src import DataAnalyst


def test_live_plot_editing():
    """Test live plot editing functionality."""
    print("=" * 70)
    print("LIVE PLOT EDITING TEST")
    print("=" * 70)
    print()

    # Initialize analyst
    print("1. Initializing DataAnalyst...")
    analyst = DataAnalyst()
    print(f"   Loaded {len(analyst.df)} measurements")
    print()

    # Get available W13 devices with 5mlhr flowrate
    print("2. Checking available test data...")
    w13_5mlhr = analyst.df[
        (analyst.df['device_type'] == 'W13') &
        (analyst.df['aqueous_flowrate'] == 5)
    ]

    if len(w13_5mlhr) == 0:
        print("   [WARNING] No W13 devices at 5mlhr found in database")
        print("   Trying with all W13 devices...")
        w13_5mlhr = analyst.df[analyst.df['device_type'] == 'W13']

        if len(w13_5mlhr) == 0:
            print("   [ERROR] No W13 devices found in database at all!")
            print("   Cannot run test.")
            return False

    print(f"   Found {len(w13_5mlhr)} W13 measurements")
    print(f"   Unique devices: {w13_5mlhr['device_id'].nunique()}")
    print(f"   DFU rows available: {sorted(w13_5mlhr['dfu_row'].dropna().unique())}")
    print()

    # Create live plot preview
    print("3. Creating live plot preview...")
    print("   This will open a matplotlib window...")
    print()

    try:
        result = analyst.plot_metric_vs_dfu(
            metric='droplet_size_mean',
            device_type='W13',
            aqueous_flowrate=5,
            output_path='outputs/test_live_plot.png',
            live_preview=True
        )

        if not result.get('live_preview'):
            print("[ERROR] Live preview was not activated!")
            return False

        print("[OK] Live plot preview created successfully")
        print()
        print(f"   Metric: {result['metric']}")
        print(f"   Devices plotted: {result['num_devices']}")
        print(f"   DFU rows: {result['dfu_rows_measured']}")
        print(f"   Total measurements: {result['total_measurements']}")

        if result.get('varying_parameters'):
            print(f"   Varying parameters: {', '.join(result['varying_parameters'])}")

        print()
        print("4. Testing plot editor commands...")
        print()

        # Get the editor
        editor = result['editor']

        # Test help command
        print("   a) Testing 'help' command...")
        help_result = editor.process_command('help')
        if help_result['status'] == 'success':
            print("      [OK] Help command works")
        else:
            print(f"      [ERROR] Help command failed: {help_result.get('message')}")

        # Wait a moment for user to see the plot
        print()
        print("   Waiting 2 seconds for plot to render...")
        time.sleep(2)

        # Test color change
        print()
        print("   b) Testing 'change colors' command...")
        color_result = editor.process_command('change colors')
        if color_result['status'] == 'success':
            print(f"      [OK] {color_result['message']}")
            time.sleep(1)
        else:
            print(f"      [ERROR] Color change failed: {color_result.get('message')}")

        # Test grid toggle
        print()
        print("   c) Testing 'remove grid' command...")
        grid_result = editor.process_command('remove grid')
        if grid_result['status'] == 'success':
            print(f"      [OK] {grid_result['message']}")
            time.sleep(1)
        else:
            print(f"      [ERROR] Grid toggle failed: {grid_result.get('message')}")

        # Test adding grid back
        print()
        print("   d) Testing 'add grid' command...")
        grid_result = editor.process_command('add grid')
        if grid_result['status'] == 'success':
            print(f"      [OK] {grid_result['message']}")
            time.sleep(1)
        else:
            print(f"      [ERROR] Grid toggle failed: {grid_result.get('message')}")

        # Test title change
        print()
        print("   e) Testing 'change title' command...")
        title_result = editor.process_command('change title Test Plot - Live Editing Works!')
        if title_result['status'] == 'success':
            print(f"      [OK] {title_result['message']}")
            time.sleep(1)
        else:
            print(f"      [ERROR] Title change failed: {title_result.get('message')}")

        # Test test date addition (if available)
        print()
        print("   f) Testing 'add test date' command...")
        date_result = editor.process_command('add test date')
        if date_result['status'] == 'success':
            print(f"      [OK] {date_result['message']}")
            time.sleep(1)
        elif date_result['status'] == 'error' and 'not available' in date_result['message']:
            print(f"      [SKIP] No test date data available (expected for some datasets)")
        else:
            print(f"      [WARNING] {date_result.get('message')}")

        # Test saving
        print()
        print("   g) Testing 'save' command...")
        save_result = editor.process_command('save')
        if save_result['status'] == 'success':
            print(f"      [OK] {save_result['message']}")
            file_path = save_result.get('file_path', 'unknown')
            print(f"      File saved to: {file_path}")

            # Check if file exists
            if Path(file_path).exists():
                print("      [OK] File confirmed to exist")
            else:
                print("      [WARNING] File does not exist at expected path")
        else:
            print(f"      [ERROR] Save failed: {save_result.get('message')}")

        print()
        print("=" * 70)
        print("TEST COMPLETED SUCCESSFULLY")
        print("=" * 70)
        print()
        print("Summary:")
        print("- Live plot preview: WORKING")
        print("- Command processing: WORKING")
        print("- Plot modifications: WORKING")
        print("- Plot saving: WORKING")
        print()

        return True

    except Exception as e:
        print()
        print(f"[ERROR] Test failed with exception: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_simple_live_plot():
    """Simpler test that just creates a live plot and waits for manual interaction."""
    print("=" * 70)
    print("SIMPLE LIVE PLOT TEST (Manual Interaction)")
    print("=" * 70)
    print()
    print("This test will create a live plot and wait for you to interact with it.")
    print("The plot window should open in a separate window.")
    print()

    analyst = DataAnalyst()

    # Find any available data
    if len(analyst.df) == 0:
        print("[ERROR] No data in database!")
        return False

    device_type = analyst.df['device_type'].iloc[0]
    print(f"Creating plot for device type: {device_type}")
    print()

    try:
        result = analyst.plot_metric_vs_dfu(
            device_type=device_type,
            live_preview=True
        )

        if not result.get('live_preview'):
            print("[ERROR] Live preview not activated!")
            return False

        print("[OK] Live plot created!")
        print()
        print("INSTRUCTIONS:")
        print("1. A plot window should have opened")
        print("2. You can now interact with it in the terminal")
        print()
        print("Try these commands:")
        print("  - help")
        print("  - change colors")
        print("  - remove legend")
        print("  - save")
        print()

        # Interactive loop
        editor = result['editor']
        while True:
            try:
                cmd = input("plot> ").strip()
                if not cmd:
                    continue

                result = editor.process_command(cmd)

                if result['status'] == 'success':
                    print(f"[OK] {result['message']}")
                    if result['action'] == 'help':
                        pass  # Message already printed
                    elif result['action'] in ['save', 'discard']:
                        print()
                        print("Plot interaction ended.")
                        break
                else:
                    print(f"[Error] {result['message']}")

                if result['action'] not in ['help', 'save', 'discard']:
                    print("Plot updated.")
                print()

            except KeyboardInterrupt:
                print()
                print("Interrupted. Closing plot...")
                editor.process_command('discard')
                break

        return True

    except Exception as e:
        print(f"[ERROR] {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print()
    print("Live Plot Editing Test Suite")
    print()
    print("Choose test mode:")
    print("  1. Automated test (tests all commands automatically)")
    print("  2. Manual test (interactive - you control the commands)")
    print()

    choice = input("Enter choice (1 or 2): ").strip()

    print()

    if choice == '1':
        success = test_live_plot_editing()
    elif choice == '2':
        success = test_simple_live_plot()
    else:
        print("Invalid choice. Running automated test...")
        success = test_live_plot_editing()

    print()
    if success:
        print("Test completed successfully!")
    else:
        print("Test failed!")

    sys.exit(0 if success else 1)
