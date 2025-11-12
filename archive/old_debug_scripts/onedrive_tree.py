#!/usr/bin/env python3
"""
OneDrive Folder Tree Script
Accesses OneDrive via Microsoft Graph API and displays folder/file tree structure
"""

import msal
import requests
import json
import base64
from datetime import datetime
from typing import Dict, List, Optional, Tuple


# Azure AD App Configuration
# You can use the public client ID for Microsoft Graph Explorer for testing
CLIENT_ID = "14d82eec-204b-4c2f-b7e8-296a70dab67e"  # Microsoft Graph Explorer public client
AUTHORITY = "https://login.microsoftonline.com/common"
SCOPES = ["Files.Read", "Files.Read.All", "Sites.Read.All"]

GRAPH_API_ENDPOINT = "https://graph.microsoft.com/v1.0"


def get_access_token() -> Optional[str]:
    """
    Authenticate user and get access token using interactive flow
    """
    app = msal.PublicClientApplication(
        CLIENT_ID,
        authority=AUTHORITY
    )

    # Try to get token from cache first
    accounts = app.get_accounts()
    if accounts:
        result = app.acquire_token_silent(SCOPES, account=accounts[0])
        if result and "access_token" in result:
            print("Token acquired from cache")
            return result["access_token"]

    # If no cached token, use interactive flow
    print("No cached token found. Opening browser for authentication...")
    result = app.acquire_token_interactive(SCOPES)

    if "access_token" in result:
        print("Authentication successful!\n")
        return result["access_token"]
    else:
        print(f"Authentication failed: {result.get('error')}")
        print(f"Error description: {result.get('error_description')}")
        return None


def encode_sharing_link(sharing_url: str) -> str:
    """
    Encode a OneDrive/SharePoint sharing URL for use with Graph API

    Args:
        sharing_url: The sharing URL from OneDrive/SharePoint

    Returns:
        Base64-encoded sharing token
    """
    # Remove any query parameters and encode to base64
    base_url = sharing_url.split('?')[0] if '?' in sharing_url else sharing_url
    encoded_bytes = base64.urlsafe_b64encode(base_url.encode('utf-8'))
    encoded_str = encoded_bytes.decode('utf-8').rstrip('=')
    return f"u!{encoded_str}"


def get_item_from_sharing_link(access_token: str, sharing_url: str) -> Optional[Tuple[str, str, str]]:
    """
    Get the drive item ID, name, and drive ID from a OneDrive/SharePoint sharing link

    Args:
        access_token: Microsoft Graph API access token
        sharing_url: The sharing URL

    Returns:
        Tuple of (item_id, item_name, drive_id) or None if failed
    """
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    encoded_url = encode_sharing_link(sharing_url)
    url = f"{GRAPH_API_ENDPOINT}/shares/{encoded_url}/driveItem"

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
            print("Could not retrieve item ID or drive ID from sharing link")
            return None
    except requests.exceptions.HTTPError as e:
        print(f"Error accessing shared link: {e}")
        if e.response.status_code == 403:
            print("Permission denied. Make sure you have access to this folder.")
        elif e.response.status_code == 404:
            print("Folder not found. Check if the sharing link is valid.")
        return None


def get_onedrive_items(access_token: str, item_id: str = "root", drive_id: Optional[str] = None) -> List[Dict]:
    """
    Get children items from a OneDrive folder

    Args:
        access_token: Microsoft Graph API access token
        item_id: The folder ID or 'root' for root folder
        drive_id: Optional drive ID for SharePoint/shared drives

    Returns:
        List of items (files and folders)
    """
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    # Use different endpoint for SharePoint drives vs personal OneDrive
    if drive_id:
        url = f"{GRAPH_API_ENDPOINT}/drives/{drive_id}/items/{item_id}/children"
    else:
        url = f"{GRAPH_API_ENDPOINT}/me/drive/items/{item_id}/children"

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        return data.get("value", [])
    except requests.exceptions.HTTPError as e:
        print(f"Error accessing OneDrive: {e}")
        return []


