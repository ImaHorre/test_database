"""
Local Scanner Agent

Handles local file system scanning and file discovery.
Communicates with Extractor agent to pass discovered files for metadata extraction.
"""

import os
from typing import List, Dict, Optional
from datetime import datetime
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LocalScanner:
    """
    Scans local file system directory structure.

    Expected directory structure (7-8 levels):
    1. Device ID (W13_S1_R4)
    2. Bonding Date (06102025 or 0610)
    3. Testing Date (23102025 or 2310, sometimes absent)
    4. Fluids (NaCas_SO, SDS_SO, sometimes absent)
    5. Flow Parameters (5mlhr150mbar)
    6. Measurement folders (dfu_measure/, freq_analysis/)
    7. Data files (CSV/TXT)
    """

    def __init__(self, exclude_dirs=None):
        """Initialize local scanner (no authentication needed).

        Args:
            exclude_dirs: List of directory names to exclude from scanning (default: Archive, outputs, tool folders)
        """
        self.exclude_dirs = exclude_dirs if exclude_dirs is not None else [
            'Archive',
            'outputs',
            '0_dfu_measure_tools',
            '0_freq_analysis_tools'
        ]
        logger.info(f"✓ LocalScanner initialized (excluding: {', '.join(self.exclude_dirs)})")

    def traverse_local_structure(self, local_root_path: str, max_depth: int = 8) -> List[Dict]:
        """
        Recursively traverse local directory structure and discover all measurement files.

        Args:
            local_root_path: Local file system path to scan (e.g., "fake_onedrive_database/")
            max_depth: Maximum recursion depth

        Returns:
            List of discovered file paths with metadata
        """
        discovered_files = []

        # Convert to absolute path if relative
        root_path = Path(local_root_path).resolve()

        if not root_path.exists():
            logger.error(f"❌ Path does not exist: {root_path}")
            return []

        if not root_path.is_dir():
            logger.error(f"❌ Path is not a directory: {root_path}")
            return []

        def _traverse(current_path: Path, depth: int, relative_path: str):
            """Recursively traverse directory structure."""
            if depth > max_depth:
                return

            try:
                for item in sorted(current_path.iterdir()):
                    item_name = item.name
                    # Build relative path from root
                    new_relative = f"{relative_path}/{item_name}" if relative_path else item_name

                    if item.is_dir():
                        # Check if this directory should be excluded
                        if item_name in self.exclude_dirs:
                            logger.info(f"{'  ' * depth}⊘ {item_name} (excluded)")
                            continue

                        # It's a folder, recurse into it
                        logger.info(f"{'  ' * depth}📁 {item_name}")
                        _traverse(item, depth + 1, new_relative)

                    elif item.is_file():
                        # Only collect CSV and TXT files
                        if item.suffix.lower() in ['.csv', '.txt']:
                            # Get file metadata
                            stat_info = item.stat()

                            file_info = {
                                'name': item_name,
                                'path': new_relative,  # Relative path
                                'local_path': str(item),  # Absolute path for reading
                                'size': stat_info.st_size,
                                'modified': datetime.fromtimestamp(stat_info.st_mtime).isoformat(),
                                'file_url': f"file://{item.resolve()}"  # file:// URL
                            }

                            logger.info(f"{'  ' * depth}📄 {item_name}")
                            discovered_files.append(file_info)

            except PermissionError as e:
                logger.warning(f"⚠ Permission denied accessing {current_path}: {e}")
            except Exception as e:
                logger.error(f"❌ Error traversing {current_path}: {e}")

        logger.info(f"🔍 Starting local scan from: {root_path}")
        _traverse(root_path, 0, "")
        logger.info(f"✓ Scan complete. Found {len(discovered_files)} measurement files")

        return discovered_files

    def read_file_content(self, file_info: Dict) -> Optional[str]:
        """
        Read content of a local file.

        Args:
            file_info: File metadata dict from traverse_local_structure()

        Returns:
            File content as string, or None if read fails
        """
        local_path = file_info.get('local_path')

        if not local_path:
            logger.error("File info missing local_path")
            return None

        try:
            with open(local_path, 'r', encoding='utf-8') as f:
                content = f.read()
            logger.info(f"✓ Read file: {file_info.get('name')}")
            return content

        except Exception as e:
            logger.error(f"❌ Error reading file {local_path}: {e}")
            return None


# Example usage
if __name__ == "__main__":
    scanner = LocalScanner()

    # Discover all files
    files = scanner.traverse_local_structure("fake_onedrive_database")

    print(f"\n📊 Summary:")
    print(f"Total files found: {len(files)}")

    # Group by file type
    csv_files = [f for f in files if f['name'].endswith('.csv')]
    txt_files = [f for f in files if f['name'].endswith('.txt')]

    print(f"CSV files: {len(csv_files)}")
    print(f"TXT files: {len(txt_files)}")
