from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.core.config import Settings
from app.utils.embeddings import hashed_embedding

try:
    import chromadb
except ImportError:  # pragma: no cover
    chromadb = None


class ChromaMemoryService:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._fallback_path = settings.data_dir / "memory.json"
        self._fallback_path.parent.mkdir(parents=True, exist_ok=True)
        if not self._fallback_path.exists():
            self._fallback_path.write_text(
                json.dumps(
                    {
                        "failure_patterns": [],
                        "successful_fixes": [],
                        "reflection_memories": [],
                        "repair_strategy_memories": [],
                    },
                    indent=2,
                ),
                encoding="utf-8",
            )

        self._client = None
        if chromadb is not None:
            try:
                self._client = self._build_client(settings)
            except Exception:
                self._client = None

    def _build_client(self, settings: Settings):
        if settings.chroma_api_key and getattr(chromadb, "CloudClient", None) is not None:
            return chromadb.CloudClient(
                api_key=settings.chroma_api_key,
                tenant=settings.chroma_tenant,
                database=settings.chroma_database,
                cloud_host=settings.chroma_cloud_host,
                cloud_port=settings.chroma_cloud_port,
                enable_ssl=settings.chroma_cloud_ssl,
            )

        # Use Local Persistent Client for development/production stability
        # This stores the database in the backend/storage/chroma directory
        chroma_path = settings.data_dir / "chroma"
        chroma_path.mkdir(parents=True, exist_ok=True)
        
        return chromadb.PersistentClient(
            path=str(chroma_path),
            tenant=settings.chroma_tenant,
            database=settings.chroma_database,
        )

    def _read_fallback(self) -> dict[str, Any]:
        return json.loads(self._fallback_path.read_text(encoding="utf-8"))

    def _write_fallback(self, payload: dict[str, Any]) -> None:
        self._fallback_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    async def store(
        self,
        collection: str,
        identifier: str,
        text: str,
        metadata: dict[str, Any],
    ) -> None:
        if self._client is not None:
            handle = self._client.get_or_create_collection(name=f"{self._settings.chroma_collection_prefix}_{collection}")
            handle.upsert(
                ids=[identifier],
                documents=[text],
                embeddings=[hashed_embedding(text)],
                metadatas=[metadata],
            )
            return

        fallback = self._read_fallback()
        fallback.setdefault(collection, []).append(
            {"id": identifier, "text": text, "metadata": metadata, "embedding": hashed_embedding(text)}
        )
        self._write_fallback(fallback)

    async def query(self, collection: str, text: str, limit: int = 5) -> list[dict[str, Any]]:
        if self._client is not None:
            handle = self._client.get_or_create_collection(name=f"{self._settings.chroma_collection_prefix}_{collection}")
            result = handle.query(query_embeddings=[hashed_embedding(text)], n_results=limit)
            documents = result.get("documents", [[]])[0]
            metadatas = result.get("metadatas", [[]])[0]
            distances = result.get("distances", [[]])[0]
            return [
                {
                    "text": documents[index],
                    "metadata": metadatas[index],
                    "distance": distances[index],
                    "similarity": max(0.0, round(1 - distances[index], 4)),
                }
                for index in range(len(documents))
            ]

        query_embedding = hashed_embedding(text)
        items = self._read_fallback().get(collection, [])
        scored = []
        for item in items:
            similarity = sum(a * b for a, b in zip(query_embedding, item["embedding"]))
            scored.append({"text": item["text"], "metadata": item["metadata"], "similarity": similarity})
        scored.sort(key=lambda entry: entry["similarity"], reverse=True)
        return scored[:limit]