def print_tree(access_token: str, item_id: str = "root", prefix: str = "", is_last: bool = True, item_name: str = "OneDrive Root", drive_id: Optional[str] = None, output_lines: Optional[List[str]] = None):
    """
    Recursively print the folder/file tree structure

    Args:
        access_token: Microsoft Graph API access token
        item_id: Current folder ID
        prefix: Prefix for tree formatting
        is_last: Whether this is the last item in current level
        item_name: Name of the current item
        drive_id: Optional drive ID for SharePoint/shared drives
        output_lines: Optional list to collect output lines for file export
    """
    # Print current item
    connector = "└── " if is_last else "├── "
    line = f"{prefix}{connector}{item_name}"
    print(line)

    # Collect for export if list provided
    if output_lines is not None:
        output_lines.append(line)

    # Get children
    items = get_onedrive_items(access_token, item_id, drive_id)

    if not items:
        return

    # Sort items: folders first, then files
    items.sort(key=lambda x: (not ("folder" in x), x.get("name", "").lower()))

    # Update prefix for children
    extension = "    " if is_last else "│   "
    new_prefix = prefix + extension

    # Process each child
    for idx, item in enumerate(items):
        is_last_child = (idx == len(items) - 1)
        item_name = item.get("name", "Unknown")

        # Add folder/file indicator
        if "folder" in item:
            item_name = f"📁 {item_name}"
            # Recursively process folders
            print_tree(
                access_token,
                item["id"],
                new_prefix,
                is_last_child,
                item_name,
                drive_id,
                output_lines
            )
        else:
            file_size = item.get("size", 0)
            size_str = format_size(file_size)
            item_name = f"📄 {item_name} ({size_str})"
            connector = "└── " if is_last_child else "├── "
            line = f"{new_prefix}{connector}{item_name}"
            print(line)

            # Collect for export if list provided
            if output_lines is not None:
                output_lines.append(line)


def format_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format

    Args:
        size_bytes: Size in bytes

    Returns:
        Formatted size string
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} PB"


def main():
    """
    Main function to run the OneDrive tree script
    """
    print("=" * 60)
    print("OneDrive Folder Tree Viewer")
    print("=" * 60)
    print()

    # Authenticate
    access_token = get_access_token()
    if not access_token:
        print("Failed to authenticate. Exiting...")
        return

    # Get sharing link from user
    print("Enter the OneDrive/SharePoint sharing link to the folder:")
    print("(Leave blank to view your entire OneDrive)")
    sharing_link = input("> ").strip()

    # Create list to collect output for file export
    output_lines = []
    folder_name = "OneDrive"

    if sharing_link:
        # Use the sharing link to get the specific folder
        print("\nResolving sharing link...")
        result = get_item_from_sharing_link(access_token, sharing_link)

        if not result:
            print("Failed to access the shared folder. Exiting...")
            return

        item_id, folder_name, drive_id = result
        print(f"Found folder: {folder_name}\n")
        print("Fetching folder structure...\n")
        print_tree(access_token, item_id=item_id, item_name=f"📁 {folder_name}", drive_id=drive_id, output_lines=output_lines)
    else:
        # Default: show entire OneDrive
        print("Fetching OneDrive structure...\n")
        print_tree(access_token, output_lines=output_lines)

    print("\n" + "=" * 60)
    print("Done!")

    # Export to file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"onedrive_tree_{timestamp}.txt"

    try:
        with open(filename, "w", encoding="utf-8") as f:
            # Write header
            f.write("=" * 60 + "\n")
            f.write("OneDrive Folder Tree Export\n")
            f.write(f"Folder: {folder_name}\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 60 + "\n\n")

            # Write tree structure
            f.write("\n".join(output_lines))

            # Write footer
            f.write("\n\n" + "=" * 60 + "\n")
            f.write(f"Total items: {len(output_lines)}\n")
            f.write("=" * 60 + "\n")

        print(f"\nTree exported to: {filename}")
    except Exception as e:
        print(f"\nError exporting to file: {e}")


if __name__ == "__main__":
    main()
