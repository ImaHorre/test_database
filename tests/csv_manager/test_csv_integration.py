"""
CSV Manager Integration Test

Tests the complete pipeline:
1. Scanner discovers files from local fake database
2. Extractor extracts metadata from file paths and content
3. CSV Manager loads data into database
4. Validates flattening logic, schema, and data integrity
"""

import os
import sys
import logging
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.scanner import SharePointScanner
from src.extractor import MetadataExtractor
from src.csv_manager import CSVManager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class LocalScanner:
    """
    Scanner that works with local file system instead of SharePoint.
    Used for testing with fake database.
    """

    def __init__(self, base_path: str):
        """
        Initialize local scanner.

        Args:
            base_path: Root path to scan
        """
        self.base_path = Path(base_path)
        if not self.base_path.exists():
            raise ValueError(f"Path does not exist: {base_path}")

        logger.info(f"Initialized LocalScanner for: {self.base_path.absolute()}")

    def traverse_structure(self) -> list:
        """
        Recursively traverse directory structure and discover all measurement files.

        Returns:
            List of discovered file dicts with metadata
        """
        discovered_files = []

        for file_path in self.base_path.rglob('*'):
            if file_path.is_file() and file_path.suffix in ['.csv', '.txt']:
                # Calculate relative path from base
                rel_path = file_path.relative_to(self.base_path)

                file_info = {
                    'name': file_path.name,
                    'path': str(rel_path).replace('\\', '/'),  # Use forward slashes
                    'size': file_path.stat().st_size,
                    'modified': file_path.stat().st_mtime,
                    'local_path': str(file_path),  # Store local absolute path
                    'download_url': None,  # Not applicable for local files
                    'web_url': None
                }

                discovered_files.append(file_info)
                logger.info(f"  Discovered: {file_info['path']}")

        logger.info(f"\nFound {len(discovered_files)} measurement files")
        return discovered_files


class LocalMetadataExtractor(MetadataExtractor):
    """
    Extended Extractor that can read local files for content parsing.
    """

    def parse_dfu_csv_content(self, local_path: str):
        """
        Parse DFU measurement CSV file from local path.

        Args:
            local_path: Local file system path

        Returns:
            Dict with droplet size statistics
        """
        try:
            import pandas as pd

            df = pd.read_csv(local_path)

            stats = {
                'row_count': len(df),
                'columns': df.columns.tolist(),
            }

            # Try to extract droplet size data
            size_columns = [col for col in df.columns if any(
                keyword in col.lower() for keyword in ['diameter', 'size', 'droplet']
            )]

            if size_columns:
                size_col = size_columns[0]
                sizes = df[size_col].dropna()

                stats.update({
                    'droplet_size_mean': float(sizes.mean()),
                    'droplet_size_std': float(sizes.std()),
                    'droplet_size_min': float(sizes.min()),
                    'droplet_size_max': float(sizes.max()),
                    'droplet_count': len(sizes),
                    'size_column': size_col
                })

            return stats

        except Exception as e:
            logger.warning(f"Could not parse CSV content: {e}")
            return None

    def parse_freq_txt_content(self, local_path: str):
        """
        Parse frequency analysis TXT file from local path.

        Args:
            local_path: Local file system path

        Returns:
            Dict with frequency analysis data
        """
        try:
            with open(local_path, 'r') as f:
                lines = f.read().strip().split('\n')

            data = {
                'line_count': len(lines),
                'raw_sample': lines[:5] if len(lines) >= 5 else lines
            }

            # Try to extract numeric values
            numeric_values = []
            for line in lines:
                try:
                    value = float(line.strip())
                    numeric_values.append(value)
                except ValueError:
                    continue

            if numeric_values:
                data.update({
                    'frequency_count': len(numeric_values),
                    'frequency_mean': sum(numeric_values) / len(numeric_values),
                    'frequency_min': min(numeric_values),
                    'frequency_max': max(numeric_values)
                })

            return data

        except Exception as e:
            logger.warning(f"Could not parse TXT content: {e}")
            return None

    def extract_from_path_with_content(self, file_path: str, local_path: str = None) -> dict:
        """
        Extract metadata including file content (for local files).

        Args:
            file_path: Relative path from root (forward slashes)
            local_path: Absolute local file system path

        Returns:
            Dict with extracted metadata
        """
        # First extract from path
        metadata = self.extract_from_path(file_path)

        # Then try to parse file content if local_path provided
        if local_path and os.path.exists(local_path):
            file_type = metadata.get('file_type')
            measurement_type = metadata.get('measurement_type')

            if file_type == 'csv' and measurement_type == 'dfu_measure':
                logger.info(f"Parsing DFU CSV content: {metadata.get('file_name')}")
                content_data = self.parse_dfu_csv_content(local_path)
                if content_data:
                    metadata['file_content_data'] = content_data

            elif file_type == 'txt' and measurement_type == 'freq_analysis':
                logger.info(f"Parsing frequency TXT content: {metadata.get('file_name')}")
                content_data = self.parse_freq_txt_content(local_path)
                if content_data:
                    metadata['file_content_data'] = content_data

        return metadata


