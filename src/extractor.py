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
import requests
from io import StringIO

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

    def parse_date(self, date_str: str) -> Optional[str]:
        """
        Parse date string in various formats.

        Args:
            date_str: e.g., "06102025" or "0610"

        Returns:
            ISO format date string (YYYY-MM-DD) or None
        """
        # Try long format first (DDMMYYYY)
        match = re.match(self.DATE_LONG_PATTERN, date_str)
        if match:
            day = match.group(1)
            month = match.group(2)
            year = match.group(3)
            return f"{year}-{month}-{day}"

        # Try short format (DDMM)
        match = re.match(self.DATE_SHORT_PATTERN, date_str)
        if match:
            day = match.group(1)
            month = match.group(2)
            # Assume current year
            return f"{self.current_year}-{month}-{day}"

        logger.warning(f"⚠ Could not parse date: {date_str}")
        return None

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

    def parse_dfu_csv_content(self, download_url: str) -> Optional[Dict]:
        """
        Parse DFU measurement CSV file content.

        Args:
            download_url: URL to download the CSV file

        Returns:
            Dict with droplet size statistics or None if parsing fails
        """
        try:
            response = requests.get(download_url, timeout=30)
            response.raise_for_status()

            # Parse CSV
            df = pd.read_csv(StringIO(response.text))

            # Extract basic statistics
            stats = {
                'row_count': len(df),
                'columns': df.columns.tolist(),
            }

            # Try to extract droplet size data if column exists
            # Common column names: 'Diameter', 'Size', 'Droplet_Size', etc.
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
            logger.warning(f"⚠ Could not parse CSV content: {e}")
            return None

    def parse_freq_txt_content(self, download_url: str) -> Optional[Dict]:
        """
        Parse frequency analysis TXT file content.

        Args:
            download_url: URL to download the TXT file

        Returns:
            Dict with frequency analysis data or None if parsing fails
        """
        try:
            response = requests.get(download_url, timeout=30)
            response.raise_for_status()

            lines = response.text.strip().split('\n')

            # Basic parsing - extract numeric data
            # Format may vary, so we'll be flexible
            data = {
                'line_count': len(lines),
                'raw_sample': lines[:5] if len(lines) >= 5 else lines  # First 5 lines as sample
            }

            # Try to extract numeric values (frequencies)
            numeric_values = []
            for line in lines:
                try:
                    # Try to parse as float
                    value = float(line.strip())
                    numeric_values.append(value)
                except ValueError:
                    # Skip non-numeric lines
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
            logger.warning(f"⚠ Could not parse TXT content: {e}")
            return None

    def extract_from_path(self, file_path: str, download_url: Optional[str] = None) -> Dict:
        """
        Extract all metadata from a complete file path.

        Args:
            file_path: e.g., "W13_S1_R2/06102025/23102025/NaCas_SO/5mlhr150mbar/dfu_measure/DFU1.csv"
            download_url: Optional URL to download and parse file contents

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
            bonding_date = self.parse_date(parts[1])
            if bonding_date:
                metadata['bonding_date'] = bonding_date

        # Determine if level 2 is a testing date or something else
        next_idx = 2  # Default: start parsing from level 2
        if len(parts) >= 3:
            # Could be testing date or fluids (testing date may be absent)
            # Try parsing as date first
            testing_date = self.parse_date(parts[2])
            if testing_date:
                metadata['testing_date'] = testing_date
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

            # Check if it's measurement type folder
            if part in ['dfu_measure', 'freq_analysis']:
                metadata['measurement_type'] = part
                continue

            # Check if it's a file name (last part)
            if i == len(remaining) - 1 and '.' in part:
                file_data = self.parse_file_name(part)
                if file_data:
                    metadata.update(file_data)
                    metadata['file_name'] = part

        # Parse file contents if download URL is provided
        if download_url:
            file_type = metadata.get('file_type')
            measurement_type = metadata.get('measurement_type')

            if file_type == 'csv' and measurement_type == 'dfu_measure':
                logger.info(f"📊 Parsing DFU CSV content from {metadata.get('file_name')}")
                content_data = self.parse_dfu_csv_content(download_url)
                if content_data:
                    metadata['file_content_data'] = content_data

            elif file_type == 'txt' and measurement_type == 'freq_analysis':
                logger.info(f"📈 Parsing frequency TXT content from {metadata.get('file_name')}")
                content_data = self.parse_freq_txt_content(download_url)
                if content_data:
                    metadata['file_content_data'] = content_data

        # Validate dates
        self._validate_dates(metadata)

        # Add data quality flag
        metadata['parse_quality'] = self._assess_parse_quality(metadata)

        return metadata

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
            'complete', 'partial', or 'incomplete'
        """
        required_fields = [
            'device_type', 'bonding_date', 'aqueous_flowrate',
            'oil_pressure', 'measurement_type', 'dfu_row'
        ]

        missing = [field for field in required_fields if field not in metadata]

        if not missing:
            return 'complete'
        elif len(missing) <= 2:
            return 'partial'
        else:
            return 'incomplete'

    def batch_extract(self, file_paths: List[str], file_metadata: Optional[List[Dict]] = None) -> List[Dict]:
        """
        Extract metadata from multiple file paths.

        Args:
            file_paths: List of file path strings
            file_metadata: Optional list of file metadata dicts from scanner (includes download_url)

        Returns:
            List of metadata dicts
        """
        results = []

        for i, path in enumerate(file_paths):
            try:
                # Get download URL if file_metadata is provided
                download_url = None
                if file_metadata and i < len(file_metadata):
                    download_url = file_metadata[i].get('download_url')

                metadata = self.extract_from_path(path, download_url=download_url)
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
