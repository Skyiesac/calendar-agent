# Credentials Directory

This directory should contain your Google Calendar API service account credentials.

## Required File

Place your `service_account.json` file in this directory. This file should be downloaded from the Google Cloud Console after creating a service account.

## File Structure

```
credentials/
├── README.md
└── service_account.json  # Place your Google service account JSON here
```

## Security Note

⚠️ **Important**: Never commit the `service_account.json` file to version control. This file contains sensitive credentials.


## Getting the Service Account JSON

### 1. Google Calendar Service Account Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable the Google Calendar API
4. Create a Service Account:
   - Go to "IAM & Admin" > "Service Accounts"
   - Click "Create Service Account"
   - Name it "calendar-booking-agent"
   - Grant "Editor" role
5. Create and download the JSON key:
   - Click on the service account
   - Go to "Keys" tab
   - Click "Add Key" > "Create new key"
   - Choose JSON format
   - Download the file as `service_account.json`
6. Place the downloaded file in `credentials/service_account.json`

### 2. Share Google Calendar

1. Open your Google Calendar
2. Find the calendar you want to use (or create a new one)
3. Click the three dots next to the calendar name
4. Select "Settings and sharing"
5. Scroll down to "Share with specific people"
6. Add your service account email (found in the JSON file)
7. Grant "Make changes to events" permission
