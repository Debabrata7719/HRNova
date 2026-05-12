"""
Google Calendar OAuth Setup
Run this script once to authenticate with Google Calendar.
It will open a browser window for you to log in.

Usage: python scripts/setup_google_auth.py
"""

import os
import json
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/calendar"]

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CREDENTIALS_PATH = os.path.join(BASE_DIR, "Credentials.json")
TOKEN_PATH = os.path.join(BASE_DIR, "token.json")


def main():
    print("=" * 50)
    print("  NovaHR — Google Calendar Setup")
    print("=" * 50)
    print()

    if not os.path.exists(CREDENTIALS_PATH):
        print("ERROR: Credentials.json not found in project root.")
        print("Download it from Google Cloud Console:")
        print("  1. Go to https://console.cloud.google.com/")
        print("  2. APIs & Services > Credentials")
        print("  3. Download OAuth 2.0 Client ID as Credentials.json")
        sys.exit(1)

    # Delete old token if exists
    if os.path.exists(TOKEN_PATH):
        os.remove(TOKEN_PATH)
        print("Deleted old token.json")

    print("Opening browser for Google login...")
    print("Please log in and grant Calendar access.")
    print()

    flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
    creds = flow.run_local_server(port=0)

    # Save token
    with open(TOKEN_PATH, "w") as f:
        f.write(json.dumps({
            "token": creds.token,
            "refresh_token": creds.refresh_token,
            "token_uri": creds.token_uri,
            "client_id": creds.client_id,
            "client_secret": creds.client_secret,
            "scopes": list(creds.scopes),
        }))

    print()
    print("token.json created successfully!")
    print("Google Calendar is now connected.")
    print("Restart the API server: python scripts/start_api.py")


if __name__ == "__main__":
    main()
