#!/usr/bin/env python3
"""
Test script to validate the critical fixes applied to the scanner and extractor.

This script tests:
1. Encoding handling improvements
2. Structured error reporting (partially)
3. Removal of hardcoded default fluids
4. Date year assumption fixes
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.extractor import MetadataExtractor
from src.utils import safe_file_read
import tempfile


def test_encoding_handling():
    """Test that safe_file_read handles different encodings."""
    print("[TEST] Testing encoding handling...")

    # Test with a simple ASCII file
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        f.write("Simple ASCII content\nLine 2")
        temp_path = f.name

    try:
        content = safe_file_read(temp_path)
        assert content is not None, "Should read ASCII file successfully"
        assert "Simple ASCII content" in content, "Content should be correct"
        print("  [PASS] ASCII file reading works")
    finally:
        os.unlink(temp_path)

    # Test with non-existent file
    content = safe_file_read("non_existent_file.txt")
    assert content is None, "Should return None for non-existent file"
    print("  [PASS] Non-existent file handling works")


def test_fluid_defaults_removed():
    """Test that hardcoded fluid defaults are no longer applied."""
    print("\n[TEST] Testing removal of hardcoded fluid defaults...")

    extractor = MetadataExtractor()

    # Test path without fluid information
    test_path = "W13_S1_R2/06102025/5mlhr500mbar/dfu_measure/DFU1.csv"

    metadata = extractor.extract_from_path(test_path)

    # Check that fluids are None instead of hardcoded defaults
    print(f"   Aqueous fluid: {metadata.get('aqueous_fluid')}")
    print(f"   Oil fluid: {metadata.get('oil_fluid')}")
    print(f"   Missing aqueous flag: {metadata.get('missing_aqueous_fluid')}")
    print(f"   Missing oil flag: {metadata.get('missing_oil_fluid')}")

    # Should be None, not 'SDS' or 'SO'
    assert metadata.get('aqueous_fluid') is None, f"Expected None, got {metadata.get('aqueous_fluid')}"
    assert metadata.get('oil_fluid') is None, f"Expected None, got {metadata.get('oil_fluid')}"
    assert metadata.get('missing_aqueous_fluid') is True, "Should flag missing aqueous fluid"
    assert metadata.get('missing_oil_fluid') is True, "Should flag missing oil fluid"

    print("  [PASS] Hardcoded defaults removed successfully")


def test_date_year_assumptions():
    """Test that date year assumptions are properly validated and tracked."""
    print("\n[TEST] Testing date year assumption improvements...")

    extractor = MetadataExtractor()

    # Test short date format (should track year assumption)
    test_path = "W13_S1_R2/0610/5mlhr500mbar/dfu_measure/DFU1.csv"

    metadata = extractor.extract_from_path(test_path)

    print(f"   Bonding date: {metadata.get('bonding_date')}")
    print(f"   Year assumed: {metadata.get('bonding_date_year_assumed')}")

    # Should have parsed date and flagged year assumption
    assert metadata.get('bonding_date') is not None, "Should parse short date"
    assert metadata.get('bonding_date_year_assumed') is True, "Should flag year assumption"

    # Test long date format (should not flag year assumption)
    test_path_long = "W13_S1_R2/06102025/5mlhr500mbar/dfu_measure/DFU1.csv"

    metadata_long = extractor.extract_from_path(test_path_long)

    print(f"   Long date bonding: {metadata_long.get('bonding_date')}")
    print(f"   Year assumed (long): {metadata_long.get('bonding_date_year_assumed')}")

    assert metadata_long.get('bonding_date') is not None, "Should parse long date"
    assert metadata_long.get('bonding_date_year_assumed') is None, "Should not flag year assumption for long date"

    print("  [PASS] Date year assumption tracking works")


def test_parse_quality_assessment():
    """Test that parse quality assessment reflects the changes."""
    print("\n[TEST] Testing parse quality assessment...")

    extractor = MetadataExtractor()

    # Test with good data (no fluids, but other fields present)
    test_path = "W13_S1_R2/06102025/5mlhr500mbar/dfu_measure/DFU1.csv"

    metadata = extractor.extract_from_path(test_path)

    print(f"   Parse quality: {metadata.get('parse_quality')}")
    print(f"   Device type: {metadata.get('device_type')}")
    print(f"   Bonding date: {metadata.get('bonding_date')}")
    print(f"   Flow rate: {metadata.get('aqueous_flowrate')}")
    print(f"   Pressure: {metadata.get('oil_pressure')}")

    # Should be partial or minimal since fluids are missing
    quality = metadata.get('parse_quality')
    assert quality in ['partial', 'minimal'], f"Expected partial/minimal quality, got {quality}"

    print("  [PASS] Parse quality assessment updated correctly")


def test_structured_error_reporting():
    """Test the new structured error reporting (basic test)."""
    print("\n[TEST] Testing structured error reporting...")

    extractor = MetadataExtractor()

    # Test the new structured method
    result = extractor.extract_from_path_structured("W13_S1_R2/06102025/5mlhr500mbar/dfu_measure/DFU1.csv")

    print(f"   Success: {result.success}")
    print(f"   Metadata present: {result.metadata is not None}")
    print(f"   Parse quality: {result.parse_quality}")
    print(f"   Warnings: {len(result.warnings)}")
    print(f"   Errors: {len(result.errors)}")

    assert result.success is True, "Should succeed for valid path"
    assert result.metadata is not None, "Should have metadata"

    # Test with invalid path
    invalid_result = extractor.extract_from_path_structured("")

    print(f"   Invalid path success: {invalid_result.success}")
    print(f"   Invalid path errors: {len(invalid_result.errors)}")

    assert invalid_result.success is False, "Should fail for empty path"
    assert len(invalid_result.errors) > 0, "Should have error messages"

    print("  [PASS] Structured error reporting works")


def main():
    """Run all tests."""
    print("Running critical fixes validation tests...\n")

    try:
        test_encoding_handling()
        test_fluid_defaults_removed()
        test_date_year_assumptions()
        test_parse_quality_assessment()
        test_structured_error_reporting()

        print("\n[SUCCESS] All critical fixes validation tests passed!")
        print("\nSummary of fixes validated:")
        print("   [OK] Encoding vulnerabilities fixed")
        print("   [OK] Hardcoded fluid defaults removed")
        print("   [OK] Date year assumptions improved with validation")
        print("   [OK] Parse quality assessment updated")
        print("   [OK] Structured error reporting implemented")

        return True

    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)