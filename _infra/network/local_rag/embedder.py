# Arena.ai Agent Mode
from __future__ import annotations
import hashlib
import os
from typing import Any

class BGE_M3_Embedder:
    def __init__(self, model: str = "bge-m3:latest", client: Any | None = None, expected_dim: int = 1024):
        self.model = model
        self.client = client
        self.expected_dim = expected_dim
        self._cache = {}

    def _get_client(self):
        if self.client: return self.client
        import ollama
        os.environ["NO_PROXY"] = os.environ.get("NO_PROXY", "") + ",127.0.0.1,localhost"
        self.client = ollama
        return self.client

    def embed(self, text: str) -> list[float]:
        # 强制截断防 500 错误
        trunc = " ".join(text.split()[:1500])
        key = hashlib.sha256(f"{self.model}:{trunc}".encode()).hexdigest()
        if key in self._cache: return self._cache[key]
        client = self._get_client()
        res = client.embeddings(model=self.model, prompt=trunc, options={"num_ctx": 4096})
        emb = [float(x) for x in res.get("embedding", [])]
        self._cache[key] = emb
        return emb
