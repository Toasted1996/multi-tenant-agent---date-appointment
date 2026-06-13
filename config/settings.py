from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    telegram_bot_token: str
    telegram_secret_token: str
    supabase_url: str
    supabase_key: str
    fernet_encryption_key: str
    ngrok_auth_token: str = ""
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2"
    rate_limit_per_minute: int = 10


@lru_cache
def get_settings() -> Settings:
    return Settings()
