import time

from ..shared import llm
from ..shared.cache import QueryCache
from ..shared.usage import log_usage
from .retrieve import retrieve

MIN_SCORE = 0.35   # below this, we treat retrieval as "no relevant policy found"

def answer_question(question: str, k: int = 4, use_cache: bool = True) -> dict:
    t0 = time.time()
    # Embed once (cached); reused for the semantic cache AND retrieval below.
    q_vec = llm.embed(question)

    if use_cache:
        cache = QueryCache()
        hit, kind = cache.lookup(question, q_vec)
        if hit is not None:                     # exact or semantic cache hit
            log_usage(f"rag_cache_{kind}", None, time.time() - t0, cached=True)
            return {**hit, "cache": kind}

    chunks = retrieve(question, k)

    # 1. Refuse when nothing is relevant enough (the grounding guarantee).
    if not chunks or chunks[0]["score"] < MIN_SCORE:
        result = {"answer": "I couldn't find that in the policy documents.",
                  "citations": [], "refused": True}
    else:
        # 2. Build the context block the model must answer FROM.
        context = "\n\n".join(
            f"[{c['source']} :: {c['section']}]\n{c['text']}" for c in chunks
        )

        system = (
            "You answer questions about a fintech company's policy documents.\n"
            "Rules:\n"
            "1. Answer ONLY using the provided context, never outside knowledge.\n"
            "2. Cite the exact bracketed [source :: section] label shown above the "
            "passage you used, copied verbatim (e.g. [refund_billing_policy.txt :: "
            "1. Subscription refund window]).\n"
            "3. If the context does not contain the answer, say you don't have that "
            "information in the policy documents -- do not guess."
        )
        user = f"Context:\n{context}\n\nQuestion: {question}"
        answer = llm.chat([{"role": "system", "content": system},
                           {"role": "user", "content": user}])
        citations = [{"source": c["source"], "section": c["section"]} for c in chunks]
        result = {"answer": answer, "citations": citations, "refused": False}

    if use_cache:
        cache.store(question, q_vec, result)
    return {**result, "cache": None}