"""Token + latency instrumentation for every LLM/embedding call.

Each call appends a line to config.USAGE_LOG; summarize() rolls it up so we can
show cache hit-rate, estimated spend, and p50 latency.
"""

import json
import time

from . import config

# gpt-4o-mini + text-embedding-3-small pricing per 1M tokens (USD), for rough estimates.
PRICES = {"input": 0.15, "output": 0.60, "embed": 0.02}


def log_usage(tag: str, usage, latency_s: float, cached: bool) -> None:
    config.RUNTIME_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    rec = {"ts": time.time(), "tag": tag,
           "latency_ms": round(latency_s * 1000, 1), "cached": cached}
    if usage is not None:
        pt = getattr(usage, "prompt_tokens", 0) or 0
        ct = getattr(usage, "completion_tokens", 0) or 0
        rec.update(prompt_tokens=pt, completion_tokens=ct,
                   est_cost_usd=round(pt / 1e6 * PRICES["input"] + ct / 1e6 * PRICES["output"], 6))
    with open(config.USAGE_LOG, "a") as f:
        f.write(json.dumps(rec) + "\n")


def summarize() -> dict:
    if not config.USAGE_LOG.exists():
        return {"calls": 0}
    recs = [json.loads(l) for l in config.USAGE_LOG.read_text().splitlines() if l.strip()]
    lat = sorted(r["latency_ms"] for r in recs)
    return {
        "calls": len(recs),
        "cached_hits": sum(1 for r in recs if r.get("cached")),
        "total_est_cost_usd": round(sum(r.get("est_cost_usd", 0) for r in recs), 4),
        "p50_latency_ms": lat[len(lat) // 2] if lat else None,
    }