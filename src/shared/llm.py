"""Thin wrappers around the OpenAI client for chat + embeddings.

Everything that calls the LLM goes through here, so caching + usage logging
(Phase 8) are wired in one place:
  - embeddings are cached by content hash (each text embedded once)
  - every real API call logs tokens + latency to the usage log
"""
import time

from openai import OpenAI

from . import config

# The client reads OPENAI_API_KEY from the environment (loaded by config).
_client = OpenAI()
_embed_cache = None


def chat(messages: list[dict], *, model: str | None = None,
         temperature: float = 0.0, **kwargs) -> str:
    """Call chat completions and return the assistant message text.

    messages: [{"role": "system"|"user"|"assistant", "content": "..."}]
    Pass response_format={"type": "json_object"} via kwargs to force JSON.
    """
    from .usage import log_usage
    t0 = time.time()
    resp = _client.chat.completions.create(
        model=model or config.OPENAI_MODEL,
        messages=messages,
        temperature=temperature,
        **kwargs,
    )
    log_usage("chat", resp.usage, time.time() - t0, cached=False)
    return resp.choices[0].message.content


def embed(texts: str | list[str]) -> list[float] | list[list[float]]:
    """Embed a string (-> one vector) or a list of strings (-> list of vectors).

    Results are cached by content hash, so identical text is embedded only once.
    """
    global _embed_cache
    from .cache import EmbeddingCache
    from .usage import log_usage

    single = isinstance(texts, str)
    inp = [texts] if single else list(texts)
    if _embed_cache is None:
        _embed_cache = EmbeddingCache()

    def _call(items: list[str]) -> list[list[float]]:
        t0 = time.time()
        resp = _client.embeddings.create(model=config.OPENAI_EMBED_MODEL, input=items)
        log_usage("embed", None, time.time() - t0, cached=False)
        return [d.embedding for d in resp.data]

    vecs = _embed_cache.get_or_embed(inp, _call)
    return vecs[0] if single else vecs
