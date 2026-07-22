"""Shared configuration: loads .env once and exposes model names + paths.

Import this anywhere with `from ..shared import config` and read e.g.
`config.OPENAI_MODEL`. Loading .env here means no other module has to.
"""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()  # reads .env at repo root into os.environ

# Repo root = three levels up from this file: src/shared/config.py -> repo/
ROOT = Path(__file__).resolve().parents[2]

# --- LLM models (overridable via .env) ---
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_EMBED_MODEL = os.getenv("OPENAI_EMBED_MODEL", "text-embedding-3-small")

# --- Data paths ---
DATA_DIR = ROOT / "data"
SAMPLE_TICKETS = DATA_DIR / "sample_tickets.json"
# POLICY_DIR is overridable so you can swap in a different corpus later (Phase 3+)
POLICY_DIR = Path(os.getenv("POLICY_DIR", DATA_DIR / "policies"))

# --- RAG / cache ---
CACHE_DIR = ROOT / ".cache"          # bundled, read-only policy index lives here
CHUNK_MAX_CHARS = 1200

# --- Caching + usage (Phase 8) ---
# Runtime caches must be written somewhere writable; the Lambda image is read-only
# except for /tmp, so redirect there when running on Lambda.
_IN_LAMBDA = bool(os.getenv("AWS_LAMBDA_FUNCTION_NAME"))
RUNTIME_CACHE_DIR = Path("/tmp/ticketpilot-cache") if _IN_LAMBDA else CACHE_DIR
SEMANTIC_CACHE_THRESHOLD = float(os.getenv("SEMANTIC_CACHE_THRESHOLD", "0.95"))
USAGE_LOG = RUNTIME_CACHE_DIR / "usage_log.jsonl"

# --- Storage backend: "local" JSON files ($0) or "aws" DynamoDB ---
BACKEND = os.getenv("TICKETPILOT_BACKEND", "local")
DDB_TICKETS_TABLE = os.getenv("DDB_TICKETS_TABLE", "ticketpilot-tickets")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")   # Lambda sets AWS_REGION automatically
