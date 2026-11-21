"""Pluggable LLM layer for the Physio Clinic RAG Assistant (concept demo).

By design this demo runs WITHOUT a paid LLM key:
``generate_answer()`` returns ``None`` unless a provider is explicitly
configured, and ``rag.py`` then uses its extractive answer (quoted from
the retrieved document, with a citation).

To plug in a paid provider later, without changing retrieval or the API:

1. Set the environment variable, for example::

       export LLM_PROVIDER=openai
       export OPENAI_API_KEY=...

   or ``LLM_PROVIDER=anthropic`` with ``ANTHROPIC_API_KEY``.
2. Install the provider SDK, for example ``pip install openai``.
3. Implement ``_call_openai()`` / ``_call_anthropic()`` below. Each must
   answer ONLY from the ``context`` passed in, and say the answer is not
   in the documents if the context does not cover the question.

No key is ever read from, or written to, the demo data. The demo data
remains synthetic and contains no real patient information.
"""

from __future__ import annotations

import os

SYSTEM_PROMPT = (
    "You are a reception assistant for a physiotherapy clinic. "
    "Answer ONLY from the clinic documents given as context. "
    "If the context does not answer the question, say so and do not guess. "
    "Do not give medical advice or a diagnosis."
)


def configured_provider() -> str | None:
    """Return the provider name from the environment, or ``None``."""
    provider = os.environ.get("LLM_PROVIDER", "").strip().lower()
    if provider in {"openai", "anthropic"}:
        return provider
    return None


def generate_answer(question: str, context: str, provider: str | None = None) -> str | None:
    """Draft an answer from ``context`` with a configured LLM, or ``None``.

    Returns ``None`` when no provider is configured, so the caller falls
    back to its extractive, cited answer. This keeps the demo runnable
    locally with no key and no network call.
    """
    provider = (provider or configured_provider() or "").lower()
    if provider == "openai":
        return _call_openai(question, context)
    if provider == "anthropic":
        return _call_anthropic(question, context)
    return None


def _call_openai(question: str, context: str) -> str | None:
    # PLUGGABLE SPOT - implement when an OpenAI key is available, e.g.:
    #   from openai import OpenAI
    #   client = OpenAI()
    #   reply = client.chat.completions.create(
    #       model="gpt-4o-mini",
    #       messages=[
    #           {"role": "system", "content": SYSTEM_PROMPT},
    #           {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"},
    #       ],
    #   )
    #   return reply.choices[0].message.content
    raise NotImplementedError(
        "OpenAI provider is a pluggable spot in llm.py - set LLM_PROVIDER=openai, "
        "install the openai package and implement _call_openai(). "
        "The demo runs without it."
    )


def _call_anthropic(question: str, context: str) -> str | None:
    # PLUGGABLE SPOT - implement when an Anthropic key is available, e.g.:
    #   import anthropic
    #   client = anthropic.Anthropic()
    #   reply = client.messages.create(
    #       model="claude-haiku-4-5", max_tokens=300, system=SYSTEM_PROMPT,
    #       messages=[{"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"}],
    #   )
    #   return reply.content[0].text
    raise NotImplementedError(
        "Anthropic provider is a pluggable spot in llm.py - set LLM_PROVIDER=anthropic, "
        "install the anthropic package and implement _call_anthropic(). "
        "The demo runs without it."
    )
