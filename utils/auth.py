"""
Authentication utilities for Microsoft Graph API and SharePoint access.
"""

import os
from msal import ConfidentialClientApplication
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class SharePointAuthenticator:
    """Handles authentication for SharePoint via Microsoft Graph API."""

    def __init__(self):
        self.client_id = os.getenv('CLIENT_ID')
        self.client_secret = os.getenv('CLIENT_SECRET')
        self.tenant_id = os.getenv('TENANT_ID')

        if not all([self.client_id, self.client_secret, self.tenant_id]):
            raise ValueError(
                "Missing authentication credentials. "
                "Please set CLIENT_ID, CLIENT_SECRET, and TENANT_ID in .env file"
            )

        self.authority = f"https://login.microsoftonline.com/{self.tenant_id}"
        self.scopes = ["https://graph.microsoft.com/.default"]

        # Create MSAL client
        self.app = ConfidentialClientApplication(
            self.client_id,
            authority=self.authority,
            client_credential=self.client_secret
        )

    def get_access_token(self):
        """Get access token for Microsoft Graph API."""
        result = self.app.acquire_token_silent(self.scopes, account=None)

        if not result:
            result = self.app.acquire_token_for_client(scopes=self.scopes)

        if "access_token" in result:
            return result["access_token"]
        else:
            error = result.get("error")
            error_description = result.get("error_description")
            raise Exception(f"Authentication failed: {error} - {error_description}")

    def get_graph_headers(self):
        """Get headers for Microsoft Graph API requests."""
        token = self.get_access_token()
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }


def authenticate():
    """Create and return authenticated SharePoint client."""
    return SharePointAuthenticator()


def get_graph_client():
    """Get authenticated Microsoft Graph API client."""
    auth = authenticate()
    return auth
