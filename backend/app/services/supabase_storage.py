from __future__ import annotations

import io
from typing import Any

try:
    from supabase import Client, create_client
except ImportError:
    Client = None
    create_client = None

from app.core.config import Settings


class SupabaseStorageService:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._client = None
        if Client and settings.supabase_url and settings.supabase_service_role_key:
            self._client = create_client(settings.supabase_url, settings.supabase_service_role_key)

    @property
    def is_enabled(self) -> bool:
        return self._client is not None

    async def upload_file(self, bucket: str, path: str, content: bytes, content_type: str = "application/octet-stream") -> str:
        if not self._client:
            raise RuntimeError("Supabase storage is not configured")
        
        # Supabase Python client uses synchronous calls for storage
        self._client.storage.from_(bucket).upload(
            path=path,
            file=content,
            file_options={"content-type": content_type, "upsert": "true"}
        )
        return self._client.storage.from_(bucket).get_public_url(path)

    async def download_file(self, bucket: str, path: str) -> bytes:
        if not self._client:
            raise RuntimeError("Supabase storage is not configured")
        
        return self._client.storage.from_(bucket).download(path)
