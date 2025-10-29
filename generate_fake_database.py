"""
Generate fake OneDrive database structure for testing.

Creates a realistic folder structure with random data matching the real format.
"""

import os
import random
from pathlib import Path
from datetime import datetime, timedelta


def generate_droplet_csv(output_path: str, device_type: str, num_droplets: int = 50):
    """
    Generate fake droplet annotation CSV matching real format.

    W14: 10-15um droplets
    W13: 20-30um droplets

    Args:
        output_path: Full path including filename
        device_type: W13 or W14
        num_droplets: Number of droplet rows to generate
    """
    # Droplet size range based on device type
    if device_type == "W14":
        diameter_range = (10, 15)
    else:  # W13
        diameter_range = (20, 30)

    with open(output_path, 'w') as f:
        # Header
        f.write("droplet_id,roi_id,frame,center_x,center_y,radius_px,diameter_um,magnification,pixels_per_um\n")

        # Generate random droplet data
        for i in range(1, num_droplets + 1):
            droplet_id = i
            roi_id = random.randint(1, 5)  # ROIs 1-5
            frame = random.randint(1, 300)
            center_x = random.uniform(100, 800)
            center_y = random.uniform(100, 900)
            diameter_um = random.uniform(*diameter_range)
            radius_px = diameter_um / 2 * 1.425  # pixels_per_um = 1.425
            magnification = "10x"
            pixels_per_um = 1.425

            f.write(f"{droplet_id},{roi_id},{frame},{center_x:.2f},{center_y:.2f},"
                   f"{radius_px:.2f},{diameter_um:.6f},{magnification},{pixels_per_um}\n")


def generate_frequency_txt(output_path: str, roi_num: int):
    """
    Generate fake frequency analysis TXT matching real format.

    Frequencies: 1-20 Hz
    """
    freq = random.uniform(1, 20)
    num_events = random.randint(3, 10)
    fps = 25

    # Generate formation event frames
    frames = sorted([random.randint(1, 500) for _ in range(num_events)])
    cycle_lengths = [frames[i+1] - frames[i] for i in range(len(frames)-1)]
    avg_cycle_length = sum(cycle_lengths) / len(cycle_lengths) if cycle_lengths else 80
    avg_cycle_time = avg_cycle_length / fps

    with open(output_path, 'w') as f:
        f.write(f"Droplet Frequency Analysis - ROI {roi_num}\n")
        f.write("=" * 50 + "\n\n")
        f.write("Analysis Parameters:\n")
        f.write(f"  Effective FPS: {fps}\n")
        f.write(f"  Formation events recorded: {num_events}\n")
        f.write(f"  Number of cycles: {len(cycle_lengths)}\n\n")
        f.write(f"Formation Event Frames: {frames}\n")
        f.write(f"Cycle Lengths (frames): {cycle_lengths}\n")
        f.write(f"Individual Frequencies: {[f'{freq:.2f}' for _ in cycle_lengths]} Hz\n\n")
        f.write("Results:\n")
        f.write(f"  Average Cycle Length: {avg_cycle_length:.1f} frames ({avg_cycle_time:.3f} seconds)\n")
        f.write(f"  Frequency Method 1 (avg of frequencies): {freq:.2f} Hz\n")
        f.write(f"  Frequency Method 2 (freq from avg time): {freq:.2f} Hz\n")

        if len(cycle_lengths) == 1:
            f.write("  Note: Only one cycle measured, no variability statistics\n")


