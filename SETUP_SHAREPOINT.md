# SharePoint Authentication Setup Guide

To access your SharePoint site via Microsoft Graph API, you need to create an Azure AD App Registration.

## Step 1: Register an App in Azure AD

1. Go to [Azure Portal](https://portal.azure.com)
2. Navigate to: **Azure Active Directory** → **App registrations** → **New registration**

3. Fill in:
   - **Name**: `OneDrive Database Scanner` (or any name)
   - **Supported account types**: "Accounts in this organizational directory only"
   - **Redirect URI**: Leave blank for now
   - Click **Register**

4. After registration, you'll see:
   - **Application (client) ID** - Copy this for CLIENT_ID
   - **Directory (tenant) ID** - Copy this for TENANT_ID

## Step 2: Create Client Secret

1. In your app registration, go to: **Certificates & secrets** → **Client secrets** → **New client secret**

2. Fill in:
   - **Description**: `Scanner App Secret`
   - **Expires**: Choose duration (6 months, 12 months, etc.)
   - Click **Add**

3. **IMPORTANT**: Copy the **Value** immediately (you won't be able to see it again)
   - This is your CLIENT_SECRET

## Step 3: Grant API Permissions

1. In your app registration, go to: **API permissions** → **Add a permission**

2. Select **Microsoft Graph** → **Application permissions**

3. Add these permissions:
   - ✅ `Sites.Read.All` - Read items in all site collections
   - ✅ `Files.Read.All` - Read files in all site collections

4. Click **Add permissions**

5. **IMPORTANT**: Click **Grant admin consent for [Your Organization]**
   - You need admin privileges for this
   - If you don't have admin rights, ask your IT admin to grant consent

## Step 4: Get Your SharePoint Site Info

Your SharePoint URL from the link you provided:
```
https://peakemulsions-my.sharepoint.com/sites/Techteam
```

Breaking this down:
- **Site URL**: `https://peakemulsions.sharepoint.com/sites/Techteam`
  - Note: Remove `-my` from the URL for the site
- **Root Path**: `Shared Documents/Product/test_database`

## Step 5: Create .env File

Copy `.env.template` to `.env` and fill in your values:

```bash
cp .env.template .env
```

Then edit `.env`:

```env
# From Azure App Registration
CLIENT_ID=your-client-id-here
CLIENT_SECRET=your-client-secret-here
TENANT_ID=your-tenant-id-here

# SharePoint Site (without -my)
SHAREPOINT_SITE_URL=https://peakemulsions.sharepoint.com/sites/Techteam
SHAREPOINT_ROOT_PATH=Shared Documents/Product/test_database

# Database files
CSV_DATABASE_PATH=data/database.csv
LAST_SCAN_TIMESTAMP_FILE=data/last_scan.txt

# Logging
LOG_LEVEL=INFO
```

## Step 6: Test Connection

Once you have your `.env` file set up, test the connection:

```bash
python -m agents.scanner
```

This will attempt to:
1. Authenticate with Azure AD
2. Connect to your SharePoint site
3. Traverse the directory structure
4. List all discovered files

## Troubleshooting

**Error: "Authentication failed"**
- Check CLIENT_ID, CLIENT_SECRET, TENANT_ID are correct
- Make sure client secret hasn't expired

**Error: "Forbidden" or "Access Denied"**
- Verify API permissions are granted
- Check admin consent was given
- Wait 5-10 minutes after granting permissions

**Error: "Site not found"**
- Verify SHAREPOINT_SITE_URL is correct
- Remove `-my` from the URL if present
- Check you have access to the site

## Security Notes

⚠️ **Never commit your .env file to git!**

The `.gitignore` file already excludes `.env`, but double-check:
```bash
git status
# .env should NOT appear in the list
```

Keep your CLIENT_SECRET secure - it grants access to all your SharePoint files.
