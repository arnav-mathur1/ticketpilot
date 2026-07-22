"""Phase 8 demo: show the RAG query cache turning repeated/reworded questions
into near-instant, zero-cost answers. Run:  python scripts/cache_demo.py
"""
import json
import pathlib
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from src.rag_agent.answer import answer_question   # noqa: E402
from src.shared import usage                        # noqa: E402


def timed(label: str, q: str) -> None:
    t0 = time.time()
    r = answer_question(q)
    dt = (time.time() - t0) * 1000
    print(f"  {label:14} {dt:8.1f} ms   cache={str(r.get('cache')):18} | {q}")


if __name__ == "__main__":
    print("RAG query cache demo:")
    timed("cold",         "What is the refund window for a subscription?")
    timed("exact repeat", "What is the refund window for a subscription?")
    timed("paraphrase",   "What's the refund window for a subscription?")
    timed("different Q",  "How do I dispute a fraudulent charge?")
    print("\nusage.summarize():", json.dumps(usage.summarize(), indent=2))
