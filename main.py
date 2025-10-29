"""
OneDrive Database Scanner - Main Orchestration

This script coordinates all agents to scan SharePoint, extract metadata,
update the CSV database, and generate reports.
"""

import argparse
import logging
from datetime import datetime
from pathlib import Path

from src import SharePointScanner, MetadataExtractor, CSVManager, DataAnalyst

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def full_scan_and_update():
    """
    Perform full scan, extraction, and database update.

    This is the main workflow where all agents work together:
    1. Scanner discovers files in SharePoint
    2. Extractor parses file paths to extract metadata
    3. CSV Manager updates the database
    4. Analyst generates summary reports
    """
    logger.info("🚀 Starting full scan and update...")

    # Step 1: Initialize agents
    logger.info("\n" + "="*70)
    logger.info("STEP 1: Initializing Agents")
    logger.info("="*70)

    scanner = SharePointScanner()
    extractor = MetadataExtractor()
    csv_manager = CSVManager()
    analyst = DataAnalyst(csv_manager)

    # Step 2: Scan SharePoint
    logger.info("\n" + "="*70)
    logger.info("STEP 2: Scanning SharePoint")
    logger.info("="*70)

    discovered_files = scanner.traverse_structure()
    logger.info(f"✓ Discovered {len(discovered_files)} files")

    if not discovered_files:
        logger.warning("⚠ No files found. Check your SharePoint path and permissions.")
        return

    # Step 3: Extract metadata
    logger.info("\n" + "="*70)
    logger.info("STEP 3: Extracting Metadata")
    logger.info("="*70)

    file_paths = [f['path'] for f in discovered_files]
    metadata_list = extractor.batch_extract(file_paths, file_metadata=discovered_files)

    # Add file URLs to metadata (for reference)
    for i, metadata in enumerate(metadata_list):
        if i < len(discovered_files):
            metadata['download_url'] = discovered_files[i].get('download_url')
            metadata['web_url'] = discovered_files[i].get('webUrl')

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


def incremental_update():
    """
    Perform incremental update (only check changed files since last scan).
    """
    logger.info("🔄 Starting incremental update...")

    csv_manager = CSVManager()
    last_scan = csv_manager.get_last_scan_timestamp()

    if not last_scan:
        logger.warning("⚠ No previous scan found. Running full scan instead.")
        full_scan_and_update()
        return

    logger.info(f"📅 Last scan: {last_scan}")

    scanner = SharePointScanner()
    extractor = MetadataExtractor()

    # Get only changed files
    changed_files = scanner.get_changed_files_since(last_scan)
    logger.info(f"✓ Found {len(changed_files)} changed files")

    if not changed_files:
        logger.info("✓ No changes detected. Database is up to date.")
        return

    # Extract and update
    file_paths = [f['path'] for f in changed_files]
    metadata_list = extractor.batch_extract(file_paths, file_metadata=changed_files)

    csv_manager.update_records(metadata_list)
    csv_manager.update_scan_timestamp()
    csv_manager.save()

    logger.info("✅ Incremental update complete")


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
        description='OneDrive Database Scanner - Microfluidic Device Measurement Tracking'
    )

    parser.add_argument(
        'command',
        choices=['scan', 'update', 'query', 'report'],
        help='Command to run'
    )

    parser.add_argument('--device-type', type=str, help='Filter by device type (e.g., W13)')
    parser.add_argument('--flowrate', type=int, help='Filter by aqueous flowrate (ml/hr)')
    parser.add_argument('--pressure', type=int, help='Filter by oil pressure (mbar)')

    args = parser.parse_args()

    try:
        if args.command == 'scan':
            full_scan_and_update()

        elif args.command == 'update':
            incremental_update()

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