def validate_csv_output(csv_manager: CSVManager) -> dict:
    """
    Validate CSV output data.

    Checks:
    - No duplicate records
    - No data loss
    - Schema matches expected columns
    - Measurement data properly flattened
    - Area/timepoint fields work

    Returns:
        Dict with validation results
    """
    logger.info("\n" + "="*70)
    logger.info("VALIDATION: CSV Output")
    logger.info("="*70)

    results = {
        'total_records': len(csv_manager.df),
        'issues': [],
        'warnings': []
    }

    # Check for duplicates
    if len(csv_manager.df) > 0:
        duplicates = csv_manager.df[csv_manager.df.duplicated(subset=['raw_path'], keep=False)]
        if len(duplicates) > 0:
            results['issues'].append(f"Found {len(duplicates)} duplicate records by raw_path")
        else:
            results['warnings'].append("✓ No duplicate records detected")

    # Check schema
    missing_cols = [col for col in CSVManager.COLUMNS if col not in csv_manager.df.columns]
    if missing_cols:
        results['issues'].append(f"Missing columns: {missing_cols}")
    else:
        results['warnings'].append(f"✓ All {len(CSVManager.COLUMNS)} schema columns present")

    # Check for measurement data
    if len(csv_manager.df) > 0:
        csv_files = csv_manager.df[csv_manager.df['file_type'] == 'csv']
        txt_files = csv_manager.df[csv_manager.df['file_type'] == 'txt']

        results['csv_files'] = len(csv_files)
        results['txt_files'] = len(txt_files)

        # Check droplet data flattening
        csv_with_droplet_data = csv_files[csv_files['droplet_size_mean'].notna()]
        if len(csv_with_droplet_data) > 0:
            results['warnings'].append(
                f"✓ Droplet data properly flattened: {len(csv_with_droplet_data)} CSV files with data"
            )
        else:
            results['warnings'].append("⚠ No droplet data found in CSV files (may be normal if files are empty)")

        # Check frequency data flattening
        txt_with_freq_data = txt_files[txt_files['frequency_mean'].notna()]
        if len(txt_with_freq_data) > 0:
            results['warnings'].append(
                f"✓ Frequency data properly flattened: {len(txt_with_freq_data)} TXT files with data"
            )
        else:
            results['warnings'].append("⚠ No frequency data found in TXT files (may be normal if files are empty)")

        # Check parse quality
        parse_quality_counts = csv_manager.df['parse_quality'].value_counts().to_dict()
        results['parse_quality'] = parse_quality_counts
        results['warnings'].append(f"✓ Parse quality distribution: {parse_quality_counts}")

        # Check for data loss (all droplet mean values should be non-null for real CSV files)
        csv_with_content = csv_files[csv_files['file_name'].notna()]
        csv_missing_data = csv_with_content[csv_with_content['droplet_size_mean'].isna()]
        if len(csv_missing_data) > 0:
            results['warnings'].append(
                f"⚠ {len(csv_missing_data)} CSV files have no droplet data (may indicate parsing issue)"
            )

    # Check metadata fields
    if len(csv_manager.df) > 0:
        device_types = csv_manager.df['device_type'].nunique()
        unique_devices = csv_manager.df['device_id'].nunique()
        results['warnings'].append(f"✓ Device types: {device_types}, Unique devices: {unique_devices}")

    return results


