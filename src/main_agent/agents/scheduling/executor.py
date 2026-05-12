"""
Schedule Agent for Google Calendar
Creates calendar events from natural language input
Run standalone: python run_main_agent.py (or use employee_agent)
"""

import argparse
import os
import json
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
import dateutil.parser
from langsmith import traceable
from src.config import get_settings
from src.logger import get_logger

logger = get_logger(__name__)
_settings = get_settings()

SCOPES = ["https://www.googleapis.com/auth/calendar"]
IST = ZoneInfo("Asia/Kolkata")

llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0.2,
    api_key=_settings.GROQ_API_KEY,
)

# Get base directory (project root)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))


def load_credentials():
    """Load OAuth credentials from token.json"""
    token_path = os.path.join(BASE_DIR, "token.json")
    creds = None

    if os.path.exists(token_path):
        try:
            with open(token_path, "r") as f:
                token_data = json.load(f)
                creds = Credentials.from_authorized_user_info(token_data, SCOPES)
        except Exception as e:
            logger.warning("Failed to load token.json: %s", e)
            return None

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                # Save refreshed token
                with open(token_path, "w") as f:
                    f.write(json.dumps({
                        "token": creds.token,
                        "refresh_token": creds.refresh_token,
                        "token_uri": creds.token_uri,
                        "client_id": creds.client_id,
                        "client_secret": creds.client_secret,
                        "scopes": creds.scopes,
                    }))
            except Exception as e:
                error_str = str(e).lower()
                if "invalid_grant" in error_str or "token has been expired" in error_str or "revoked" in error_str:
                    # Token is permanently invalid — delete it so user knows to re-auth
                    logger.warning("Google OAuth token expired/revoked. Deleting token.json — re-authentication required.")
                    try:
                        os.remove(token_path)
                    except Exception:
                        pass
                    return None
                else:
                    logger.error("Failed to refresh Google token: %s", e)
                    return None
        else:
            logger.warning("No valid Google Calendar credentials found. Run the OAuth flow to generate token.json.")
            return None

    return creds


def parse_datetime_with_llm(user_input: str) -> dict:
    """Use LLM to parse natural language date/time"""
    today_ist = datetime.now(IST)
    today_str = today_ist.strftime("%B %d, %Y")
    tomorrow_str = (today_ist + timedelta(days=1)).strftime("%Y-%m-%d")

    prompt = f"""Parse this meeting request and extract date and time.

CURRENT DATE: {today_str}
TOMORROW'S DATE: {tomorrow_str}
IMPORTANT: Always use the current year. Never guess a past date.

Input: {user_input}

Respond in this exact JSON format (no other text):
{{
    "title": "Meeting",
    "date": "today", "tomorrow", or "YYYY-MM-DD" format,
    "time": "HH:MM in 24-hour format",
    "description": "extracted description or empty"
}}

Rules for title:
- Use simple title like "Meeting", "Team Meeting", "Call", "Sync", "Standup"
- NEVER use the full user input as title

Rules for date:
- "tomorrow" → use exactly "tomorrow"
- "today" → use exactly "today"
- Specific date like "May 06" → use "YYYY-MM-DD" format

Rules for time:
- "3pm" = 15:00
- "4pm IST" = 16:00
- Always output 24-hour format

Examples:
- "meeting tomorrow at 3pm" → {{"title": "Meeting", "date": "tomorrow", "time": "15:00", "description": ""}}
- "team standup today at 10am" → {{"title": "Team Standup", "date": "today", "time": "10:00", "description": ""}}
"""

    messages = [
        SystemMessage(
            content="Extract meeting details. Title should be simple (Meeting, Call, etc), NOT the full input. Current year: 2026."
        ),
        HumanMessage(content=prompt),
    ]

    try:
        response = llm.invoke(messages)
        content = response.content.strip()

        data = {}
        for line in content.split("\n"):
            if ":" in line:
                key, value = line.split(":", 1)
                key = key.strip().strip('"').lower()
                value = value.strip().strip(",").strip('"').strip("'")
                if value.lower() == "none" or value.lower() == "null":
                    value = ""
                data[key] = value

        return data
    except Exception as e:
        logger.error("LLM datetime parsing error: %s", e)
        return {"title": "", "date": "", "time": "", "description": ""}


def parse_to_datetime(date_str: str, time_str: str) -> datetime:
    """
    Convert date/time strings to a timezone-aware datetime in IST (Asia/Kolkata).
    Returns a datetime with tzinfo=IST so isoformat() includes +05:30.
    """
    today = datetime.now(IST)

    date_str = date_str.lower().strip()
    time_str = time_str.lower().strip() if time_str else "09:00"

    if date_str in ["today"]:
        parsed_date = today.date()
    elif date_str in ["tomorrow", "next day"]:
        parsed_date = (today + timedelta(days=1)).date()
    elif "next" in date_str and "day" in date_str:
        days_ahead = 7 - today.weekday()
        if days_ahead <= 0:
            days_ahead += 7
        parsed_date = (today + timedelta(days=days_ahead)).date()
    else:
        try:
            parsed_date = dateutil.parser.parse(date_str).date()
        except Exception:
            parsed_date = today.date()

    try:
        parsed_time = dateutil.parser.parse(time_str).time()
    except Exception:
        parsed_time = datetime.strptime("09:00", "%H:%M").time()

    # Combine and attach IST timezone — this makes isoformat() emit +05:30
    naive_dt = datetime.combine(parsed_date, parsed_time)
    return naive_dt.replace(tzinfo=IST)


