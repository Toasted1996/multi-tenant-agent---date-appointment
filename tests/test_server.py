import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    with patch("main.get_settings") as mock_settings, \
         patch("main.get_db_client") as mock_db, \
         patch("main._apscheduler") as mock_scheduler:

        from tests.conftest import TEST_FERNET_KEY
        mock_settings.return_value = MagicMock(
            telegram_secret_token="test_secret_456",
            rate_limit_per_minute=10,
            fernet_encryption_key=TEST_FERNET_KEY,
            ollama_base_url="http://localhost:11434",
            ollama_model="llama3.2",
        )
        mock_db.return_value = MagicMock()
        mock_scheduler.running = True

        from main import app
        yield TestClient(app)


def test_health_endpoint_returns_ok(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_webhook_rejects_wrong_secret(client):
    response = client.post(
        "/webhook/fake_bot_token/wrong_secret",
        json={"message": {"text": "hola"}},
    )
    assert response.status_code == 403


def test_webhook_rejects_invalid_hmac(client):
    response = client.post(
        "/webhook/fake_bot_token/test_secret_456",
        content=b'{"message": {"text": "hola"}}',
        headers={
            "Content-Type": "application/json",
            "X-Telegram-Bot-Api-Secret-Token": "firma_invalida",
        },
    )
    assert response.status_code == 403
