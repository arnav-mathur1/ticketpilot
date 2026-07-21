"""
RAG ingest: turn the policies into a searchable vector index.

Pipeline (run once):
    chunk each doc on '## ' sections
    embed each chunk
    store in FAISS index
"""
import json
import re

import faiss
import numpy as np

from ..shared import config
from ..shared.llm import embed

INDEX_PATH = config.CACHE_DIR / "policy.faiss"
META_PATH = config.CACHE_DIR / "policy_chunks.json"


def chunk_doc(text: str, source: str) -> list[dict]:
    """Split one policy doc into section chunks on '## ' headings.

    Each chunk keeps its source filename + section heading, so the RAG agent
    can later cite *exactly* where an answer came from. A section longer than
    CHUNK_MAX_CHARS is hard-split so no single chunk is too large to embed well.
    """
    parts = re.split(r"\n(?=## )", text)   # split *before* each line starting "## "
    chunks: list[dict] = []
    for part in parts:
        part = part.strip()
        if not part:
            continue
        lines = part.splitlines()
        heading = lines[0].lstrip("# ").strip()      # "## 1. Refund window" -> "1. Refund window"
        body = "\n".join(lines[1:]).strip()
        if not body:
            continue                                 # skip title-only parts (the doc's top line)
        # hard-split any oversized section into <= CHUNK_MAX_CHARS pieces
        while len(part) > config.CHUNK_MAX_CHARS:
            chunks.append({"source": source, "section": heading,
                           "text": part[:config.CHUNK_MAX_CHARS]})
            part = part[config.CHUNK_MAX_CHARS:]
        chunks.append({"source": source, "section": heading, "text": part})
    return chunks


def build_index() -> tuple[int, int]:
    files = sorted(config.POLICY_DIR.glob("*.txt")) + sorted(config.POLICY_DIR.glob("*.md"))
    if not files:
        raise SystemExit(f"No policy docs (.txt/.md) found in {config.POLICY_DIR}")

    chunks: list[dict] = []
    for f in files:
        chunks += chunk_doc(f.read_text(), f.name)
    for i, c in enumerate(chunks):
        c["chunk_id"] = f"C{i:03d}"

    # Embed every chunk, then L2-normalize so inner product == cosine similarity.
    vecs = np.array(embed([c["text"] for c in chunks]), dtype="float32")
    faiss.normalize_L2(vecs)
    index = faiss.IndexFlatIP(vecs.shape[1])   # flat exact search; fine for a small corpus
    index.add(vecs)

    config.CACHE_DIR.mkdir(parents=True, exist_ok=True)
    faiss.write_index(index, str(INDEX_PATH))
    META_PATH.write_text(json.dumps(chunks, indent=2))
    return len(files), len(chunks)


if __name__ == "__main__":
    nf, nc = build_index()
    print(f"Indexed {nc} chunks from {nf} documents -> {INDEX_PATH}")
