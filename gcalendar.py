"""
Google Calendar integration for Worklog CLI.
"""

import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# If modifying these scopes, delete the token file.
SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]

CONFIG_DIR = Path.home() / ".worklog"
CREDENTIALS_FILE = CONFIG_DIR / "google_credentials.json"
TOKEN_FILE = CONFIG_DIR / "google_token.json"


def get_credentials() -> Optional[Credentials]:
    """Get or refresh Google OAuth credentials."""
    creds = None
    
    # Load existing token
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
    
    # If no valid credentials, authenticate
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not CREDENTIALS_FILE.exists():
                raise FileNotFoundError(
                    "Google credentials not found. Run 'worklog setup' to configure."
                )
            flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_FILE), SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save credentials for next run
        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())
        os.chmod(TOKEN_FILE, 0o600)
    
    return creds


def get_calendar_events(config: dict, start: datetime, end: datetime) -> list[dict]:
    """Fetch calendar events for a given date range."""
    creds = get_credentials()
    if not creds:
        return []
    
    service = build("calendar", "v3", credentials=creds)
    
    # Convert to RFC3339 format
    time_min = start.isoformat() + "Z"
    time_max = end.isoformat() + "Z"
    
    events_result = service.events().list(
        calendarId="primary",
        timeMin=time_min,
        timeMax=time_max,
        maxResults=50,
        singleEvents=True,
        orderBy="startTime"
    ).execute()
    
    events = events_result.get("items", [])
    
    formatted_events = []
    for event in events:
        start_time = event["start"].get("dateTime", event["start"].get("date"))
        end_time = event["end"].get("dateTime", event["end"].get("date"))
        
        # Parse times
        if "T" in start_time:
            start_dt = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
            end_dt = datetime.fromisoformat(end_time.replace("Z", "+00:00"))
            time_str = start_dt.strftime("%H:%M") + " - " + end_dt.strftime("%H:%M")
            duration = end_dt - start_dt
            duration_str = format_duration(duration.total_seconds())
        else:
            time_str = "All day"
            duration_str = "All day"
        
        formatted_events.append({
            "time": time_str,
            "summary": event.get("summary", "(No title)"),
            "duration": duration_str,
            "description": event.get("description", ""),
            "location": event.get("location", ""),
        })
    
    return formatted_events


def format_duration(seconds: float) -> str:
    """Format duration in seconds to human-readable string."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    
    if hours > 0:
        return f"{hours}h {minutes}m"
    return f"{minutes}m"


def test_calendar_connection(config: dict) -> bool:
    """Test if calendar connection is working."""
    try:
        if TOKEN_FILE.exists():
            creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
            return creds.valid or (creds.expired and creds.refresh_token)
        return False
    except Exception:
        return False
