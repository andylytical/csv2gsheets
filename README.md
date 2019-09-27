# csv2gsheets
Upload data from local CSV file to a Google Sheet


# One Time Setup for access to Google Sheets
Enable Google API access
1. Go to [Google Cloud Platform Credentials Management](https://console.cloud.google.com/apis/credentials)
1. Create a client ID
   1. Click *Credentials* (on the left hand pane)
      1. Create credentials (dropdown) → OAuth client ID
      1. Other
      1. Enter a name: (something like _BrewPi Backups_)
         1. Client ID and Client Secret are displayed, close that pop-up window.
      1.  In the client IDs list, find the client ID row you just created and click the *Download JSON* image. Save the file to your computer.
      1. Transfer the JSON file to raspberry pi as `/home/pi/.googleauth/client_secrets.json`.
1. Enable API access for your google account
   1.  Click *Library* (on the left hand pane)
      1. Find *Google Drive API* (part of G Suite category) and click on it
      1. Click the *Enable* button
      1. Find the *Google Sheets API* (part of the G Suite category) and click on it
      1. Click the *Enable* button

# Usage
Coming soon :metal:

