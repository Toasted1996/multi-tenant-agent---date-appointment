import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.agent.core import AgentCore
from app.messaging.base import IncomingMessage
from app.llm.base import LLMResponse

FAKE_TENANT = {
    "id": "tenant-uuid-123",
    "name": "PetShop Demo",
    "niche": "grooming",
    "escalation_contact": "987654321",
    "telegram_bot_token": "fake_token",
}

FAKE_CLIENT = {
    "id": "client-uuid-456",
    "tenant_id": "tenant-uuid-123",
    "telegram_user_id": 111222,
    "name": "María",
    "consent_accepted_at": "2026-06-14T10:00:00",
}

FAKE_CONVERSATION = {
    "id": "conv-uuid-789",
    "tenant_id": "tenant-uuid-123",
    "client_id": "client-uuid-456",
    "state": "idle",
    "context_json": {},
}


def make_core(mock_db, mock_settings, llm, messenger):
    from tests.conftest import TEST_FERNET_KEY
    mock_settings.return_value = MagicMock(fernet_encryption_key=TEST_FERNET_KEY)

    db = MagicMock()
    mock_db.return_value = db

    # Cliente registrado existe
    db.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = MagicMock(data=[FAKE_CLIENT])
    # Conversación existe
    db.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = MagicMock(data=[FAKE_CONVERSATION])

    return AgentCore(llm=llm, messenger=messenger, tenant=FAKE_TENANT), db


@pytest.mark.asyncio
async def test_agent_sends_message_to_registered_client():
    mock_llm = AsyncMock()
    mock_llm.chat = AsyncMock(return_value=LLMResponse(
        content='{"intent": "GREETING"}', raw={}
    ))
    mock_messenger = AsyncMock()

    with patch("app.agent.core.get_db_client") as mock_db, \
         patch("app.agent.core.get_settings") as mock_settings:

        from tests.conftest import TEST_FERNET_KEY
        mock_settings.return_value = MagicMock(fernet_encryption_key=TEST_FERNET_KEY)
        db = MagicMock()
        mock_db.return_value = db

        db.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = MagicMock(data=[FAKE_CLIENT])
        db.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = MagicMock(data=[FAKE_CONVERSATION])
        db.table.return_value.update.return_value.eq.return_value.execute.return_value = MagicMock()

        core = AgentCore(llm=mock_llm, messenger=mock_messenger, tenant=FAKE_TENANT)
        incoming = IncomingMessage(user_id=111222, text="Hola", tenant_bot_token="fake_token")
        await core.handle(incoming)

        mock_messenger.send_message.assert_called_once()


@pytest.mark.asyncio
async def test_agent_escalates_on_human_escalation_intent():
    mock_llm = AsyncMock()
    mock_llm.chat = AsyncMock(return_value=LLMResponse(
        content='{"intent": "HUMAN_ESCALATION"}', raw={}
    ))
    mock_messenger = AsyncMock()

    with patch("app.agent.core.get_db_client") as mock_db, \
         patch("app.agent.core.get_settings") as mock_settings:

        from tests.conftest import TEST_FERNET_KEY
        mock_settings.return_value = MagicMock(fernet_encryption_key=TEST_FERNET_KEY)
        db = MagicMock()
        mock_db.return_value = db
        db.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = MagicMock(data=[FAKE_CLIENT])
        db.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = MagicMock(data=[FAKE_CONVERSATION])
        db.table.return_value.insert.return_value.execute.return_value = MagicMock()
        db.table.return_value.update.return_value.eq.return_value.execute.return_value = MagicMock()

        core = AgentCore(llm=mock_llm, messenger=mock_messenger, tenant=FAKE_TENANT)
        incoming = IncomingMessage(user_id=111222, text="Quiero hablar con alguien", tenant_bot_token="fake_token")
        await core.handle(incoming)

        # Debe enviar mensaje al cliente Y al operador
        assert mock_messenger.send_message.call_count >= 2


@pytest.mark.asyncio
async def test_agent_anonymizes_on_delete_data_intent():
    mock_llm = AsyncMock()
    mock_llm.chat = AsyncMock(return_value=LLMResponse(
        content='{"intent": "DELETE_MY_DATA"}', raw={}
    ))
    mock_messenger = AsyncMock()

    with patch("app.agent.core.get_db_client") as mock_db, \
         patch("app.agent.core.get_settings") as mock_settings:

        from tests.conftest import TEST_FERNET_KEY
        mock_settings.return_value = MagicMock(fernet_encryption_key=TEST_FERNET_KEY)
        db = MagicMock()
        mock_db.return_value = db
        db.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = MagicMock(data=[FAKE_CLIENT])
        db.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = MagicMock(data=[FAKE_CONVERSATION])
        db.table.return_value.update.return_value.eq.return_value.eq.return_value.execute.return_value = MagicMock()

        core = AgentCore(llm=mock_llm, messenger=mock_messenger, tenant=FAKE_TENANT)
        incoming = IncomingMessage(user_id=111222, text="Eliminen mis datos", tenant_bot_token="fake_token")
        await core.handle(incoming)

        mock_messenger.send_message.assert_called_once()
        msg = mock_messenger.send_message.call_args.args[1]
        assert "eliminad" in msg.lower() or "borrad" in msg.lower() or "eliminados" in msg.lower()


@pytest.mark.asyncio
async def test_agent_creates_new_client_if_not_exists():
    mock_llm = AsyncMock()
    mock_llm.chat = AsyncMock(return_value=LLMResponse(
        content='{"intent": "GREETING"}', raw={}
    ))
    mock_messenger = AsyncMock()

    with patch("app.agent.core.get_db_client") as mock_db, \
         patch("app.agent.core.get_settings") as mock_settings:

        from tests.conftest import TEST_FERNET_KEY
        mock_settings.return_value = MagicMock(fernet_encryption_key=TEST_FERNET_KEY)
        db = MagicMock()
        mock_db.return_value = db

        # Simular cliente nuevo (no existe)
        no_data = MagicMock(data=[])
        with_data = MagicMock(data=[FAKE_CLIENT])
        created_client = MagicMock(data=[FAKE_CLIENT])
        created_conv = MagicMock(data=[FAKE_CONVERSATION])

        select_mock = MagicMock()
        select_mock.eq.return_value.eq.return_value.execute.side_effect = [
            no_data,       # buscar cliente → no existe
            no_data,       # buscar conversación → no existe
        ]
        db.table.return_value.select.return_value = select_mock
        db.table.return_value.insert.return_value.execute.side_effect = [
            created_client,
            created_conv,
        ]
        db.table.return_value.update.return_value.eq.return_value.execute.return_value = MagicMock()

        core = AgentCore(llm=mock_llm, messenger=mock_messenger, tenant=FAKE_TENANT)
        incoming = IncomingMessage(user_id=999888, text="Hola", tenant_bot_token="fake_token", username="nuevo_usuario")
        await core.handle(incoming)

        # Debe haber intentado insertar cliente
        assert db.table.return_value.insert.called
