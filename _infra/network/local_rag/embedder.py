# Arena.ai Agent Mode - Execution Lead Engineer
from __future__ import annotations
import hashlib
import json
import os
from typing import Any

class BGE_M3_Embedder:
    def __init__(self, model: str = "bge-m3:latest", client: Any | None = None, expected_dim: int = 1024):
        self.model = model
        self.client = client
        self.expected_dim = expected_dim
        self._cache: dict[str, list[float]] = {}

    def _get_client(self):
        if self.client is not None: return self.client
        try:
            import ollama
            os.environ["NO_PROXY"] = os.environ.get("NO_PROXY", "") + ",127.0.0.1,localhost"
            self.client = ollama
            return self.client
        except Exception as e:
            raise RuntimeError(f"Ollama client error: {e}")

    def embed(self, text: str) -> list[float]:
        # Truncate text to avoid context length issues (approx 2000 words)
        truncated_text = " ".join(text.split()[:2000])
        key = hashlib.sha256(f"{self.model}\0{truncated_text}".encode("utf-8")).hexdigest()
        if key in self._cache: return list(self._cache[key])

        client = self._get_client()
        # Add options to handle context length
        response = client.embeddings(model=self.model, prompt=truncated_text, options={"num_ctx": 8192})
        
        embedding = [float(x) for x in response.get("embedding", [])]
        if self.expected_dim and len(embedding) != self.expected_dim:
            # Handle dimension mismatch or empty response
            if not embedding: raise ValueError("Empty embedding from Ollama")
        
        self._cache[key] = list(embedding)
        return embedding
