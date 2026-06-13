import pytest
from unittest.mock import AsyncMock, patch
from app.messaging.base import IncomingMessage


class TestIncomingMessage:
    def test_creates_with_required_fields(self):
        msg = IncomingMessage(
            user_id=123456,
            text="Hola",
            tenant_bot_token="bot_token_abc",
            username="juan_perez",
        )
        assert msg.user_id == 123456
        assert msg.text == "Hola"
        assert msg.tenant_bot_token == "bot_token_abc"

    def test_username_is_optional(self):
        msg = IncomingMessage(user_id=1, text="test", tenant_bot_token="tok")
        assert msg.username is None


class TestTelegramMessenger:
    @pytest.mark.asyncio
    async def test_send_message_calls_bot(self):
        with patch("app.messaging.telegram.Bot") as MockBot:
            mock_bot = AsyncMock()
            MockBot.return_value = mock_bot

            from app.messaging.telegram import TelegramMessenger
            messenger = TelegramMessenger(bot_token="fake_token")
            await messenger.send_message(user_id=123, text="Test mensaje")

            mock_bot.send_message.assert_called_once_with(
                chat_id=123, text="Test mensaje"
            )

    def test_extract_message_from_update(self):
        with patch("app.messaging.telegram.Bot"):
            from app.messaging.telegram import TelegramMessenger
            messenger = TelegramMessenger(bot_token="fake_token")

            fake_update = {
                "message": {
                    "from": {"id": 789, "username": "maria"},
                    "text": "Quiero agendar",
                    "chat": {"id": 789},
                }
            }
            msg = messenger.extract_message(fake_update, bot_token="tok123")
            assert msg.user_id == 789
            assert msg.text == "Quiero agendar"
            assert msg.tenant_bot_token == "tok123"
            assert msg.username == "maria"

    def test_extract_message_without_username(self):
        with patch("app.messaging.telegram.Bot"):
            from app.messaging.telegram import TelegramMessenger
            messenger = TelegramMessenger(bot_token="fake_token")

            fake_update = {
                "message": {
                    "from": {"id": 111},
                    "text": "Hola",
                    "chat": {"id": 111},
                }
            }
            msg = messenger.extract_message(fake_update, bot_token="tok")
            assert msg.username is None
