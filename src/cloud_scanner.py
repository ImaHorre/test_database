"""
Cloud Scanner Agent

Handles OneDrive cloud scanning via Microsoft Graph API.
Provides the same interface as LocalScanner for seamless integration.
"""

import msal
import requests
import base64
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CloudScanner:
    """
    Scans OneDrive cloud storage via Microsoft Graph API.

    Uses Microsoft Graph Explorer public client for authentication.
    Returns data in the same format as LocalScanner for compatibility.
    """

    # Azure AD App Configuration (Microsoft Graph Explorer public client)
    CLIENT_ID = "14d82eec-204b-4c2f-b7e8-296a70dab67e"
    AUTHORITY = "https://login.microsoftonline.com/common"
    SCOPES = ["Files.Read", "Files.Read.All", "Sites.Read.All"]
    GRAPH_API_ENDPOINT = "https://graph.microsoft.com/v1.0"

    def __init__(self, exclude_dirs=None):
        """Initialize cloud scanner.

        Args:
            exclude_dirs: List of directory names to exclude from scanning
        """
        self.exclude_dirs = exclude_dirs if exclude_dirs is not None else [
            'Archive',
            'outputs',
            '0_dfu_measure_tools',
            '0_freq_analysis_tools'
        ]
        self.access_token = None
        logger.info(f"✓ CloudScanner initialized (excluding: {', '.join(self.exclude_dirs)})")

    def authenticate(self) -> bool:
        """
        Authenticate user and get access token using interactive flow.

        Returns:
            True if authentication successful, False otherwise
        """
        app = msal.PublicClientApplication(
            self.CLIENT_ID,
            authority=self.AUTHORITY
        )

        # Try to get token from cache first
        accounts = app.get_accounts()
        if accounts:
            result = app.acquire_token_silent(self.SCOPES, account=accounts[0])
            if result and "access_token" in result:
                logger.info("✓ Token acquired from cache")
                self.access_token = result["access_token"]
                return True

        # If no cached token, use interactive flow
        logger.info("🔐 No cached token found. Opening browser for authentication...")
        result = app.acquire_token_interactive(self.SCOPES)

        if "access_token" in result:
            logger.info("✓ Authentication successful!")
            self.access_token = result["access_token"]
            return True
        else:
            logger.error(f"❌ Authentication failed: {result.get('error')}")
            logger.error(f"Error description: {result.get('error_description')}")
            return False

    def _encode_sharing_link(self, sharing_url: str) -> str:
        """
        Encode a OneDrive/SharePoint sharing URL for use with Graph API.

        Args:
            sharing_url: The sharing URL from OneDrive/SharePoint

        Returns:
            Base64-encoded sharing token
        """
        base_url = sharing_url.split('?')[0] if '?' in sharing_url else sharing_url
        encoded_bytes = base64.urlsafe_b64encode(base_url.encode('utf-8'))
        encoded_str = encoded_bytes.decode('utf-8').rstrip('=')
        return f"u!{encoded_str}"

    def _get_item_from_sharing_link(self, sharing_url: str) -> Optional[Tuple[str, str, str]]:
        """
        Get the drive item ID, name, and drive ID from a OneDrive/SharePoint sharing link.

        Args:
            sharing_url: The sharing URL

        Returns:
            Tuple of (item_id, item_name, drive_id) or None if failed
        """
        if not self.access_token:
            logger.error("❌ Not authenticated. Call authenticate() first.")
            return None

        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }

        encoded_url = self._encode_sharing_link(sharing_url)
        url = f"{self.GRAPH_API_ENDPOINT}/shares/{encoded_url}/driveItem"

        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()

            item_id = data.get("id")
            item_name = data.get("name", "Shared Folder")

            # Get the drive ID from the parent reference
            drive_id = None
            if "parentReference" in data and "driveId" in data["parentReference"]:
                drive_id = data["parentReference"]["driveId"]

            if item_id and drive_id:
                return (item_id, item_name, drive_id)
            else:
                logger.error("❌ Could not retrieve item ID or drive ID from sharing link")
                return None

        except requests.exceptions.HTTPError as e:
            logger.error(f"❌ Error accessing shared link: {e}")
            if e.response.status_code == 403:
                logger.error("Permission denied. Make sure you have access to this folder.")
            elif e.response.status_code == 404:
                logger.error("Folder not found. Check if the sharing link is valid.")
            return None

    def _get_children(self, item_id: str, drive_id: str) -> List[Dict]:
        """
        Get children items from a OneDrive folder.

        Args:
            item_id: The folder ID
            drive_id: The drive ID

        Returns:
            List of items (files and folders)
        """
        if not self.access_token:
            logger.error("❌ Not authenticated. Call authenticate() first.")
            return []

        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }

        url = f"{self.GRAPH_API_ENDPOINT}/drives/{drive_id}/items/{item_id}/children"

        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            return data.get("value", [])
        except requests.exceptions.HTTPError as e:
            logger.error(f"❌ Error accessing OneDrive: {e}")
            return []

    def traverse_cloud_structure(self, sharing_url: str, max_depth: int = 8) -> List[Dict]:
        """
        Recursively traverse OneDrive cloud structure and discover all measurement files.

        Args:
            sharing_url: OneDrive sharing link to the root folder
            max_depth: Maximum recursion depth

        Returns:
            List of discovered file paths with metadata (same format as LocalScanner)
        """
        discovered_files = []

        # Authenticate if not already done
        if not self.access_token:
            if not self.authenticate():
                logger.error("❌ Authentication failed. Cannot proceed with scan.")
                return []

        # Resolve sharing link to get item ID and drive ID
        logger.info("🔍 Resolving sharing link...")
        result = self._get_item_from_sharing_link(sharing_url)

        if not result:
            logger.error("❌ Failed to access the shared folder.")
            return []

        item_id, folder_name, drive_id = result
        logger.info(f"✓ Found folder: {folder_name}")
        logger.info(f"🔍 Starting cloud scan...")

        def _traverse(current_item_id: str, depth: int, relative_path: str, current_name: str):
            """Recursively traverse directory structure."""
            if depth > max_depth:
                return

            logger.info(f"{'  ' * depth}📁 {current_name}")

            # Get children of current folder
            items = self._get_children(current_item_id, drive_id)

            # Sort items: folders first, then files
            items.sort(key=lambda x: (not ("folder" in x), x.get("name", "").lower()))

            for item in items:
                item_name = item.get("name", "Unknown")
                new_relative = f"{relative_path}/{item_name}" if relative_path else item_name

                if "folder" in item:
                    # Check if this directory should be excluded
                    if item_name in self.exclude_dirs:
                        logger.info(f"{'  ' * (depth + 1)}⊘ {item_name} (excluded)")
                        continue

                    # It's a folder, recurse into it
                    _traverse(item["id"], depth + 1, new_relative, item_name)

                else:
                    # It's a file
                    file_extension = item_name.split('.')[-1].lower() if '.' in item_name else ''

                    # Only collect CSV and TXT files
                    if file_extension in ['csv', 'txt']:
                        # Get file metadata
                        modified_time = item.get("lastModifiedDateTime", "")
                        if modified_time:
                            # Convert ISO format to datetime
                            try:
                                modified_dt = datetime.fromisoformat(modified_time.replace('Z', '+00:00'))
                                modified_iso = modified_dt.isoformat()
                            except:
                                modified_iso = modified_time
                        else:
                            modified_iso = datetime.now().isoformat()

                        file_info = {
                            'name': item_name,
                            'path': new_relative,  # Relative path
                            'cloud_id': item["id"],  # Cloud item ID for downloading
                            'drive_id': drive_id,  # Drive ID for downloading
                            'size': item.get("size", 0),
                            'modified': modified_iso,
                            'file_url': item.get("webUrl", ""),  # Web URL
                            'download_url': item.get("@microsoft.graph.downloadUrl", "")  # Direct download URL
                        }

                        logger.info(f"{'  ' * (depth + 1)}📄 {item_name}")
                        discovered_files.append(file_info)

        # Start traversal from root
        _traverse(item_id, 0, "", folder_name)
        logger.info(f"✓ Cloud scan complete. Found {len(discovered_files)} measurement files")

        return discovered_files

    def read_file_content(self, file_info: Dict) -> Optional[str]:
        """
        Read content of a cloud file.

        Args:
            file_info: File metadata dict from traverse_cloud_structure()

        Returns:
            File content as string, or None if read fails
        """
        download_url = file_info.get('download_url')

        if not download_url:
            # If no direct download URL, construct it from cloud_id and drive_id
            cloud_id = file_info.get('cloud_id')
            drive_id = file_info.get('drive_id')

            if not cloud_id or not drive_id:
                logger.error("❌ File info missing cloud_id, drive_id, or download_url")
                return None

            if not self.access_token:
                logger.error("❌ Not authenticated. Call authenticate() first.")
                return None

            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }

            url = f"{self.GRAPH_API_ENDPOINT}/drives/{drive_id}/items/{cloud_id}/content"

            try:
                response = requests.get(url, headers=headers)
                response.raise_for_status()
                content = response.text
                logger.info(f"✓ Read file: {file_info.get('name')}")
                return content
            except Exception as e:
                logger.error(f"❌ Error reading file {file_info.get('name')}: {e}")
                return None
        else:
            # Use direct download URL (no auth required, temporary URL)
            try:
                response = requests.get(download_url)
                response.raise_for_status()
                content = response.text
                logger.info(f"✓ Read file: {file_info.get('name')}")
                return content
            except Exception as e:
                logger.error(f"❌ Error reading file {file_info.get('name')}: {e}")
                return None


# Example usage
if __name__ == "__main__":
    scanner = CloudScanner()

    # Authenticate
    if scanner.authenticate():
        print("\n" + "=" * 60)
        print("Enter the OneDrive sharing link to the root folder:")
        sharing_link = input("> ").strip()

        if sharing_link:
            # Discover all files
            files = scanner.traverse_cloud_structure(sharing_link)

            print(f"\n📊 Summary:")
            print(f"Total files found: {len(files)}")

            # Group by file type
            csv_files = [f for f in files if f['name'].endswith('.csv')]
            txt_files = [f for f in files if f['name'].endswith('.txt')]

            print(f"CSV files: {len(csv_files)}")
            print(f"TXT files: {len(txt_files)}")
        else:
            print("❌ No sharing link provided.")
    else:
        print("❌ Authentication failed.")