def create_calendar_event(
    title: str, start_datetime: datetime, description: str = ""
) -> dict:
    """Create event on Google Calendar"""
    creds = load_credentials()
    if not creds:
        return {
            "success": False,
            "message": (
                "Google Calendar is not connected. "
                "Please re-authenticate by running the OAuth flow. "
                "Delete token.json (if it exists) and restart the server to trigger re-authentication."
            )
        }

    end_datetime = start_datetime + timedelta(hours=1)

    service = build("calendar", "v3", credentials=creds)

    event = {
        "summary": title,
        "description": description,
        "start": {
            "dateTime": start_datetime.isoformat(),
            "timeZone": "Asia/Kolkata",
        },
        "end": {
            "dateTime": end_datetime.isoformat(),
            "timeZone": "Asia/Kolkata",
        },
    }

    try:
        event_result = (
            service.events()
            .insert(
                calendarId="primary",
                body=event,
                sendNotifications=False,
            )
            .execute()
        )

        # Verify success - check for id and htmlLink
        if event_result and "id" in event_result and "htmlLink" in event_result:
            return {
                "success": True,
                "message": f"Event created: {event_result.get('htmlLink')}",
                "event_id": event_result.get("id"),
            }
        else:
            return {"success": False, "message": "Event not created properly"}

    except Exception as e:
        return {"success": False, "message": f"Error: {str(e)}"}


@traceable(name="Schedule Agent")
def schedule_agent(state: dict) -> dict:
    """
    Handle meeting scheduling requests.
    """
    user_input = state.get("input", "").strip()
    step = state.get("step", "initial")

    # Handle schedule fields - check both formats (standalone and main_agent)
    state["title"] = state.get("title") or state.get("schedule_title") or ""
    state["date"] = state.get("date") or state.get("schedule_date") or ""
    state["time"] = state.get("time") or state.get("schedule_time") or ""
    state["description"] = (
        state.get("description") or state.get("schedule_description") or ""
    )

    if step == "initial":
        if not user_input:
            response = "I can help you schedule a meeting on Google Calendar. What's the meeting title?"
            state["step"] = "ask_title"
            state["output"] = response
            return state

        data = parse_datetime_with_llm(user_input)
        state["title"] = data.get("title", user_input)
        state["date"] = data.get("date", "today")
        state["time"] = data.get("time", "09:00")
        state["description"] = data.get("description", "")

        # Also set schedule_* fields for main_agent
        state["schedule_title"] = state["title"]
        state["schedule_date"] = state["date"]
        state["schedule_time"] = state["time"]
        state["schedule_description"] = state["description"]

        response = f"I understood:\nTitle: {state['title']}\nDate: {state['date']} (Asia/Kolkata IST)\nTime: {state['time']} IST"
        response += f"\nDescription: {state['description'] or 'None'}"
        state["step"] = "confirm"
        state["output"] = response
        return state

    elif step == "ask_title":
        if not user_input:
            response = "Please provide a meeting title."
            state["output"] = response
            return state

        state["title"] = user_input
        response = f"Got it: {user_input}\nWhen should the meeting be? (e.g., tomorrow at 3pm, next Friday at 2pm)"
        state["step"] = "ask_date_time"
        state["output"] = response
        return state

    elif step == "ask_date_time":
        if not user_input:
            response = (
                "Please provide date and time (e.g., tomorrow at 3pm, May 15 at 10am)"
            )
            state["output"] = response
            return state

        data = parse_datetime_with_llm(user_input)
        state["date"] = data.get("date", "today")
        state["time"] = data.get("time", "09:00")

        response = f"Date: {state['date']}, Time: {state['time']}\nAdd a description? (or press Enter to skip)"
        state["step"] = "ask_description"
        state["output"] = response
        return state

    elif step == "ask_description":
        if user_input and user_input.lower() not in ["no", "skip", "-"]:
            state["description"] = user_input
        else:
            state["description"] = ""

        start_dt = parse_to_datetime(state["date"], state["time"])
        date_str = start_dt.strftime("%Y-%m-%d at %I:%M %p")

        response = f"Confirm meeting:\nTitle: {state['title']}\nDate: {date_str}\nDuration: 1 hour\n"
        if state["description"]:
            response += f"Description: {state['description']}\n"
        response += "\nConfirm? (yes/no)"

        state["step"] = "confirm"
        state["output"] = response
        return state

    elif step == "confirm":
        user_lower = user_input.lower()

        if user_lower in ["yes", "y", "confirm", "c"]:
            start_dt = parse_to_datetime(state["date"], state["time"])
            result = create_calendar_event(
                state["title"],
                start_dt,
                state["description"],
            )

            if result["success"]:
                date_str = start_dt.strftime("%A, %B %d, %Y at %I:%M %p")
                response = f"""Meeting Scheduled Successfully!

Title: {state["title"]}
Date: {date_str} (Asia/Kolkata IST)
Duration: 1 hour
Description: {state["description"] or "None"}

View in Calendar: {result["message"]}"""
            else:
                response = f"Error creating event: {result['message']}"

            state["step"] = "completed"
            state["output"] = response
            return state

        elif user_lower in ["no", "n"]:
            state["output"] = "Meeting cancelled. What would you like to do?"
            state["step"] = "initial"
            return state

        else:
            response = "Please confirm with 'yes' or 'no'"
            state["output"] = response
            return state

    else:
        response = "Meeting scheduled. Anything else?"
        state["output"] = response
        return state
