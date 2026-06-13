from telegram import Bot
from app.messaging.base import BaseMessenger, IncomingMessage


class TelegramMessenger(BaseMessenger):
    def __init__(self, bot_token: str):
        self._token = bot_token
        self._bot = Bot(token=bot_token)

    async def send_message(self, user_id: int, text: str) -> None:
        await self._bot.send_message(chat_id=user_id, text=text)

    def extract_message(self, payload: dict, bot_token: str) -> IncomingMessage:
        msg = payload.get("message", {})
        sender = msg.get("from", {})
        return IncomingMessage(
            user_id=sender.get("id"),
            text=msg.get("text", ""),
            tenant_bot_token=bot_token,
            username=sender.get("username"),
        )
