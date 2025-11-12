"""
Test script for LocalScanner

Tests local file system scanning capability before SharePoint deployment.
Scans the fake_onedrive_database and validates output structure.
"""

import json
import logging
from pathlib import Path
from src.scanner import LocalScanner
from src.extractor import MetadataExtractor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_local_scanner():
    """Test the LocalScanner with fake_onedrive_database."""

    print("\n" + "="*80)
    print("LOCAL SCANNER TEST")
    print("="*80)

    # Initialize scanner
    scanner = LocalScanner()

    # Path to fake database
    fake_db_path = "fake_onedrive_database"

    # Check if path exists
    if not Path(fake_db_path).exists():
        logger.error(f"Database path not found: {fake_db_path}")
        return False

    # Scan local directory
    logger.info(f"Scanning: {fake_db_path}")
    files = scanner.traverse_local_structure(fake_db_path)

    print(f"\n✓ Scan completed successfully!")
    print(f"✓ Files discovered: {len(files)}")

    if not files:
        logger.error("No files found in database")
        return False

    # Analyze results
    csv_files = [f for f in files if f['name'].endswith('.csv')]
    txt_files = [f for f in files if f['name'].endswith('.txt')]

    print(f"\n📊 File Summary:")
    print(f"  CSV files: {len(csv_files)}")
    print(f"  TXT files: {len(txt_files)}")

    # Check file structure
    print(f"\n📁 Directory Structure Analysis:")
    device_ids = set()
    bonding_dates = set()
    testing_dates = set()
    flow_params = set()

    for file in files:
        path_parts = file['path'].split('/')
        if len(path_parts) >= 1:
            device_ids.add(path_parts[0])
        if len(path_parts) >= 2:
            bonding_dates.add(path_parts[1])
        if len(path_parts) >= 3:
            testing_dates.add(path_parts[2])
        if len(path_parts) >= 5:
            flow_params.add(path_parts[4])

    print(f"  Unique device IDs: {len(device_ids)}")
    for did in sorted(device_ids):
        print(f"    - {did}")

    print(f"  Unique bonding dates: {len(bonding_dates)}")
    for bd in sorted(bonding_dates):
        print(f"    - {bd}")

    print(f"  Unique testing dates: {len(testing_dates)}")
    for td in sorted(testing_dates):
        print(f"    - {td}")

    print(f"  Unique flow parameters: {len(flow_params)}")
    for fp in sorted(flow_params):
        print(f"    - {fp}")

    # Sample file details
    print(f"\n📄 Sample Files (first 5):")
    for i, file in enumerate(files[:5]):
        print(f"\n  [{i+1}] {file['name']}")
        print(f"      Path: {file['path']}")
        print(f"      Size: {file['size']} bytes")
        print(f"      Modified: {file['modified']}")
        print(f"      File URL: {file['file_url']}")

    # Test Extractor compatibility
    print(f"\n🔗 Testing Extractor Compatibility:")
    extractor = MetadataExtractor()

    # Test a few files
    sample_files = files[:3]
    extraction_results = []

    for file in sample_files:
        try:
            # Extract metadata from path
            metadata = extractor.extract_from_path(file['path'])
            extraction_results.append(metadata)

            print(f"\n  {file['name']}:")
            print(f"    Device: {metadata.get('device_type', 'N/A')}")
            print(f"    Bonding Date: {metadata.get('bonding_date', 'N/A')}")
            print(f"    Testing Date: {metadata.get('testing_date', 'N/A')}")
            print(f"    Flow Rate: {metadata.get('aqueous_flowrate', 'N/A')} {metadata.get('aqueous_flowrate_unit', '')}")
            print(f"    Oil Pressure: {metadata.get('oil_pressure', 'N/A')} {metadata.get('oil_pressure_unit', '')}")
            print(f"    DFU Row: {metadata.get('dfu_row', 'N/A')}")
            print(f"    Parse Quality: {metadata.get('parse_quality', 'N/A')}")

        except Exception as e:
            logger.error(f"Error extracting metadata from {file['path']}: {e}")
            extraction_results.append({
                'error': str(e),
                'path': file['path']
            })

    # Save results to JSON
    output_file = "test_scanner_results.json"
    results = {
        'timestamp': __import__('datetime').datetime.now().isoformat(),
        'scan_path': fake_db_path,
        'files_discovered': len(files),
        'csv_count': len(csv_files),
        'txt_count': len(txt_files),
        'unique_devices': len(device_ids),
        'unique_bonding_dates': len(bonding_dates),
        'unique_testing_dates': len(testing_dates),
        'unique_flow_parameters': len(flow_params),
        'sample_files': [
            {
                'name': f['name'],
                'path': f['path'],
                'size': f['size'],
                'modified': f['modified']
            }
            for f in files[:10]
        ],
        'extraction_samples': extraction_results[:3]
    }

    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\n✓ Results saved to: {output_file}")

    # Final validation
    print(f"\n" + "="*80)
    print("VALIDATION SUMMARY")
    print("="*80)

    checks = [
        ("Files discovered", len(files) > 0),
        ("CSV files found", len(csv_files) > 0),
        ("TXT files found", len(txt_files) > 0),
        ("Device hierarchy parsed", len(device_ids) > 0),
        ("File paths in correct format", all('/' in f['path'] for f in files)),
        ("File metadata complete", all(all(k in f for k in ['name', 'path', 'size', 'modified']) for f in files)),
        ("Metadata extraction works", len(extraction_results) > 0),
    ]

    all_passed = True
    for check_name, passed in checks:
        status = "✓" if passed else "✗"
        print(f"  {status} {check_name}")
        if not passed:
            all_passed = False

    print("\n" + "="*80)
    if all_passed:
        print("✓ ALL TESTS PASSED")
        return True
    else:
        print("✗ SOME TESTS FAILED")
        return False


if __name__ == "__main__":
    success = test_local_scanner()
    exit(0 if success else 1)
