from config.settings import Settings


def test_settings_loads_from_env():
    s = Settings()
    assert s.telegram_bot_token == "test_token_123"
    assert s.supabase_url == "https://test.supabase.co"
    assert s.ollama_model == "llama3.2"
    assert s.rate_limit_per_minute == 10


def test_settings_defaults():
    s = Settings()
    assert s.ollama_base_url == "http://localhost:11434"
    assert s.ngrok_auth_token == ""