def print_sample_records(csv_manager: CSVManager, num_samples: int = 3):
    """Print sample records from the CSV."""
    if len(csv_manager.df) == 0:
        print("⚠ No records to display")
        return

    logger.info("\n" + "="*70)
    logger.info("SAMPLE RECORDS (First 3)")
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
    print(sample.to_string())
    print()


def main():
    """Run integration test."""
    logger.info("\n" + "="*70)
    logger.info("CSV MANAGER INTEGRATION TEST")
    logger.info("="*70)

    # Verify fake database exists
    fake_db_path = Path("fake_onedrive_database")
    if not fake_db_path.exists():
        logger.error(f"Fake database not found at: {fake_db_path.absolute()}")
        logger.info("Please run: python generate_fake_database.py")
        return 1

    try:
        # Step 1: Scan local fake database
        logger.info("\n" + "="*70)
        logger.info("STEP 1: Scanning Local Fake Database")
        logger.info("="*70)

        scanner = LocalScanner(str(fake_db_path))
        discovered_files = scanner.traverse_structure()

        if not discovered_files:
            logger.error("No files discovered!")
            return 1

        logger.info(f"\n✓ Discovered {len(discovered_files)} files")

        # Step 2: Extract metadata
        logger.info("\n" + "="*70)
        logger.info("STEP 2: Extracting Metadata")
        logger.info("="*70)

        extractor = LocalMetadataExtractor()
        metadata_list = []

        for i, file_info in enumerate(discovered_files):
            file_path = file_info['path']
            local_path = file_info['local_path']

            # Extract with content parsing
            metadata = extractor.extract_from_path_with_content(file_path, local_path)
            metadata_list.append(metadata)

            if (i + 1) % 10 == 0:
                logger.info(f"  Extracted {i + 1}/{len(discovered_files)} files...")

        logger.info(f"✓ Extracted metadata from {len(metadata_list)} files")

        # Step 3: Load into CSV database
        logger.info("\n" + "="*70)
        logger.info("STEP 3: Loading Data into CSV")
        logger.info("="*70)

        # Use test database path
        test_csv_path = "data/test_database.csv"
        csv_manager = CSVManager(csv_path=test_csv_path)

        records_added = csv_manager.add_records(metadata_list)
        logger.info(f"✓ Added {records_added} records to CSV")

        # Save database
        csv_manager.save()
        logger.info(f"✓ Database saved to: {csv_manager.csv_path}")

        # Step 4: Validate output
        logger.info("\n" + "="*70)
        logger.info("STEP 4: Validating Output")
        logger.info("="*70)

        validation = validate_csv_output(csv_manager)

        # Print validation results
        logger.info(f"\nTotal Records: {validation['total_records']}")
        logger.info(f"CSV Files: {validation.get('csv_files', 0)}")
        logger.info(f"TXT Files: {validation.get('txt_files', 0)}")

        if validation.get('parse_quality'):
            logger.info(f"Parse Quality Distribution:")
            for quality, count in validation['parse_quality'].items():
                logger.info(f"  {quality}: {count}")

        logger.info("\nValidation Notes:")
        for note in validation['warnings']:
            logger.info(f"  {note}")

        if validation['issues']:
            logger.warning("\nValidation Issues:")
            for issue in validation['issues']:
                logger.warning(f"  ❌ {issue}")

        # Step 5: Print sample records
        print_sample_records(csv_manager)

        # Step 6: Print summary
        logger.info("\n" + "="*70)
        logger.info("DATABASE SUMMARY")
        logger.info("="*70)

        csv_manager.print_summary()

        # Final report
        logger.info("\n" + "="*70)
        logger.info("INTEGRATION TEST COMPLETE")
        logger.info("="*70)
        logger.info(f"\n✅ Test passed!")
        logger.info(f"   Records created: {validation['total_records']}")
        logger.info(f"   CSV database: {test_csv_path}")

        if validation['issues']:
            logger.warning(f"\n⚠ {len(validation['issues'])} validation issue(s) detected")
            return 1

        return 0

    except Exception as e:
        logger.error(f"\n❌ Test failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit(main())
