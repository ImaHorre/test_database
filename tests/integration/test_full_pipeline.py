"""
Full Pipeline Integration Test

Tests the complete Scanner → Extractor → CSV Manager pipeline.
Uses fake_onedrive_database for testing without SharePoint access.

Validates:
1. Scanner discovers all files from fake database
2. Extractor extracts metadata from paths and file content
3. CSV Manager loads data into database
4. Data integrity preserved (no loss, no duplicates)
5. Parse quality tracking works
6. Area/timepoint fields properly populated
"""

import os
import sys
import logging
import json
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.scanner import LocalScanner
from src.extractor import MetadataExtractor
from src.csv_manager import CSVManager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def validate_csv_output(csv_manager: CSVManager) -> dict:
    """
    Validate CSV output data integrity.

    Checks:
    - No duplicate records
    - No data loss (droplet/frequency stats)
    - Schema matches expected columns
    - Area/timepoint fields populated
    - Parse quality tracking works
    """
    logger.info("\n" + "="*70)
    logger.info("VALIDATION: CSV Output Integrity")
    logger.info("="*70)

    results = {
        'total_records': len(csv_manager.df),
        'issues': [],
        'warnings': [],
        'checks_passed': 0,
        'checks_total': 0
    }

    if len(csv_manager.df) == 0:
        results['issues'].append("No records loaded into CSV")
        return results

    df = csv_manager.df

    # Check 1: No duplicates by raw_path
    results['checks_total'] += 1
    duplicates = df[df.duplicated(subset=['raw_path'], keep=False)]
    if len(duplicates) > 0:
        results['issues'].append(f"Found {len(duplicates)} duplicate records by raw_path")
    else:
        results['warnings'].append("✓ No duplicate records detected")
        results['checks_passed'] += 1

    # Check 2: Schema completeness
    results['checks_total'] += 1
    missing_cols = [col for col in CSVManager.COLUMNS if col not in df.columns]
    if missing_cols:
        results['issues'].append(f"Missing columns: {missing_cols}")
    else:
        results['warnings'].append(f"✓ All {len(CSVManager.COLUMNS)} schema columns present")
        results['checks_passed'] += 1

    # Check 3: File type distribution
    results['checks_total'] += 1
    csv_files = df[df['file_type'] == 'csv']
    txt_files = df[df['file_type'] == 'txt']
    results['csv_files'] = len(csv_files)
    results['txt_files'] = len(txt_files)

    if len(csv_files) > 0 and len(txt_files) > 0:
        results['warnings'].append(
            f"✓ Both file types present: {len(csv_files)} CSV, {len(txt_files)} TXT"
        )
        results['checks_passed'] += 1
    else:
        results['issues'].append(f"Incomplete file types: CSV={len(csv_files)}, TXT={len(txt_files)}")

    # Check 4: Droplet data preservation (CSV files)
    results['checks_total'] += 1
    csv_with_droplet_data = csv_files[csv_files['droplet_size_mean'].notna()]
    if len(csv_with_droplet_data) > 0:
        results['warnings'].append(
            f"✓ Droplet data preserved: {len(csv_with_droplet_data)} CSV files with measurements"
        )
        results['checks_passed'] += 1
    else:
        results['warnings'].append("⚠ No droplet data in CSV files (check if content was parsed)")

    # Check 5: Frequency data preservation (TXT files)
    results['checks_total'] += 1
    txt_with_freq_data = txt_files[txt_files['frequency_mean'].notna()]
    if len(txt_with_freq_data) > 0:
        results['warnings'].append(
            f"✓ Frequency data preserved: {len(txt_with_freq_data)} TXT files with measurements"
        )
        results['checks_passed'] += 1
    else:
        results['warnings'].append("⚠ No frequency data in TXT files (check if content was parsed)")

    # Check 6: Parse quality tracking
    results['checks_total'] += 1
    parse_quality_counts = df['parse_quality'].value_counts().to_dict()
    results['parse_quality'] = parse_quality_counts

    if parse_quality_counts:
        quality_str = ', '.join([f"{k}:{v}" for k, v in sorted(parse_quality_counts.items())])
        results['warnings'].append(f"✓ Parse quality tracked: {quality_str}")
        results['checks_passed'] += 1
    else:
        results['issues'].append("No parse quality data recorded")

    # Check 7: Metadata field completeness
    results['checks_total'] += 1
    required_metadata = ['device_type', 'bonding_date', 'aqueous_flowrate', 'oil_pressure']
    missing_metadata = [field for field in required_metadata
                       if df[field].isna().sum() > len(df) * 0.5]  # More than 50% missing

    if not missing_metadata:
        results['warnings'].append(f"✓ Key metadata fields populated: {', '.join(required_metadata)}")
        results['checks_passed'] += 1
    else:
        results['issues'].append(f"Metadata fields >50% empty: {missing_metadata}")

    # Check 8: Area and timepoint fields
    results['checks_total'] += 1
    area_populated = df['measurement_area'].notna().sum()
    timepoint_populated = df['timepoint'].notna().sum()

    if area_populated > 0 or timepoint_populated > 0:
        results['warnings'].append(
            f"✓ Measurement fields: area={area_populated}, timepoint={timepoint_populated}"
        )
        results['checks_passed'] += 1
    else:
        results['warnings'].append("⚠ Area and timepoint fields empty (may be expected)")

    # Check 9: Device type and DFU row variety
    results['checks_total'] += 1
    device_types = df['device_type'].nunique()
    unique_devices = df['device_id'].nunique()
    dfu_rows = df['dfu_row'].nunique()

    if device_types > 1 and unique_devices > 1:
        results['warnings'].append(
            f"✓ Device diversity: {device_types} types, {unique_devices} unique IDs, {dfu_rows} DFU rows"
        )
        results['checks_passed'] += 1
    else:
        results['issues'].append(
            f"Low device diversity: {device_types} types, {unique_devices} unique IDs"
        )

    return results


