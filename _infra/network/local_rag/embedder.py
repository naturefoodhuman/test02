# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-06-23 16:55:00

"""bge-m3 embedder wrapper (E9-C2-S1-T1)."""

from __future__ import annotations

import hashlib
from typing import Any


class BGE_M3_Embedder:
    """Ollama-backed bge-m3 embedder with in-memory cache and test injection."""

    def __init__(self, model: str = "bge-m3", client: Any | None = None, expected_dim: int = 1024):
        self.model = model
        self.client = client
        self.expected_dim = expected_dim
        self._cache: dict[str, list[float]] = {}

    @staticmethod
    def _cache_key(model: str, text: str) -> str:
        return hashlib.sha256(f"{model}\0{text}".encode("utf-8")).hexdigest()

    def _get_client(self):
        if self.client is not None:
            return self.client
        try:
            import ollama

            self.client = ollama
            return self.client
        except Exception as exc:
            raise RuntimeError("ollama client unavailable for embeddings") from exc

    @staticmethod
    def _extract_embedding(response: Any) -> list[float]:
        if isinstance(response, dict):
            if "embedding" in response:
                return [float(x) for x in response["embedding"]]
            if "embeddings" in response and response["embeddings"]:
                return [float(x) for x in response["embeddings"][0]]
        embedding = getattr(response, "embedding", None)
        if embedding is not None:
            return [float(x) for x in embedding]
        raise ValueError("embedding response did not contain embedding")

    def embed(self, text: str) -> list[float]:
        key = self._cache_key(self.model, text)
        if key in self._cache:
            return list(self._cache[key])

        client = self._get_client()
        if hasattr(client, "embeddings"):
            response = client.embeddings(model=self.model, prompt=text)
        elif hasattr(client, "embed"):
            response = client.embed(model=self.model, input=text)
        else:
            raise RuntimeError("embedding client has neither embeddings() nor embed()")

        embedding = self._extract_embedding(response)
        if self.expected_dim and len(embedding) != self.expected_dim:
            raise ValueError(f"expected embedding dim {self.expected_dim}, got {len(embedding)}")
        self._cache[key] = list(embedding)
        return embedding


__all__ = ["BGE_M3_Embedder"]
