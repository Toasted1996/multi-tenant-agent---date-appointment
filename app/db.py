from supabase import create_client, Client
from functools import lru_cache
from config.settings import get_settings


@lru_cache
def get_db_client() -> Client:
    settings = get_settings()
    return create_client(settings.supabase_url, settings.supabase_key)
