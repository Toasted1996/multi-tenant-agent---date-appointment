import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock, AsyncMock, patch
from app.calendar.base import TimeSlot, CalendarEvent


class TestTimeSlot:
    def test_creates_slot(self):
        start = datetime(2026, 6, 20, 15, 0, tzinfo=timezone.utc)
        end = datetime(2026, 6, 20, 17, 0, tzinfo=timezone.utc)
        slot = TimeSlot(start=start, end=end, available=True)
        assert slot.available is True
        assert slot.duration_minutes == 120

    def test_unavailable_slot(self):
        start = datetime(2026, 6, 20, 10, 0, tzinfo=timezone.utc)
        end = datetime(2026, 6, 20, 10, 30, tzinfo=timezone.utc)
        slot = TimeSlot(start=start, end=end, available=False)
        assert slot.available is False
        assert slot.duration_minutes == 30


class TestGoogleCalendarProvider:
    def _make_provider(self, mock_build):
        mock_service = MagicMock()
        mock_build.return_value = mock_service
        creds_json = (
            '{"token":"t","refresh_token":"r","token_uri":"https://oauth2.googleapis.com/token",'
            '"client_id":"c","client_secret":"s"}'
        )
        from app.calendar.google import GoogleCalendarProvider
        return GoogleCalendarProvider(credentials_json=creds_json), mock_service

    @patch("app.calendar.google.build")
    def test_check_availability_returns_true_when_free(self, mock_build):
        provider, mock_service = self._make_provider(mock_build)
        mock_service.freebusy().query().execute.return_value = {
            "calendars": {"primary": {"busy": []}}
        }
        start = datetime(2026, 6, 20, 15, 0, tzinfo=timezone.utc)
        end = datetime(2026, 6, 20, 17, 0, tzinfo=timezone.utc)
        slot = provider.check_availability(start=start, end=end)
        assert slot.available is True

    @patch("app.calendar.google.build")
    def test_check_availability_returns_false_when_busy(self, mock_build):
        provider, mock_service = self._make_provider(mock_build)
        mock_service.freebusy().query().execute.return_value = {
            "calendars": {"primary": {"busy": [{"start": "2026-06-20T15:00:00Z", "end": "2026-06-20T17:00:00Z"}]}}
        }
        start = datetime(2026, 6, 20, 15, 0, tzinfo=timezone.utc)
        end = datetime(2026, 6, 20, 17, 0, tzinfo=timezone.utc)
        slot = provider.check_availability(start=start, end=end)
        assert slot.available is False

    @patch("app.calendar.google.build")
    def test_create_event_returns_event_id(self, mock_build):
        provider, mock_service = self._make_provider(mock_build)
        mock_service.events().insert().execute.return_value = {"id": "google-event-abc123"}
        event = CalendarEvent(
            title="Baño Luna",
            start=datetime(2026, 6, 20, 15, 0, tzinfo=timezone.utc),
            end=datetime(2026, 6, 20, 17, 0, tzinfo=timezone.utc),
            description="Servicio de baño + corte",
        )
        event_id = provider.create_event(event)
        assert event_id == "google-event-abc123"

    @patch("app.calendar.google.build")
    def test_delete_event_calls_service(self, mock_build):
        provider, mock_service = self._make_provider(mock_build)
        provider.delete_event("google-event-abc123")
        mock_service.events().delete.assert_called_once_with(
            calendarId="primary", eventId="google-event-abc123"
        )


class TestCalComProvider:
    @pytest.mark.asyncio
    async def test_check_availability_returns_true_when_slots_exist(self):
        with patch("app.calendar.cal_com.httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_response = MagicMock()
            mock_response.raise_for_status = MagicMock()
            mock_response.json.return_value = {
                "data": {"slots": {"2026-06-20": [{"time": "2026-06-20T15:00:00.000Z"}]}}
            }
            mock_client.get = AsyncMock(return_value=mock_response)
            MockClient.return_value = mock_client

            from app.calendar.cal_com import CalComProvider
            provider = CalComProvider(api_key="cal_test_key", event_type_id=123)
            start = datetime(2026, 6, 20, 15, 0, tzinfo=timezone.utc)
            end = datetime(2026, 6, 20, 17, 0, tzinfo=timezone.utc)
            slot = await provider.check_availability(start=start, end=end)
            assert slot.available is True

    @pytest.mark.asyncio
    async def test_check_availability_returns_false_when_no_slots(self):
        with patch("app.calendar.cal_com.httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_response = MagicMock()
            mock_response.raise_for_status = MagicMock()
            mock_response.json.return_value = {"data": {"slots": {}}}
            mock_client.get = AsyncMock(return_value=mock_response)
            MockClient.return_value = mock_client

            from app.calendar.cal_com import CalComProvider
            provider = CalComProvider(api_key="cal_test_key", event_type_id=123)
            start = datetime(2026, 6, 20, 15, 0, tzinfo=timezone.utc)
            end = datetime(2026, 6, 20, 17, 0, tzinfo=timezone.utc)
            slot = await provider.check_availability(start=start, end=end)
            assert slot.available is False

    @pytest.mark.asyncio
    async def test_create_event_returns_booking_uid(self):
        with patch("app.calendar.cal_com.httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_response = MagicMock()
            mock_response.raise_for_status = MagicMock()
            mock_response.json.return_value = {"data": {"uid": "calcom-uid-xyz789"}}
            mock_client.post = AsyncMock(return_value=mock_response)
            MockClient.return_value = mock_client

            from app.calendar.cal_com import CalComProvider
            provider = CalComProvider(api_key="cal_test_key", event_type_id=123)
            event = CalendarEvent(
                title="Consulta veterinaria",
                start=datetime(2026, 6, 20, 15, 0, tzinfo=timezone.utc),
                end=datetime(2026, 6, 20, 15, 30, tzinfo=timezone.utc),
                attendee_name="Juan Pérez",
                attendee_email="juan@example.com",
            )
            uid = await provider.create_event(event)
            assert uid == "calcom-uid-xyz789"

    @pytest.mark.asyncio
    async def test_delete_event_cancels_booking(self):
        with patch("app.calendar.cal_com.httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_response = MagicMock()
            mock_response.raise_for_status = MagicMock()
            mock_client.patch = AsyncMock(return_value=mock_response)
            MockClient.return_value = mock_client

            from app.calendar.cal_com import CalComProvider
            provider = CalComProvider(api_key="cal_test_key", event_type_id=123)
            await provider.delete_event("calcom-uid-xyz789")
            mock_client.patch.assert_called_once()
