"""chunk_doc splits policy docs on '## ' headings and keeps source + section
so answers can cite exactly where they came from."""
from src.rag_agent.ingest import chunk_doc

DOC = "# Refund Policy\n\n## 1. Refund window\nFull refund within 14 days.\n\n## 2. Cancellation\nCancel anytime."


def test_splits_on_headings_and_skips_title():
    chunks = chunk_doc(DOC, "refund.txt")
    assert [c["section"] for c in chunks] == ["1. Refund window", "2. Cancellation"]


def test_keeps_source_and_body():
    chunks = chunk_doc(DOC, "refund.txt")
    assert all(c["source"] == "refund.txt" for c in chunks)
    assert "14 days" in chunks[0]["text"]
