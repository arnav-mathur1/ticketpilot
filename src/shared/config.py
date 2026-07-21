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

# --- RAG / cache (used from Phase 3 onward) ---
CACHE_DIR = ROOT / ".cache"
CHUNK_MAX_CHARS = 1200
