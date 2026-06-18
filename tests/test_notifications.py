import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch, call


class TestReminderScheduler:
    def _make_scheduler(self, mock_db, mock_messenger):
        from app.notifications.scheduler import ReminderScheduler
        return ReminderScheduler(db=mock_db, messenger=mock_messenger)

    def test_schedule_creates_two_reminders(self):
        mock_db = MagicMock()
        mock_db.table.return_value.insert.return_value.execute.return_value = MagicMock()
        mock_messenger = AsyncMock()

        scheduler = self._make_scheduler(mock_db, mock_messenger)
        cita = datetime(2026, 6, 20, 15, 0, tzinfo=timezone.utc)

        scheduler.schedule(
            tenant_id="tenant-123",
            appointment_id="appt-456",
            client_telegram_id=111222,
            datetime_start=cita,
            tenant_name="PetShop Demo",
            service="Baño",
            entity_name="Luna",
        )

        assert mock_db.table.return_value.insert.call_count == 2

    def test_schedule_24h_reminder_is_before_appointment(self):
        mock_db = MagicMock()
        inserted_rows = []
        mock_db.table.return_value.insert.side_effect = lambda row: inserted_rows.append(row) or MagicMock()
        mock_db.table.return_value.insert.return_value.execute.return_value = MagicMock()
        mock_messenger = AsyncMock()

        scheduler = self._make_scheduler(mock_db, mock_messenger)
        cita = datetime(2026, 6, 20, 15, 0, tzinfo=timezone.utc)

        scheduler.schedule(
            tenant_id="tenant-123",
            appointment_id="appt-456",
            client_telegram_id=111222,
            datetime_start=cita,
            tenant_name="PetShop Demo",
            service="Baño",
            entity_name="Luna",
        )

        calls_args = [c.args[0] for c in mock_db.table.return_value.insert.call_args_list]
        send_at_values = [row["send_at"] for row in calls_args]

        expected_24h = (cita - timedelta(hours=24)).isoformat()
        expected_2h = (cita - timedelta(hours=2)).isoformat()

        assert expected_24h in send_at_values
        assert expected_2h in send_at_values

    def test_schedule_reminders_have_sent_false(self):
        mock_db = MagicMock()
        mock_db.table.return_value.insert.return_value.execute.return_value = MagicMock()
        mock_messenger = AsyncMock()

        scheduler = self._make_scheduler(mock_db, mock_messenger)
        cita = datetime(2026, 6, 20, 15, 0, tzinfo=timezone.utc)

        scheduler.schedule(
            tenant_id="t", appointment_id="a", client_telegram_id=1,
            datetime_start=cita, tenant_name="Shop", service="Corte", entity_name=None,
        )

        calls_args = [c.args[0] for c in mock_db.table.return_value.insert.call_args_list]
        for row in calls_args:
            assert row["sent"] is False

    @pytest.mark.asyncio
    async def test_tick_sends_pending_reminders(self):
        mock_db = MagicMock()
        mock_messenger = AsyncMock()

        pending = [
            {
                "id": "rem-1",
                "tenant_id": "t1",
                "client_telegram_id": 111222,
                "message_template": "Hola, tienes una cita mañana",
                "sent": False,
            }
        ]
        mock_db.table.return_value.select.return_value.eq.return_value.lte.return_value.execute.return_value = MagicMock(data=pending)
        mock_db.table.return_value.update.return_value.eq.return_value.execute.return_value = MagicMock()

        scheduler = self._make_scheduler(mock_db, mock_messenger)
        await scheduler.tick()

        mock_messenger.send_message.assert_called_once_with(
            111222, "Hola, tienes una cita mañana"
        )

    @pytest.mark.asyncio
    async def test_tick_marks_reminder_as_sent(self):
        mock_db = MagicMock()
        mock_messenger = AsyncMock()

        pending = [
            {
                "id": "rem-1",
                "tenant_id": "t1",
                "client_telegram_id": 111222,
                "message_template": "Recordatorio",
                "sent": False,
            }
        ]
        mock_db.table.return_value.select.return_value.eq.return_value.lte.return_value.execute.return_value = MagicMock(data=pending)
        update_mock = MagicMock()
        mock_db.table.return_value.update.return_value.eq.return_value.execute.return_value = update_mock

        scheduler = self._make_scheduler(mock_db, mock_messenger)
        await scheduler.tick()

        mock_db.table.return_value.update.assert_called_once_with({"sent": True})

    @pytest.mark.asyncio
    async def test_tick_does_nothing_when_no_pending_reminders(self):
        mock_db = MagicMock()
        mock_messenger = AsyncMock()

        mock_db.table.return_value.select.return_value.eq.return_value.lte.return_value.execute.return_value = MagicMock(data=[])

        scheduler = self._make_scheduler(mock_db, mock_messenger)
        await scheduler.tick()

        mock_messenger.send_message.assert_not_called()

    def test_reminder_message_contains_tenant_name(self):
        mock_db = MagicMock()
        mock_db.table.return_value.insert.return_value.execute.return_value = MagicMock()
        mock_messenger = AsyncMock()

        scheduler = self._make_scheduler(mock_db, mock_messenger)
        cita = datetime(2026, 6, 20, 15, 0, tzinfo=timezone.utc)

        scheduler.schedule(
            tenant_id="t", appointment_id="a", client_telegram_id=1,
            datetime_start=cita, tenant_name="Clínica Mascota Feliz",
            service="Vacunación", entity_name="Firulais",
        )

        calls_args = [c.args[0] for c in mock_db.table.return_value.insert.call_args_list]
        for row in calls_args:
            assert "Clínica Mascota Feliz" in row["message_template"]
            assert "Firulais" in row["message_template"]
