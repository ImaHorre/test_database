"""
Database Scanner - Main Orchestration

This script coordinates all agents to scan local or cloud directories, extract metadata,
update the CSV database, and generate reports.

Supports:
- Local filesystem scanning (default)
- OneDrive cloud scanning via Microsoft Graph API
"""

import argparse
import logging
from datetime import datetime
from pathlib import Path

from src import LocalScanner, CloudScanner, MetadataExtractor, CSVManager, DataAnalyst

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def full_scan_and_update(source: str = 'local', local_path: str = None, sharing_link: str = None):
    """
    Perform full scan, extraction, and database update.

    This is the main workflow where all agents work together:
    1. Scanner discovers files (local or cloud)
    2. Extractor parses file paths to extract metadata
    3. CSV Manager updates the database
    4. Analyst generates summary reports

    Args:
        source: Source type - 'local' or 'cloud'
        local_path: Path to local directory to scan (required if source='local')
        sharing_link: OneDrive sharing link (required if source='cloud')
    """
    logger.info("🚀 Starting full scan and update...")

    # Step 1: Initialize agents
    logger.info("\n" + "="*70)
    logger.info("STEP 1: Initializing Agents")
    logger.info("="*70)

    # Initialize appropriate scanner based on source
    if source == 'local':
        if not local_path:
            logger.error("❌ Local path required for local scanning")
            return
        scanner = LocalScanner()
        logger.info(f"✓ Using LocalScanner for path: {local_path}")
    elif source == 'cloud':
        if not sharing_link:
            logger.error("❌ Sharing link required for cloud scanning")
            return
        scanner = CloudScanner()
        logger.info(f"✓ Using CloudScanner for OneDrive")
    else:
        logger.error(f"❌ Unknown source type: {source}")
        return

    extractor = MetadataExtractor()
    csv_manager = CSVManager()
    analyst = DataAnalyst(csv_manager)

    # Step 2: Scan directory (local or cloud)
    logger.info("\n" + "="*70)
    logger.info(f"STEP 2: Scanning {source.capitalize()} Directory")
    logger.info("="*70)

    if source == 'local':
        discovered_files = scanner.traverse_local_structure(local_path)
    else:  # cloud
        discovered_files = scanner.traverse_cloud_structure(sharing_link)

    logger.info(f"✓ Discovered {len(discovered_files)} files")

    if not discovered_files:
        logger.warning("⚠ No files found. Check your directory path.")
        return

    # Step 3: Extract metadata
    logger.info("\n" + "="*70)
    logger.info("STEP 3: Extracting Metadata")
    logger.info("="*70)

    file_paths = [f['path'] for f in discovered_files]
    metadata_list = extractor.batch_extract(file_paths, file_metadata=discovered_files)

    logger.info(f"✓ Extracted metadata from {len(metadata_list)} files")

    # Step 4: Update CSV database
    logger.info("\n" + "="*70)
    logger.info("STEP 4: Updating Database")
    logger.info("="*70)

    csv_manager.update_records(metadata_list)
    csv_manager.update_scan_timestamp()
    csv_manager.save()

    # Step 5: Generate reports
    logger.info("\n" + "="*70)
    logger.info("STEP 5: Generating Reports")
    logger.info("="*70)

    analyst.refresh_data()
    analyst.generate_summary_report()

    # Generate visualizations if we have data
    if len(analyst.df) > 0:
        device_types = analyst.df['device_type'].dropna().unique().tolist()
        if device_types:
            analyst.plot_device_type_comparison(device_types)

            for device_type in device_types:
                analyst.plot_flow_parameter_analysis(device_type,
                    output_path=f'outputs/flow_analysis_{device_type}.png')

    logger.info("\n" + "="*70)
    logger.info("✅ SCAN COMPLETE")
    logger.info("="*70)
    csv_manager.print_summary()


def query_database(device_type: str = None, flowrate: int = None, pressure: int = None):
    """
    Query the database with filters.

    Args:
        device_type: Filter by device type (e.g., 'W13')
        flowrate: Filter by aqueous flowrate
        pressure: Filter by oil pressure
    """
    analyst = DataAnalyst()

    logger.info("🔍 Querying database...")

    result = analyst.df.copy()

    if device_type:
        result = result[result['device_type'] == device_type]
        logger.info(f"  Filtered to device type: {device_type}")

    if flowrate is not None:
        result = result[result['aqueous_flowrate'] == flowrate]
        logger.info(f"  Filtered to flowrate: {flowrate} ml/hr")

    if pressure is not None:
        result = result[result['oil_pressure'] == pressure]
        logger.info(f"  Filtered to pressure: {pressure} mbar")

    logger.info(f"\n✓ Query returned {len(result)} records")

    if len(result) > 0:
        print("\n" + "="*70)
        print("QUERY RESULTS")
        print("="*70)
        print(result[['device_id', 'testing_date', 'aqueous_flowrate',
                      'oil_pressure', 'dfu_row', 'file_name']].to_string())
        print("="*70)
    else:
        print("\n⚠ No results found for query")


def main():
    """Main entry point with CLI arguments."""
    parser = argparse.ArgumentParser(
        description='Database Scanner - Microfluidic Device Measurement Tracking (Local & Cloud)'
    )

    parser.add_argument(
        'command',
        choices=['scan', 'query', 'report'],
        help='Command to run'
    )

    parser.add_argument(
        '--source',
        type=str,
        choices=['local', 'cloud'],
        default='local',
        help='Data source: local filesystem or OneDrive cloud (default: local)'
    )

    parser.add_argument(
        '--path',
        type=str,
        default='fake_onedrive_database',
        help='Path to local directory to scan (required if --source=local, default: fake_onedrive_database)'
    )

    parser.add_argument(
        '--sharing-link',
        type=str,
        help='OneDrive sharing link to root folder (required if --source=cloud)'
    )

    parser.add_argument('--device-type', type=str, help='Filter by device type (e.g., W13)')
    parser.add_argument('--flowrate', type=int, help='Filter by aqueous flowrate (ml/hr)')
    parser.add_argument('--pressure', type=int, help='Filter by oil pressure (mbar)')

    args = parser.parse_args()

    try:
        if args.command == 'scan':
            full_scan_and_update(
                source=args.source,
                local_path=args.path,
                sharing_link=args.sharing_link
            )

        elif args.command == 'query':
            query_database(
                device_type=args.device_type,
                flowrate=args.flowrate,
                pressure=args.pressure
            )

        elif args.command == 'report':
            analyst = DataAnalyst()
            analyst.generate_summary_report()
            analyst.manager.print_summary()

    except Exception as e:
        logger.error(f"❌ Error: {e}", exc_info=True)
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
