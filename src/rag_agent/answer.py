from ..shared import llm
from .retrieve import retrieve

MIN_SCORE = 0.35   # below this, we treat retrieval as "no relevant policy found"

def answer_question(question: str, k: int = 4) -> dict:
    chunks = retrieve(question, k)

    # 1. Refuse when nothing is relevant enough (the grounding guarantee).
    if not chunks or chunks[0]["score"] < MIN_SCORE:
        return {"answer": "I couldn't find that in the policy documents.",
                "citations": [], "refused": True}

    # 2. Build the context block the model must answer FROM.
    context = "\n\n".join(
        f"[{c['source']} :: {c['section']}]\n{c['text']}" for c in chunks
    )

    system = (
        "You answer questions about a fintech company's policy documents.\n"
        "Rules:\n"
        "1. Answer ONLY using the provided context, never outside knowledge.\n"
        "2. Cite the [source :: section] you used at the end of your answer.\n"
        "3. If the context does not contain the answer, say you don't have that "
        "information in the policy documents -- do not guess."
    )
    user = f"Context:\n{context}\n\nQuestion: {question}"
    answer = llm.chat([{"role": "system", "content": system},
                       {"role": "user", "content": user}])

    # 4. Return the answer + which chunks it was allowed to use.
    citations = [{"source": c["source"], "section": c["section"]} for c in chunks]
    return {"answer": answer, "citations": citations, "refused": False}