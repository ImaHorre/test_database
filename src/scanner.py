"""
SharePoint Scanner Agent

Handles SharePoint/OneDrive authentication, directory traversal, and file discovery.
Also supports LOCAL file system scanning for testing.
Communicates with Extractor agent to pass discovered files for metadata extraction.
"""

import os
import requests
from typing import List, Dict, Optional
from datetime import datetime
from dotenv import load_dotenv
import logging
from pathlib import Path

from utils.auth import get_graph_client

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SharePointScanner:
    """
    Scans SharePoint directory structure and discovers measurement files.

    Expected directory structure (7-8 levels):
    1. Device ID (W13_S1_R4)
    2. Bonding Date (06102025 or 0610)
    3. Testing Date (23102025 or 2310, sometimes absent)
    4. Fluids (NaCas_SO, SDS_SO, sometimes absent)
    5. Flow Parameters (5mlhr150mbar)
    6. Measurement folders (dfu_measure/, freq_analysis/)
    7. Data files (CSV/TXT)
    """

    def __init__(self):
        self.auth = get_graph_client()
        self.site_url = os.getenv('SHAREPOINT_SITE_URL')
        self.root_path = os.getenv('SHAREPOINT_ROOT_PATH')
        self.graph_base = "https://graph.microsoft.com/v1.0"

        if not self.site_url or not self.root_path:
            raise ValueError(
                "Missing SharePoint configuration. "
                "Please set SHAREPOINT_SITE_URL and SHAREPOINT_ROOT_PATH in .env"
            )

        self.site_id = None
        self.drive_id = None

    def _get_site_id(self):
        """Get SharePoint site ID from site URL."""
        # Parse site URL to extract host and site path
        # Example: https://peakemulsions.sharepoint.com/sites/Techteam
        parts = self.site_url.replace('https://', '').split('/')
        host = parts[0]
        site_path = '/'.join(parts[1:])

        url = f"{self.graph_base}/sites/{host}:/{site_path}"
        headers = self.auth.get_graph_headers()

        response = requests.get(url, headers=headers)
        response.raise_for_status()

        data = response.json()
        self.site_id = data.get('id')
        logger.info(f"✓ Retrieved site ID: {self.site_id}")
        return self.site_id

    def _get_drive_id(self):
        """Get drive ID for the SharePoint document library."""
        if not self.site_id:
            self._get_site_id()

        url = f"{self.graph_base}/sites/{self.site_id}/drives"
        headers = self.auth.get_graph_headers()

        response = requests.get(url, headers=headers)
        response.raise_for_status()

        data = response.json()
        # Get the default document library drive
        drives = data.get('value', [])
        if drives:
            self.drive_id = drives[0]['id']
            logger.info(f"✓ Retrieved drive ID: {self.drive_id}")
            return self.drive_id
        else:
            raise Exception("No drives found in SharePoint site")

    def get_folder_contents(self, folder_path: str) -> List[Dict]:
        """
        Get contents of a folder in SharePoint.

        Args:
            folder_path: Path relative to root (e.g., "W13_S1_R2/06102025")

        Returns:
            List of items (folders and files) with metadata
        """
        if not self.drive_id:
            self._get_drive_id()

        # Construct full path
        full_path = f"{self.root_path}/{folder_path}" if folder_path else self.root_path

        # URL encode the path
        url = f"{self.graph_base}/drives/{self.drive_id}/root:/{full_path}:/children"
        headers = self.auth.get_graph_headers()

        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()

            data = response.json()
            items = data.get('value', [])

            logger.info(f"✓ Found {len(items)} items in {folder_path}")
            return items

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                logger.warning(f"⚠ Folder not found: {folder_path}")
                return []
            else:
                raise

    def traverse_structure(self, start_path: str = "", max_depth: int = 8) -> List[Dict]:
        """
        Recursively traverse directory structure and discover all measurement files.

        Args:
            start_path: Starting path relative to root
            max_depth: Maximum recursion depth

        Returns:
            List of discovered file paths with metadata
        """
        discovered_files = []

        def _traverse(path: str, depth: int):
            if depth > max_depth:
                return

            items = self.get_folder_contents(path)

            for item in items:
                item_name = item.get('name')
                item_path = f"{path}/{item_name}" if path else item_name

                if 'folder' in item:
                    # It's a folder, recurse into it
                    logger.info(f"{'  ' * depth}📁 {item_name}")
                    _traverse(item_path, depth + 1)

                elif 'file' in item:
                    # It's a file
                    file_info = {
                        'name': item_name,
                        'path': item_path,
                        'size': item.get('size'),
                        'modified': item.get('lastModifiedDateTime'),
                        'download_url': item.get('@microsoft.graph.downloadUrl'),
                        'web_url': item.get('webUrl')
                    }

                    # Only collect CSV and TXT files
                    if item_name.endswith(('.csv', '.txt')):
                        logger.info(f"{'  ' * depth}📄 {item_name}")
                        discovered_files.append(file_info)

        logger.info(f"🔍 Starting scan from: {start_path or 'root'}")
        _traverse(start_path, 0)
        logger.info(f"✓ Scan complete. Found {len(discovered_files)} measurement files")

        return discovered_files

    def get_changed_files_since(self, timestamp: datetime) -> List[Dict]:
        """
        Get files that have been modified since a specific timestamp.

        Args:
            timestamp: Datetime to check against

        Returns:
            List of files modified after timestamp
        """
        all_files = self.traverse_structure()

        changed_files = []
        for file in all_files:
            modified_str = file.get('modified')
            if modified_str:
                # Parse ISO 8601 datetime
                modified_dt = datetime.fromisoformat(modified_str.replace('Z', '+00:00'))
                if modified_dt > timestamp:
                    changed_files.append(file)

        logger.info(f"✓ Found {len(changed_files)} files modified since {timestamp}")
        return changed_files

    def download_file(self, file_info: Dict, local_path: str) -> str:
        """
        Download a file from SharePoint to local path.

        Args:
            file_info: File metadata dict from traverse_structure()
            local_path: Local directory to save file

        Returns:
            Path to downloaded file
        """
        download_url = file_info.get('download_url')
        file_name = file_info.get('name')

        if not download_url:
            raise ValueError("File info missing download URL")

        # Create directory if it doesn't exist
        os.makedirs(local_path, exist_ok=True)

        # Download file
        response = requests.get(download_url)
        response.raise_for_status()

        local_file_path = os.path.join(local_path, file_name)
        with open(local_file_path, 'wb') as f:
            f.write(response.content)

        logger.info(f"✓ Downloaded: {file_name} -> {local_file_path}")
        return local_file_path


class LocalScanner:
    """
    Scans local file system directory structure for testing.

    Mirrors the SharePointScanner interface but works with local files.
    Useful for testing before deploying to SharePoint.
    """

    def __init__(self):
        """Initialize local scanner (no authentication needed)."""
        logger.info("✓ LocalScanner initialized (no auth required)")

    def traverse_local_structure(self, local_root_path: str, max_depth: int = 8) -> List[Dict]:
        """
        Recursively traverse local directory structure and discover all measurement files.

        Args:
            local_root_path: Local file system path to scan (e.g., "fake_onedrive_database/")
            max_depth: Maximum recursion depth

        Returns:
            List of discovered file paths with metadata (same structure as SharePointScanner)
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
                                'path': new_relative,  # Relative path like SharePoint
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
    scanner = SharePointScanner()

    # Discover all files
    files = scanner.traverse_structure()

    print(f"\n📊 Summary:")
    print(f"Total files found: {len(files)}")

    # Group by file type
    csv_files = [f for f in files if f['name'].endswith('.csv')]
    txt_files = [f for f in files if f['name'].endswith('.txt')]

    print(f"CSV files: {len(csv_files)}")
    print(f"TXT files: {len(txt_files)}")
