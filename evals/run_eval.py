"""Eval harness. Scores both agents against the golden sets and
appends a labeled row to evals/history.csv, so quality is tracked over time.

Metrics:
  classification -> exact-match accuracy for category / urgency / sentiment
  RAG            -> LLM-as-judge (1-5) vs reference answer, citation-source
                    match, and refusal accuracy on the unanswerable questions
"""
import argparse
import csv
import json
from datetime import datetime, timezone
from statistics import mean

from src.shared import config, llm
from src.triage_agent.graph import classify_ticket
from src.rag_agent.answer import answer_question

GOLDEN_RAG = config.ROOT / "evals" / "golden_rag.json"
HISTORY = config.ROOT / "evals" / "history.csv"


def eval_classification(limit: int | None = None) -> dict:
    tickets = json.loads(config.SAMPLE_TICKETS.read_text())["tickets"]
    if limit:
        tickets = tickets[:limit]
    cat = urg = sent = 0
    for i, t in enumerate(tickets, 1):
        r = classify_ticket({"text": t["text"]})
        cat += r["category"] == t["expected_category"]
        urg += r["urgency"] == t["expected_urgency"]
        sent += r["sentiment"] == t["expected_sentiment"]
        print(f"  [classify {i}/{len(tickets)}] {t['id']}   ", end="\r")
    n = len(tickets)
    print()
    return {"n_class": n, "cat_acc": cat / n, "urg_acc": urg / n, "sent_acc": sent / n}


def judge(question: str, reference: str, candidate: str) -> int:
    """LLM-as-judge: score candidate vs reference on a 1-5 correctness rubric."""
    system = (
        "You are a strict evaluator. Given a QUESTION, a REFERENCE answer, and a "
        "CANDIDATE answer, score how well the candidate matches the reference on "
        "correctness and completeness, from 1 (wrong or missing key facts) to 5 "
        "(fully correct and complete). Respond as JSON: {\"score\": <int 1-5>}."
    )
    user = f"QUESTION: {question}\n\nREFERENCE: {reference}\n\nCANDIDATE: {candidate}"
    raw = llm.chat([{"role": "system", "content": system},
                    {"role": "user", "content": user}],
                   response_format={"type": "json_object"})
    return int(json.loads(raw)["score"])


def eval_rag(limit: int | None = None) -> dict:
    questions = json.loads(GOLDEN_RAG.read_text())["questions"]
    if limit:
        questions = questions[:limit]
    scores: list[int] = []
    cite_hits = n_ans = refuse_ok = n_unans = 0
    for i, q in enumerate(questions, 1):
        r = answer_question(q["question"], use_cache=False)   # measure the model, not the cache
        if q["unanswerable"]:
            n_unans += 1
            refuse_ok += int(r["refused"])
        else:
            n_ans += 1
            if r["refused"]:
                scores.append(1)  # wrongly refused an answerable question
            else:
                scores.append(judge(q["question"], q["reference_answer"], r["answer"]))
                if q["expected_source"] and q["expected_source"] in r["answer"]:
                    cite_hits += 1
        print(f"  [rag {i}/{len(questions)}] {q['id']}   ", end="\r")
    print()
    return {
        "n_ans": n_ans, "n_unans": n_unans,
        "rag_judge_avg": round(mean(scores), 2) if scores else 0.0,
        "citation_acc": round(cite_hits / n_ans, 3) if n_ans else 0.0,
        "refusal_acc": round(refuse_ok / n_unans, 3) if n_unans else None,
    }


def append_history(label: str, m: dict) -> dict:
    row = {
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "label": label,
        "cat_acc": round(m["cat_acc"], 3),
        "urg_acc": round(m["urg_acc"], 3),
        "sent_acc": round(m["sent_acc"], 3),
        "rag_judge_avg": m["rag_judge_avg"],
        "citation_acc": m["citation_acc"],
        "refusal_acc": m["refusal_acc"],
    }
    is_new = not HISTORY.exists()
    with open(HISTORY, "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(row))
        if is_new:
            w.writeheader()
        w.writerow(row)
    return row


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", required=True, help="name for this run, e.g. baseline")
    ap.add_argument("--limit", type=int, default=None, help="cap items per agent (smoke test)")
    args = ap.parse_args()

    print(f"== Eval run: {args.label} ==")
    m = eval_classification(args.limit)
    m.update(eval_rag(args.limit))
    append_history(args.label, m)

    print("\n--- RESULTS ---")
    print(f"classification  category {m['cat_acc']:.0%} | urgency {m['urg_acc']:.0%} | "
          f"sentiment {m['sent_acc']:.0%}   (n={m['n_class']})")
    print(f"RAG             judge {m['rag_judge_avg']}/5 | citation {m['citation_acc']:.0%} | "
          f"refusal {m['refusal_acc'] if m['refusal_acc'] is None else format(m['refusal_acc'], '.0%')}"
          f"   (ans={m['n_ans']}, unans={m['n_unans']})")
    print(f"\nappended row to {HISTORY.name}  (label={args.label})")


if __name__ == "__main__":
    main()
