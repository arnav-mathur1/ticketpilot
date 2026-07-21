"""Thin wrappers around the OpenAI client for chat + embeddings.

Everything that calls the LLM goes through here, so retries/caching/logging
(added in later phases) only have to be wired in one place.
"""
from openai import OpenAI

from . import config

# The client reads OPENAI_API_KEY from the environment (loaded by config).
_client = OpenAI()


def chat(messages: list[dict], *, model: str | None = None,
         temperature: float = 0.0, **kwargs) -> str:
    """Call chat completions and return the assistant message text.

    messages: [{"role": "system"|"user"|"assistant", "content": "..."}]
    Pass response_format={"type": "json_object"} via kwargs to force JSON.
    """
    resp = _client.chat.completions.create(
        model=model or config.OPENAI_MODEL,
        messages=messages,
        temperature=temperature,
        **kwargs,
    )
    return resp.choices[0].message.content


def embed(texts: str | list[str]) -> list[float] | list[list[float]]:
    """Embed a string (-> one vector) or a list of strings (-> list of vectors)."""
    single = isinstance(texts, str)
    inp = [texts] if single else list(texts)
    resp = _client.embeddings.create(model=config.OPENAI_EMBED_MODEL, input=inp)
    vecs = [d.embedding for d in resp.data]
    return vecs[0] if single else vecs
