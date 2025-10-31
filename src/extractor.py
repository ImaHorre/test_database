"""
Metadata Extractor Agent

Parses folder hierarchy and file names to extract structured data.
Handles flexible naming conventions (old vs new formats).
"""

import re
from typing import Dict, Optional, List
from datetime import datetime
import logging
import pandas as pd
import os

from .utils import safe_file_read, safe_file_readlines, sanitize_path_for_logging
from .extraction_result import ExtractionResult

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MetadataExtractor:
    """
    Extracts structured metadata from folder paths and file names.

    Expected folder structure:
    1. Device ID: W13_S1_R4 (Wafer_Shim_Replica)
    2. Bonding Date: 06102025 or 0610
    3. Testing Date: 23102025 or 2310 (sometimes absent)
    4. Fluids: SDS_SO, NaCas_SO (aqueous_oil, sometimes absent)
    5. Flow Parameters: 5mlhr150mbar
    6. Measurement Type: dfu_measure or freq_analysis
    7. Data files: DFU1.csv, DFU1_roi1.txt, etc.
    """

    # Regex patterns for parsing
    DEVICE_ID_PATTERN = r'^(W\d+)_S(\d+)_R(\d+)$'
    DATE_LONG_PATTERN = r'^(\d{2})(\d{2})(\d{4})$'  # DDMMYYYY
    DATE_SHORT_PATTERN = r'^(\d{2})(\d{2})$'  # DDMM
    FLUID_PATTERN = r'^([A-Za-z]+)_([A-Za-z]+)$'  # Aqueous_Oil
    FLOW_PATTERN = r'^(\d+)mlhr(\d+)mbar$'  # flowrate + pressure
    DFU_FILE_PATTERN = r'DFU(\d+)(?:_([A-C]))?(?:_t(\d+))?'  # DFU row, optional area (A-C), optional timepoint
    ROI_PATTERN = r'_roi(\d+)'

    def __init__(self):
        self.current_year = datetime.now().year

    def parse_device_id(self, device_str: str) -> Optional[Dict]:
        """
        Parse device ID string.

        Args:
            device_str: e.g., "W13_S1_R4"

        Returns:
            Dict with device_type, wafer, shim, replica
        """
        match = re.match(self.DEVICE_ID_PATTERN, device_str)
        if match:
            device_type = match.group(1)  # W13
            wafer = int(device_type[1:])  # 13
            shim = int(match.group(2))  # 1
            replica = int(match.group(3))  # 4

            return {
                'device_type': device_type,
                'device_id': device_str,
                'wafer': wafer,
                'shim': shim,
                'replica': replica
            }
        else:
            logger.warning(f"⚠ Could not parse device ID: {device_str}")
            return None

    def parse_date(self, date_str: str, file_path: Optional[str] = None) -> Optional[str]:
        """
        Parse date string in various formats with validation.

        Args:
            date_str: e.g., "06102025" or "0610"
            file_path: Optional file path for context validation

        Returns:
            ISO format date string (YYYY-MM-DD) or None
        """
        # Try long format first (DDMMYYYY)
        match = re.match(self.DATE_LONG_PATTERN, date_str)
        if match:
            day = match.group(1)
            month = match.group(2)
            year = match.group(3)

            # Validate date components
            try:
                date_obj = datetime(int(year), int(month), int(day))
                return f"{year}-{month}-{day}"
            except ValueError as e:
                logger.warning(f"⚠ Invalid date components in {date_str}: {e}")
                return None

        # Try short format (DDMM) with intelligent year detection
        match = re.match(self.DATE_SHORT_PATTERN, date_str)
        if match:
            day = int(match.group(1))
            month = int(match.group(2))

            # Validate month and day ranges
            if month < 1 or month > 12:
                logger.warning(f"⚠ Invalid month in date: {date_str}")
                return None
            if day < 1 or day > 31:
                logger.warning(f"⚠ Invalid day in date: {date_str}")
                return None

            # Determine year with validation
            year = self._determine_year_for_short_date(day, month, file_path, date_str)

            try:
                date_obj = datetime(year, month, day)
                return f"{year:04d}-{month:02d}-{day:02d}"
            except ValueError as e:
                logger.warning(f"⚠ Invalid date {day}/{month}/{year}: {e}")
                return None

        logger.warning(f"⚠ Could not parse date: {date_str}")
        return None

    def _determine_year_for_short_date(self, day: int, month: int, file_path: Optional[str], date_str: str) -> int:
        """
        Intelligently determine year for short date format (DDMM).

        Uses file modification time as validation hint when available.

        Args:
            day: Day component
            month: Month component
            file_path: Optional file path for validation
            date_str: Original date string for logging

        Returns:
            Year as integer
        """
        current_year = self.current_year

        # Try current year first
        try:
            test_date_current = datetime(current_year, month, day)
        except ValueError:
            # Invalid date (e.g., Feb 29 in non-leap year)
            logger.warning(f"⚠ Date {day}/{month}/{current_year} is invalid, trying previous year")
            current_year -= 1
            try:
                test_date_current = datetime(current_year, month, day)
            except ValueError:
                logger.warning(f"⚠ Date {day}/{month}/{current_year} is also invalid")
                return current_year  # Return anyway, will fail later

        # If no file path for validation, use current year with warning
        if not file_path or not os.path.exists(file_path):
            logger.info(f"ⓘ Assuming year {current_year} for date {date_str} (no file validation available)")
            return current_year

        try:
            # Get file modification time for validation
            file_mtime = datetime.fromtimestamp(os.path.getmtime(file_path))

            # Check if current year assumption makes date unreasonably far in future
            if test_date_current > datetime.now():
                days_in_future = (test_date_current - datetime.now()).days
                if days_in_future > 365:  # More than a year in future
                    previous_year = current_year - 1
                    logger.warning(f"⚠ Date {date_str} with year {current_year} is {days_in_future} days in future, using {previous_year}")
                    return previous_year

            # Check if date is reasonable compared to file modification time
            time_diff = abs((test_date_current - file_mtime).days)
            if time_diff > 730:  # More than 2 years difference
                # File was modified much earlier/later than parsed date suggests
                file_year = file_mtime.year
                logger.warning(f"⚠ Parsed date year {current_year} differs significantly from file modification year {file_year}")
                logger.warning(f"   File modified: {file_mtime.strftime('%Y-%m-%d')}, parsed date would be: {test_date_current.strftime('%Y-%m-%d')}")

                # Use file year if it makes more sense
                try:
                    file_year_date = datetime(file_year, month, day)
                    file_year_diff = abs((file_year_date - file_mtime).days)
                    if file_year_diff < time_diff:
                        logger.info(f"ⓘ Using file modification year {file_year} for better accuracy")
                        return file_year
                except ValueError:
                    pass  # File year doesn't work either

            logger.debug(f"✓ Year {current_year} for date {date_str} validated against file modification time")
            return current_year

        except (OSError, ValueError) as e:
            logger.debug(f"Could not validate date against file time: {e}")
            logger.info(f"ⓘ Using year {current_year} for date {date_str} (file validation failed)")
            return current_year

    def parse_fluids(self, fluid_str: str) -> Optional[Dict]:
        """
        Parse fluid string.

        Args:
            fluid_str: e.g., "NaCas_SO" or "SDS_SO"

        Returns:
            Dict with aqueous_fluid and oil_fluid
        """
        match = re.match(self.FLUID_PATTERN, fluid_str)
        if match:
            return {
                'aqueous_fluid': match.group(1),
                'oil_fluid': match.group(2)
            }
        else:
            logger.warning(f"⚠ Could not parse fluids: {fluid_str}")
            return None

    def parse_flow_parameters(self, flow_str: str) -> Optional[Dict]:
        """
        Parse flow parameter string.

        Args:
            flow_str: e.g., "5mlhr150mbar"

        Returns:
            Dict with aqueous_flowrate and oil_pressure
        """
        match = re.match(self.FLOW_PATTERN, flow_str)
        if match:
            return {
                'aqueous_flowrate': int(match.group(1)),
                'aqueous_flowrate_unit': 'ml/hr',
                'oil_pressure': int(match.group(2)),
                'oil_pressure_unit': 'mbar'
            }
        else:
            logger.warning(f"⚠ Could not parse flow parameters: {flow_str}")
            return None

    def parse_file_name(self, file_name: str) -> Optional[Dict]:
        """
        Parse measurement file name.

        Args:
            file_name: e.g., "DFU1.csv", "DFU2_roi3.txt", "DFU1_B_t0_droplet_annotations.csv"

        Returns:
            Dict with dfu_row, measurement_area (if applicable), timepoint (if applicable), roi (if applicable), file_type
        """
        match = re.search(self.DFU_FILE_PATTERN, file_name)
        if not match:
            logger.warning(f"⚠ Could not parse file name: {file_name}")
            return None

        dfu_row = int(match.group(1))
        measurement_area = match.group(2)  # A, B, or C (None if not present)
        timepoint = int(match.group(3)) if match.group(3) else None  # t0, t1, etc. (None if not present)

        # Determine file type from file extension
        file_type = None
        if file_name.endswith('.csv'):
            file_type = 'csv'
        elif file_name.endswith('.txt'):
            file_type = 'txt'

        # Check for ROI (both lowercase _roi and uppercase _ROI)
        roi_match = re.search(self.ROI_PATTERN, file_name, re.IGNORECASE)
        roi = int(roi_match.group(1)) if roi_match else None

        result = {
            'dfu_row': dfu_row,
            'file_type': file_type,
            'roi': roi
        }

        # Only add measurement_area and timepoint if they are present
        if measurement_area:
            result['measurement_area'] = measurement_area
        if timepoint is not None:
            result['timepoint'] = timepoint

        return result

    def parse_dfu_csv_content(self, local_path: str) -> Optional[Dict]:
        """
        Parse DFU measurement CSV file content.

        Args:
            local_path: Local file path to read CSV file

        Returns:
            Dict with droplet size statistics or None if parsing fails
        """
        try:
            if not local_path:
                logger.warning("⚠ No local_path provided")
                return None

            # Read CSV from local file with encoding handling
            try:
                # Try UTF-8 first (most common)
                df = pd.read_csv(local_path, encoding='utf-8')
            except UnicodeDecodeError:
                try:
                    # Fall back to latin-1 for special characters
                    df = pd.read_csv(local_path, encoding='latin-1')
                    logger.debug(f"Used latin-1 encoding for CSV: {sanitize_path_for_logging(local_path)}")
                except UnicodeDecodeError:
                    # Final fallback to cp1252 (Windows default)
                    df = pd.read_csv(local_path, encoding='cp1252', errors='replace')
                    logger.warning(f"Used cp1252 with error replacement for CSV: {sanitize_path_for_logging(local_path)}")
            except Exception as e:
                logger.error(f"Failed to read CSV file: {sanitize_path_for_logging(local_path)}: {e}")
                return None

            # Extract basic statistics
            stats = {
                'row_count': len(df),
                'columns': df.columns.tolist(),
            }

            # Try to extract droplet size data if column exists
            # Prioritize 'diameter' columns, exclude ID columns
            size_col = None

            # First, look for 'diameter' columns (most specific)
            diameter_cols = [col for col in df.columns if 'diameter' in col.lower() and '_id' not in col.lower()]
            if diameter_cols:
                size_col = diameter_cols[0]
            else:
                # Fallback to 'size' columns (exclude ID columns)
                size_cols = [col for col in df.columns if 'size' in col.lower() and '_id' not in col.lower()]
                if size_cols:
                    size_col = size_cols[0]

            if size_col:
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
            logger.warning(f"⚠ Could not parse CSV content: {e}")
            return None

    def parse_freq_txt_content(self, local_path: str) -> Optional[Dict]:
        """
        Parse frequency analysis TXT file content.

        Args:
            local_path: Local file path to read TXT file

        Returns:
            Dict with frequency analysis data or None if parsing fails
        """
        try:
            if not local_path:
                logger.warning("⚠ No local_path provided")
                return None

            # Read TXT from local file using safe encoding handling
            content = safe_file_read(local_path)
            if content is None:
                logger.error(f"Failed to read file: {sanitize_path_for_logging(local_path)}")
                return None

            lines = content.strip().split('\n')

            # Extract frequency data using regex for structured format
            # Example: "Frequency Method 1 (avg of frequencies): 11.47 Hz"
            freq_method_1 = None
            freq_method_2 = None
            num_cycles = None

            for line in lines:
                # Try to match "Frequency Method 1: X.XX Hz" or similar
                match1 = re.search(r'Frequency Method 1[^:]*:\s*([\d.]+)\s*Hz', line, re.IGNORECASE)
                if match1:
                    freq_method_1 = float(match1.group(1))

                match2 = re.search(r'Frequency Method 2[^:]*:\s*([\d.]+)\s*Hz', line, re.IGNORECASE)
                if match2:
                    freq_method_2 = float(match2.group(1))

                # Extract number of cycles
                cycles_match = re.search(r'Number of cycles:\s*(\d+)', line, re.IGNORECASE)
                if cycles_match:
                    num_cycles = int(cycles_match.group(1))

            # Calculate statistics from both methods
            data = {
                'line_count': len(lines),
            }

            if freq_method_1 is not None and freq_method_2 is not None:
                freq_values = [freq_method_1, freq_method_2]
                data['frequency_mean'] = sum(freq_values) / len(freq_values)
                data['frequency_min'] = min(freq_values)
                data['frequency_max'] = max(freq_values)
                data['frequency_count'] = num_cycles if num_cycles is not None else 0
                data['frequency_method_1'] = freq_method_1
                data['frequency_method_2'] = freq_method_2
            elif freq_method_1 is not None:
                data['frequency_mean'] = freq_method_1
                data['frequency_min'] = freq_method_1
                data['frequency_max'] = freq_method_1
                data['frequency_count'] = num_cycles if num_cycles is not None else 0
                data['frequency_method_1'] = freq_method_1
            elif freq_method_2 is not None:
                data['frequency_mean'] = freq_method_2
                data['frequency_min'] = freq_method_2
                data['frequency_max'] = freq_method_2
                data['frequency_count'] = num_cycles if num_cycles is not None else 0
                data['frequency_method_2'] = freq_method_2

            return data if 'frequency_mean' in data else None

        except Exception as e:
            logger.warning(f"⚠ Could not parse TXT content: {e}")
            return None

    def extract_from_path(self, file_path: str, local_path: Optional[str] = None) -> Dict:
        """
        Extract all metadata from a complete file path.

        Args:
            file_path: e.g., "W13_S1_R2/06102025/23102025/NaCas_SO/5mlhr150mbar/dfu_measure/DFU1.csv"
            local_path: Optional local file path to read contents

        Returns:
            Dict with all extracted metadata
        """
        parts = file_path.split('/')
        metadata = {
            'raw_path': file_path,
            'path_parts': parts,
            'extraction_timestamp': datetime.now().isoformat()
        }

        # Parse each level
        if len(parts) >= 1:
            device_data = self.parse_device_id(parts[0])
            if device_data:
                metadata.update(device_data)

        if len(parts) >= 2:
            bonding_date = self.parse_date(parts[1], local_path)
            if bonding_date:
                metadata['bonding_date'] = bonding_date
                # Track if year was assumed for short date format
                if len(parts[1]) == 4:  # DDMM format
                    metadata['bonding_date_year_assumed'] = True

        # Determine if level 2 is a testing date or something else
        next_idx = 2  # Default: start parsing from level 2
        if len(parts) >= 3:
            # Could be testing date or fluids (testing date may be absent)
            # Try parsing as date first
            testing_date = self.parse_date(parts[2], local_path)
            if testing_date:
                metadata['testing_date'] = testing_date
                # Track if year was assumed for short date format
                if len(parts[2]) == 4:  # DDMM format
                    metadata['testing_date_year_assumed'] = True
                next_idx = 3  # Skip testing date, continue from level 3
            else:
                # Not a date, level 2 is probably fluids or flow params
                metadata['testing_date'] = None
                next_idx = 2  # Start parsing from level 2
        else:
            # Path is too short to have a testing date
            metadata['testing_date'] = None
            next_idx = 2

        # Parse remaining parts (fluids, flow parameters, measurement type)
        remaining = parts[next_idx:] if next_idx < len(parts) else []

        for i, part in enumerate(remaining):
            # Try to identify what this part is

            # Check if it's measurement type folder (CHECK FIRST to avoid false fluid matches)
            if part in ['dfu_measure', 'freq_analysis']:
                metadata['measurement_type'] = part
                continue  # Skip to next part - this is NOT fluids/flow/file

            # Check if it's fluids
            fluid_data = self.parse_fluids(part)
            if fluid_data and 'aqueous_fluid' not in metadata:
                metadata.update(fluid_data)
                continue

            # Check if it's flow parameters
            flow_data = self.parse_flow_parameters(part)
            if flow_data and 'aqueous_flowrate' not in metadata:
                metadata.update(flow_data)
                continue

            # Check if it's a file name (last part)
            if i == len(remaining) - 1 and '.' in part:
                file_data = self.parse_file_name(part)
                if file_data:
                    metadata.update(file_data)
                    metadata['file_name'] = part

        # Parse file contents if local path is provided
        if local_path:
            file_type = metadata.get('file_type')
            measurement_type = metadata.get('measurement_type')

            if file_type == 'csv' and measurement_type == 'dfu_measure':
                logger.info(f"📊 Parsing DFU CSV content from {metadata.get('file_name')}")
                content_data = self.parse_dfu_csv_content(local_path=local_path)
                if content_data:
                    metadata['file_content_data'] = content_data

            elif file_type == 'txt' and measurement_type == 'freq_analysis':
                logger.info(f"📈 Parsing frequency TXT content from {metadata.get('file_name')}")
                content_data = self.parse_freq_txt_content(local_path=local_path)
                if content_data:
                    metadata['file_content_data'] = content_data

        # Track missing fluid information instead of applying defaults
        # This preserves data quality for scientific analysis
        if not metadata.get('aqueous_fluid'):
            logger.info(f"ⓘ No aqueous fluid found in path: {sanitize_path_for_logging(file_path)}")
            metadata['aqueous_fluid'] = None
            metadata['missing_aqueous_fluid'] = True

        if not metadata.get('oil_fluid'):
            logger.info(f"ⓘ No oil fluid found in path: {sanitize_path_for_logging(file_path)}")
            metadata['oil_fluid'] = None
            metadata['missing_oil_fluid'] = True

        # Validate dates
        self._validate_dates(metadata)

        # Add data quality flag
        metadata['parse_quality'] = self._assess_parse_quality(metadata)

        return metadata

    def extract_from_path_structured(self, file_path: str, local_path: Optional[str] = None) -> ExtractionResult:
        """
        Extract metadata with structured error reporting.

        Wrapper around extract_from_path that provides ExtractionResult format.

        Args:
            file_path: Path to extract metadata from
            local_path: Optional local file path for content reading

        Returns:
            ExtractionResult with success status and metadata
        """
        if not file_path:
            return ExtractionResult.failure_result("Empty file path provided", file_path)

        try:
            metadata = self.extract_from_path(file_path, local_path)

            if metadata:
                # Determine quality and create successful result
                quality = metadata.get('parse_quality', 'unknown')
                result = ExtractionResult.success_result(metadata, quality, file_path)

                # Add warnings for missing information
                if metadata.get('missing_aqueous_fluid'):
                    result.add_warning("Aqueous fluid information not found in path")
                if metadata.get('missing_oil_fluid'):
                    result.add_warning("Oil fluid information not found in path")
                if metadata.get('bonding_date_year_assumed'):
                    result.add_warning("Year assumed for bonding date (short format)")
                if metadata.get('testing_date_year_assumed'):
                    result.add_warning("Year assumed for testing date (short format)")

                return result
            else:
                return ExtractionResult.failure_result("Failed to extract metadata", file_path)

        except Exception as e:
            return ExtractionResult.failure_result(f"Extraction error: {str(e)}", file_path)

    def _validate_dates(self, metadata: Dict) -> None:
        """
        Validate date consistency (testing date should be >= bonding date).
        Adds warnings to metadata if dates are inconsistent.
        """
        bonding = metadata.get('bonding_date')
        testing = metadata.get('testing_date')

        if bonding and testing:
            try:
                bonding_dt = datetime.fromisoformat(bonding)
                testing_dt = datetime.fromisoformat(testing)

                if testing_dt < bonding_dt:
                    warning = f"Testing date ({testing}) is before bonding date ({bonding})"
                    logger.warning(f"⚠ {warning}")
                    metadata['date_validation_warning'] = warning

            except ValueError as e:
                logger.warning(f"⚠ Could not validate dates: {e}")

    def _assess_parse_quality(self, metadata: Dict) -> str:
        """
        Assess quality of metadata extraction.

        Returns:
            'complete', 'partial', 'minimal', or 'failed'
        """
        # Core required fields for meaningful analysis
        core_fields = ['device_type', 'bonding_date', 'measurement_type']

        # Important but sometimes absent fields
        important_fields = ['aqueous_flowrate', 'oil_pressure', 'dfu_row']

        # Optional fields that may legitimately be missing
        # Note: fluids removed from required list since they may genuinely be absent

        core_missing = [field for field in core_fields if not metadata.get(field)]
        important_missing = [field for field in important_fields if not metadata.get(field)]

        # Track fluid information quality separately
        fluid_info_available = bool(metadata.get('aqueous_fluid') or metadata.get('oil_fluid'))

        if core_missing:
            # Core information missing - cannot perform meaningful analysis
            return 'failed'
        elif not important_missing and fluid_info_available:
            # All important fields present plus fluid information
            return 'complete'
        elif len(important_missing) <= 1:
            # Most important fields present, usable for analysis
            return 'partial'
        else:
            # Missing multiple important fields, limited utility
            return 'minimal'

    def batch_extract(self, file_paths: List[str], file_metadata: Optional[List[Dict]] = None) -> List[Dict]:
        """
        Extract metadata from multiple file paths.

        Args:
            file_paths: List of file path strings
            file_metadata: Optional list of file metadata dicts from scanner (includes local_path)

        Returns:
            List of metadata dicts
        """
        results = []

        for i, path in enumerate(file_paths):
            try:
                # Get local path if file_metadata is provided
                local_path = None
                if file_metadata and i < len(file_metadata):
                    local_path = file_metadata[i].get('local_path')

                metadata = self.extract_from_path(path, local_path=local_path)
                results.append(metadata)
            except Exception as e:
                logger.error(f"❌ Error extracting from {path}: {e}")
                results.append({
                    'raw_path': path,
                    'error': str(e),
                    'parse_quality': 'failed'
                })

        logger.info(f"✓ Extracted metadata from {len(results)} files")
        return results


# Example usage
if __name__ == "__main__":
    extractor = MetadataExtractor()

    # Test with example path
    test_path = "W13_S1_R2/06102025/23102025/NaCas_SO/5mlhr150mbar/dfu_measure/DFU1.csv"

    metadata = extractor.extract_from_path(test_path)

    print("\n📊 Extracted Metadata:")
    for key, value in metadata.items():
        print(f"  {key}: {value}")