def print_sample_records(csv_manager: CSVManager, num_samples: int = 5):
    """Print sample records from the CSV."""
    if len(csv_manager.df) == 0:
        logger.info("⚠ No records to display")
        return

    logger.info("\n" + "="*70)
    logger.info(f"SAMPLE RECORDS (First {num_samples})")
    logger.info("="*70)

    # Select key columns for display
    display_cols = [
        'device_id', 'bonding_date', 'testing_date',
        'aqueous_flowrate', 'oil_pressure', 'dfu_row',
        'measurement_type', 'file_type', 'parse_quality'
    ]

    # Filter to columns that exist
    existing_cols = [col for col in display_cols if col in csv_manager.df.columns]

    sample = csv_manager.df.head(num_samples)[existing_cols]
    logger.info("\n" + sample.to_string())


def main():
    """Run the full pipeline integration test."""
    start_time = datetime.now()

    logger.info("\n" + "="*80)
    logger.info("FULL PIPELINE INTEGRATION TEST")
    logger.info("="*80)

    # Verify fake database exists
    fake_db_path = Path("fake_onedrive_database")
    if not fake_db_path.exists():
        logger.error(f"Fake database not found at: {fake_db_path.absolute()}")
        logger.info("Please run: python generate_fake_database.py")
        return 1

    try:
        # STEP 1: Scan local fake database
        logger.info("\n" + "="*80)
        logger.info("STEP 1: Scanner - Discovering Files")
        logger.info("="*80)

        scanner = LocalScanner()
        discovered_files = scanner.traverse_local_structure(str(fake_db_path))

        if not discovered_files:
            logger.error("No files discovered!")
            return 1

        logger.info(f"\n✓ Scan completed!")
        logger.info(f"  Total files discovered: {len(discovered_files)}")

        # Analyze file types
        csv_count = len([f for f in discovered_files if f['name'].endswith('.csv')])
        txt_count = len([f for f in discovered_files if f['name'].endswith('.txt')])
        logger.info(f"  CSV files: {csv_count}")
        logger.info(f"  TXT files: {txt_count}")

        # STEP 2: Extract metadata
        logger.info("\n" + "="*80)
        logger.info("STEP 2: Extractor - Parsing Metadata")
        logger.info("="*80)

        # Use standard MetadataExtractor (now supports local files!)
        extractor = MetadataExtractor()

        # Extract file paths for batch processing
        file_paths = [f['path'] for f in discovered_files]

        # Use batch_extract with file_metadata (includes local_path)
        metadata_list = extractor.batch_extract(file_paths, file_metadata=discovered_files)

        # Count extraction errors
        extraction_errors = [m for m in metadata_list if m.get('parse_quality') == 'failed']

        logger.info(f"\n✓ Extraction completed!")
        logger.info(f"  Total metadata extracted: {len(metadata_list)}")
        if extraction_errors:
            logger.warning(f"  Extraction errors: {len(extraction_errors)}")

        # Analyze metadata distribution
        device_types = set()
        parse_qualities = {}

        for meta in metadata_list:
            if 'device_type' in meta:
                device_types.add(meta['device_type'])
            quality = meta.get('parse_quality', 'unknown')
            parse_qualities[quality] = parse_qualities.get(quality, 0) + 1

        logger.info(f"  Device types found: {', '.join(sorted(device_types))}")
        logger.info(f"  Parse quality distribution:")
        for quality, count in sorted(parse_qualities.items()):
            logger.info(f"    {quality}: {count}")

        # STEP 3: Load into CSV database
        logger.info("\n" + "="*80)
        logger.info("STEP 3: CSV Manager - Loading Data")
        logger.info("="*80)

        test_csv_path = "data/test_database.csv"
        csv_manager = CSVManager(csv_path=test_csv_path)

        # Clear existing data for fresh test
        csv_manager.df = csv_manager._load_or_create_database()

        records_added = csv_manager.add_records(metadata_list)
        logger.info(f"\n✓ Data loaded!")
        logger.info(f"  Records added: {records_added}")
        logger.info(f"  Total records in database: {len(csv_manager.df)}")

        # Save database
        csv_manager.save()
        logger.info(f"  Database saved to: {csv_manager.csv_path}")

        # STEP 4: Validate output
        logger.info("\n" + "="*80)
        logger.info("STEP 4: Validation - Data Integrity Check")
        logger.info("="*80)

        validation = validate_csv_output(csv_manager)

        # Print validation summary
        logger.info(f"\nTotal Records: {validation['total_records']}")
        logger.info(f"CSV Files: {validation.get('csv_files', 0)}")
        logger.info(f"TXT Files: {validation.get('txt_files', 0)}")
        logger.info(f"Checks Passed: {validation['checks_passed']}/{validation['checks_total']}")

        logger.info("\nValidation Details:")
        for note in validation['warnings']:
            logger.info(f"  {note}")

        if validation['issues']:
            logger.warning("\nValidation Issues Found:")
            for issue in validation['issues']:
                logger.warning(f"  ❌ {issue}")

        # STEP 5: Print sample records
        print_sample_records(csv_manager)

        # STEP 6: Print database summary
        logger.info("\n" + "="*80)
        logger.info("DATABASE SUMMARY")
        logger.info("="*80)
        csv_manager.print_summary()

        # Final report
        elapsed = (datetime.now() - start_time).total_seconds()
        logger.info("\n" + "="*80)
        logger.info("INTEGRATION TEST COMPLETE")
        logger.info("="*80)
        logger.info(f"\n✅ Pipeline Execution Successful")
        logger.info(f"   Time elapsed: {elapsed:.2f} seconds")
        logger.info(f"   Records created: {validation['total_records']}")
        logger.info(f"   Database: {test_csv_path}")
        logger.info(f"   Files processed: {len(discovered_files)}")
        logger.info(f"   Metadata extracted: {len(metadata_list)}")
        logger.info(f"   Validation passed: {validation['checks_passed']}/{validation['checks_total']}")

        if validation['issues']:
            logger.warning(f"\n⚠ {len(validation['issues'])} validation issue(s) detected")
            logger.warning("Please review above for details")
            return 1

        return 0

    except Exception as e:
        logger.error(f"\n❌ Pipeline failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)