def generate_fake_database(base_path: str = "fake_onedrive_database"):
    """
    Generate complete fake database structure.

    Structure:
    - 5 devices (mix of W13 and W14)
    - 1 bonding date per device
    - 1-2 testing dates per device
    - Random flow parameters
    - 6 DFU CSVs per dfu_measure folder
    - 30 TXT files per freq_analysis folder (6 DFUs * 5 ROIs)
    """
    base = Path(base_path)
    base.mkdir(exist_ok=True)

    # Device configurations
    devices = [
        ("W13", 1, 1),
        ("W13", 1, 2),
        ("W14", 2, 1),
        ("W14", 1, 3),
        ("W13", 2, 2),
    ]

    # Flow parameter ranges
    flowrates = list(range(5, 51, 5))  # 5, 10, 15, ..., 50 ml/hr
    pressures = list(range(50, 401, 50))  # 50, 100, 150, ..., 400 mbar

    fluids = ["NaCas_SO", "SDS_SO"]

    print(f"Generating fake database at: {base.absolute()}\n")

    for device_type, shim, replica in devices:
        device_id = f"{device_type}_S{shim}_R{replica}"

        # Random bonding date (last 3 months)
        bonding_date = datetime.now() - timedelta(days=random.randint(30, 90))
        bonding_str_long = bonding_date.strftime("%d%m%Y")
        bonding_str_short = bonding_date.strftime("%d%m")

        # Use short format 50% of the time
        bonding_str = bonding_str_short if random.random() < 0.5 else bonding_str_long

        device_path = base / device_id / bonding_str

        # 1-2 testing dates per device
        num_test_dates = random.randint(1, 2)

        for _ in range(num_test_dates):
            # Testing date is after bonding
            testing_date = bonding_date + timedelta(days=random.randint(1, 30))
            testing_str_long = testing_date.strftime("%d%m%Y")
            testing_str_short = testing_date.strftime("%d%m")

            # Use short format 50% of the time
            testing_str = testing_str_short if random.random() < 0.5 else testing_str_long

            # Sometimes skip testing date folder (30% chance)
            if random.random() < 0.3:
                test_path = device_path
            else:
                test_path = device_path / testing_str

            # Random fluid (50% chance to include)
            fluid = None  # Initialize to avoid UnboundLocalError
            if random.random() < 0.5:
                fluid = random.choice(fluids)
                fluid_path = test_path / fluid
            else:
                fluid_path = test_path

            # 2-3 random flow parameter combinations per test date
            num_params = random.randint(2, 3)

            for _ in range(num_params):
                flowrate = random.choice(flowrates)
                pressure = random.choice(pressures)
                flow_str = f"{flowrate}mlhr{pressure}mbar"

                flow_path = fluid_path / flow_str

                # Create dfu_measure folder
                dfu_path = flow_path / "dfu_measure"
                dfu_path.mkdir(parents=True, exist_ok=True)

                # Build filename components
                bonding_short = bonding_date.strftime("%d%m")
                testing_short = testing_date.strftime("%d%m")
                device_id_lower = device_id.lower()
                fluid_compact = fluid.replace("_", "").lower() if fluid and random.random() < 0.5 else ""
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

                # Create 6 DFU CSV files
                for dfu_num in range(1, 7):
                    # Filename format: BBDD_TTDD_device_fluids_flow_DFUx_B_t0_droplet_annotations_timestamp.csv
                    csv_filename = f"{bonding_short}_{testing_short}_{device_id_lower}_{flow_str}"
                    if fluid_compact:
                        csv_filename += f"_{fluid_compact}"
                    csv_filename += f"_DFU{dfu_num}_B_t0_droplet_annotations_{timestamp}.csv"

                    csv_file = dfu_path / csv_filename
                    generate_droplet_csv(str(csv_file), device_type)
                    print(f"  ✓ {csv_file.relative_to(base)}")

                # Create freq_analysis folder
                freq_path = flow_path / "freq_analysis"
                freq_path.mkdir(parents=True, exist_ok=True)

                # Create 30 TXT files (6 DFUs * 5 ROIs)
                for dfu_num in range(1, 7):
                    for roi_num in range(1, 6):
                        # Filename format: BBDD_TTDD_device_fluids_flow_DFUx_B_t0_ROIx_frequency_analysis.txt
                        txt_filename = f"{bonding_short}_{testing_short}_{device_id_lower}_{flow_str}"
                        if fluid_compact:
                            txt_filename += f"_{fluid_compact}"
                        txt_filename += f"_DFU{dfu_num}_B_t0_ROI{roi_num}_frequency_analysis.txt"

                        txt_file = freq_path / txt_filename
                        generate_frequency_txt(str(txt_file), roi_num)
                        print(f"  ✓ {txt_file.relative_to(base)}")

    print(f"\n✅ Fake database generated at: {base.absolute()}")
    print(f"\nStructure summary:")
    print(f"  - Devices: {len(devices)}")

    # Count files
    csv_count = len(list(base.rglob("*.csv")))
    txt_count = len(list(base.rglob("*.txt")))

    print(f"  - CSV files: {csv_count}")
    print(f"  - TXT files: {txt_count}")
    print(f"  - Total files: {csv_count + txt_count}")


if __name__ == "__main__":
    generate_fake_database()
