"""
RAG retrieval: given a question, return the most similar chunks.

Loads the FAISS index + metadata built by ingest.py (once, cached in module
globals) and does a cosine-similarity search.
"""
import json

import faiss
import numpy as np

from ..shared.llm import embed
from .ingest import INDEX_PATH, META_PATH

_index = None
_chunks = None


def _load():
    """Lazy-load the index + chunk metadata on first use."""
    global _index, _chunks
    if _index is None:
        if not INDEX_PATH.exists():
            raise SystemExit("No index found. Build it first: python -m src.rag_agent.ingest")
        _index = faiss.read_index(str(INDEX_PATH))
        _chunks = json.loads(META_PATH.read_text())
    return _index, _chunks


def retrieve(question: str, k: int = 4) -> list[dict]:
    """Return the k chunks most similar to `question`.

    Each result is the chunk dict (source, section, text, chunk_id) plus a
    'score' in [-1, 1] (cosine similarity; higher = more relevant).
    """
    index, chunks = _load()
    q = np.array([embed(question)], dtype="float32")
    faiss.normalize_L2(q)
    scores, idxs = index.search(q, k)
    results = []
    for score, i in zip(scores[0], idxs[0]):
        if i == -1:                       # FAISS pads with -1 if fewer than k exist
            continue
        c = dict(chunks[i])
        c["score"] = float(score)
        results.append(c)
    return results
