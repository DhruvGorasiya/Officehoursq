"""Supabase client singleton for PostgreSQL and auth."""

from supabase import create_client, Client

from app.config import settings

_client: Client | None = None


def get_supabase() -> Client:
    """Return Supabase client (creates once)."""
    global _client
    if _client is None:
        _client = create_client(settings.supabase_url, settings.supabase_key)
    return _client
