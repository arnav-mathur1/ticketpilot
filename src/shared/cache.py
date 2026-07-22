"""Caching:

1. EmbeddingCache — embed each chunk/query once, keyed by content hash.
2. QueryCache — exact match first, then semantic (cosine >= threshold), so a
   repeated or reworded question skips retrieval and the LLM entirely. """
   
import hashlib
import json

import numpy as np

from . import config


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()[:24]


class EmbeddingCache:
    def __init__(self, name: str = "embeddings"):
        config.RUNTIME_CACHE_DIR.mkdir(parents=True, exist_ok=True)
        self.path = config.RUNTIME_CACHE_DIR / f"{name}.json"
        self.data = json.loads(self.path.read_text()) if self.path.exists() else {}

    def get_or_embed(self, texts: list[str], embed_fn) -> list[list[float]]:
        """Return an embedding per text, only calling embed_fn for cache misses."""
        missing = [t for t in texts if _sha(t) not in self.data]
        if missing:
            for t, v in zip(missing, embed_fn(missing)):
                self.data[_sha(t)] = v
            self.path.write_text(json.dumps(self.data))
        return [self.data[_sha(t)] for t in texts]


class QueryCache:
    def __init__(self):
        config.RUNTIME_CACHE_DIR.mkdir(parents=True, exist_ok=True)
        self.path = config.RUNTIME_CACHE_DIR / "query_cache.json"
        self.entries = json.loads(self.path.read_text()) if self.path.exists() else []

    def lookup(self, question: str, q_emb):
        """Return (result, kind) on a hit, else (None, None). kind = exact|semantic(sim)."""
        for e in self.entries:                          # exact match
            if e["question"] == question:
                return e["result"], "exact"
        if q_emb is not None and self.entries:          # semantic match
            q = np.array(q_emb)
            for e in self.entries:
                c = np.array(e["embedding"])
                sim = float(q @ c / (np.linalg.norm(q) * np.linalg.norm(c) + 1e-9))
                if sim >= config.SEMANTIC_CACHE_THRESHOLD:
                    return e["result"], f"semantic({sim:.3f})"
        return None, None

    def store(self, question: str, q_emb, result: dict) -> None:
        self.entries.append({"question": question, "embedding": q_emb, "result": result})
        self.path.write_text(json.dumps(self.entries))