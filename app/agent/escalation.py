from app.messaging.base import BaseMessenger


class EscalationHandler:
    def __init__(self, messenger: BaseMessenger):
        self._messenger = messenger

    async def escalate(
        self,
        db,
        tenant_id: str,
        conversation_id: str,
        client_user_id: int,
        escalation_contact: str,
        reason: str,
        conversation_summary: str,
    ) -> None:
        db.table("escalations").insert({
            "tenant_id": tenant_id,
            "conversation_id": conversation_id,
            "reason": reason,
            "resolved": False,
        }).execute()

        await self._messenger.send_message(
            client_user_id,
            "Te voy a conectar con nuestro equipo 🙏 En breve alguien te contactará.",
        )

        if escalation_contact and escalation_contact.isdigit():
            await self._messenger.send_message(
                int(escalation_contact),
                f"⚠️ *Escalación requerida*\nMotivo: {reason}\n\n{conversation_summary}",
            )
