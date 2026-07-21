# Run the triage graph over the sample tickets and print results.

import json
import sys

from ..shared import config
from .graph import run_triage


def _mark(got: str, expected: str) -> str:
    return "OK " if got == expected else "XX "


def main(limit: int | None = None) -> None:
    data = json.loads(config.SAMPLE_TICKETS.read_text())
    tickets = data["tickets"]
    if limit:
        tickets = tickets[:limit]

    cat_hits = urg_hits = sent_hits = 0
    for t in tickets:
        r = run_triage(t["text"])
        cat_hits += r["category"] == t["expected_category"]
        urg_hits += r["urgency"] == t["expected_urgency"]
        sent_hits += r["sentiment"] == t["expected_sentiment"]

        print("=" * 78)
        print(f"[{t['id']}] {t['text'][:70]}")
        print(f"  {_mark(r['category'], t['expected_category'])}category  {r['category']:<16} (expected {t['expected_category']})")
        print(f"  {_mark(r['urgency'], t['expected_urgency'])}urgency   {r['urgency']:<16} (expected {t['expected_urgency']})")
        print(f"  {_mark(r['sentiment'], t['expected_sentiment'])}sentiment {r['sentiment']:<16} (expected {t['expected_sentiment']})")
        print(f"     confidence {r['confidence']}")
        print(f"     draft: {r['draft_reply'][:160]}...")

    n = len(tickets)
    print("=" * 78)
    print(f"SUMMARY over {n} tickets:")
    print(f"  category  accuracy: {cat_hits}/{n} = {cat_hits/n:.0%}")
    print(f"  urgency   accuracy: {urg_hits}/{n} = {urg_hits/n:.0%}")
    print(f"  sentiment accuracy: {sent_hits}/{n} = {sent_hits/n:.0%}")


if __name__ == "__main__":
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else None
    main(limit)
