import pytest
from cryptography.fernet import Fernet

TEST_FERNET_KEY = Fernet.generate_key().decode()

TEST_ENV = {
    "TELEGRAM_BOT_TOKEN": "test_token_123",
    "TELEGRAM_SECRET_TOKEN": "test_secret_456",
    "SUPABASE_URL": "https://test.supabase.co",
    "SUPABASE_KEY": "test_key",
    "FERNET_ENCRYPTION_KEY": TEST_FERNET_KEY,
    "NGROK_AUTH_TOKEN": "",
    "OLLAMA_BASE_URL": "http://localhost:11434",
    "OLLAMA_MODEL": "llama3.2",
    "RATE_LIMIT_PER_MINUTE": "10",
}


@pytest.fixture(autouse=True)
def mock_env(monkeypatch):
    for key, value in TEST_ENV.items():
        monkeypatch.setenv(key, value)
