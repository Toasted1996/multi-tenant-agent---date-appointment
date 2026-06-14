import json
from datetime import datetime
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from app.calendar.base import BaseCalendar, TimeSlot, CalendarEvent

SCOPES = ["https://www.googleapis.com/auth/calendar"]


class GoogleCalendarProvider(BaseCalendar):
    def __init__(self, credentials_json: str):
        creds_data = json.loads(credentials_json)
        self._creds = Credentials(
            token=creds_data["token"],
            refresh_token=creds_data["refresh_token"],
            token_uri=creds_data["token_uri"],
            client_id=creds_data["client_id"],
            client_secret=creds_data["client_secret"],
            scopes=SCOPES,
        )
        self._service = build("calendar", "v3", credentials=self._creds)

    def check_availability(self, start: datetime, end: datetime) -> TimeSlot:
        body = {
            "timeMin": start.isoformat(),
            "timeMax": end.isoformat(),
            "items": [{"id": "primary"}],
        }
        result = self._service.freebusy().query(body=body).execute()
        busy = result["calendars"]["primary"]["busy"]
        return TimeSlot(start=start, end=end, available=len(busy) == 0)

    def create_event(self, event: CalendarEvent) -> str:
        body = {
            "summary": event.title,
            "description": event.description or "",
            "start": {"dateTime": event.start.isoformat(), "timeZone": "America/Santiago"},
            "end": {"dateTime": event.end.isoformat(), "timeZone": "America/Santiago"},
        }
        if event.attendee_email:
            body["attendees"] = [{"email": event.attendee_email, "displayName": event.attendee_name or ""}]

        created = self._service.events().insert(calendarId="primary", body=body).execute()
        return created["id"]

    def delete_event(self, event_id: str) -> None:
        self._service.events().delete(calendarId="primary", eventId=event_id).execute()
