import httpx
from datetime import datetime
from app.calendar.base import BaseCalendar, TimeSlot, CalendarEvent

CAL_API_BASE = "https://api.cal.com/v2"


class CalComProvider(BaseCalendar):
    """Proveedor Cal.com usando API v2 con autenticación por API key."""

    def __init__(self, api_key: str, event_type_id: int):
        self._api_key = api_key
        self._event_type_id = event_type_id
        self._headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "cal-api-version": "2024-08-13",
        }

    async def check_availability(self, start: datetime, end: datetime) -> TimeSlot:
        params = {
            "startTime": start.isoformat(),
            "endTime": end.isoformat(),
            "eventTypeId": self._event_type_id,
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{CAL_API_BASE}/slots/available",
                headers=self._headers,
                params=params,
            )
            response.raise_for_status()
            data = response.json()
            slots = data.get("data", {}).get("slots", {})
            available = len(slots) > 0
            return TimeSlot(start=start, end=end, available=available)

    async def create_event(self, event: CalendarEvent) -> str:
        payload = {
            "eventTypeId": self._event_type_id,
            "start": event.start.isoformat(),
            "attendee": {
                "name": event.attendee_name or "Cliente",
                "email": event.attendee_email or "",
                "timeZone": "America/Santiago",
            },
            "metadata": {"title": event.title, "description": event.description or ""},
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{CAL_API_BASE}/bookings",
                headers=self._headers,
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
            return data["data"]["uid"]

    async def delete_event(self, event_id: str) -> None:
        payload = {"status": "CANCELLED"}
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.patch(
                f"{CAL_API_BASE}/bookings/{event_id}",
                headers=self._headers,
                json=payload,
            )
            response.raise_for_status()
