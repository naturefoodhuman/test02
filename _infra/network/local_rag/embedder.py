# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-06-24 14:48:00
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
        trunc = " ".join(text.split()[:1500])
        key = hashlib.sha256(f"{self.model}:{trunc}".encode()).hexdigest()
        if key in self._cache: return self._cache[key]
        client = self._get_client()
        res = client.embeddings(model=self.model, prompt=trunc, options={"num_ctx": 4096})
        emb = [float(x) for x in res.get("embedding", [])]
        if self.expected_dim and len(emb) != self.expected_dim:
            raise ValueError(f"Expected embedding dimension {self.expected_dim}, got {len(emb)}")
        self._cache[key] = emb
        return emb
