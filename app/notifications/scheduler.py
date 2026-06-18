import logging
from datetime import datetime, timezone, timedelta
from typing import Optional
from app.messaging.base import BaseMessenger

logger = logging.getLogger(__name__)

TEMPLATE_24H = (
    "🔔 Recordatorio de cita\n\n"
    "Hola, te recordamos que mañana tienes una cita en *{tenant_name}*.\n"
    "📋 Servicio: {service}\n"
    "{entity_line}"
    "📅 Hora: {time}\n\n"
    "Si necesitas cancelar o reagendar, escríbenos."
)

TEMPLATE_2H = (
    "⏰ Tu cita es en 2 horas\n\n"
    "Hola, tu cita en *{tenant_name}* comienza pronto.\n"
    "📋 Servicio: {service}\n"
    "{entity_line}"
    "📅 Hora: {time}\n\n"
    "¡Te esperamos!"
)


class ReminderScheduler:
    def __init__(self, db, messenger: BaseMessenger):
        self._db = db
        self._messenger = messenger

    def schedule(
        self,
        tenant_id: str,
        appointment_id: str,
        client_telegram_id: int,
        datetime_start: datetime,
        tenant_name: str,
        service: str,
        entity_name: Optional[str] = None,
    ) -> None:
        time_str = datetime_start.strftime("%H:%M")
        entity_line = f"🐾 {entity_name}\n" if entity_name else ""

        reminders = [
            {
                "offset": timedelta(hours=24),
                "template": TEMPLATE_24H,
            },
            {
                "offset": timedelta(hours=2),
                "template": TEMPLATE_2H,
            },
        ]

        for reminder in reminders:
            send_at = (datetime_start - reminder["offset"]).isoformat()
            message = reminder["template"].format(
                tenant_name=tenant_name,
                service=service,
                entity_line=entity_line,
                time=time_str,
            )
            self._db.table("reminders").insert({
                "tenant_id": tenant_id,
                "appointment_id": appointment_id,
                "client_telegram_id": client_telegram_id,
                "send_at": send_at,
                "sent": False,
                "message_template": message,
            }).execute()

        logger.info(f"Scheduled 2 reminders for appointment {appointment_id}")

    async def tick(self) -> None:
        """Ejecutar pendientes cuyo send_at ya llegó. Llamar cada 5 minutos."""
        now = datetime.now(timezone.utc).isoformat()
        result = (
            self._db.table("reminders")
            .select("*")
            .eq("sent", False)
            .lte("send_at", now)
            .execute()
        )

        for reminder in result.data:
            try:
                await self._messenger.send_message(
                    reminder["client_telegram_id"],
                    reminder["message_template"],
                )
                self._db.table("reminders").update({"sent": True}).eq(
                    "id", reminder["id"]
                ).execute()
                logger.info(f"Reminder sent: {reminder['id']}")
            except Exception as e:
                logger.error(f"Failed to send reminder {reminder['id']}: {e}")
