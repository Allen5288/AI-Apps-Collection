"""TF-IDF retrieval for the Physio Clinic RAG Assistant (concept demo).

Retrieval works locally with only the Python standard library - no paid
LLM key and no extra embedding library are needed. A document is a chunk
of one Markdown file in ``data/`` (one ``##`` section). Each chunk is scored
against the question with TF-IDF cosine similarity.

Pluggable LLM spot: ``answer()`` first asks ``llm.generate_answer()``
(see ``llm.py``). That returns ``None`` unless a provider is configured,
so by default the answer below is extractive - it quotes the retrieved
chunk and cites its source document. Swap in OpenAI or Claude there later
without changing the retrieval or the API.

Rule: if the best score is below ``MIN_SCORE`` the assistant must say the
answer is not in the documents, and must not cite a source.
"""

from __future__ import annotations

import math
import re
from pathlib import Path

MIN_SCORE = 0.10
TOP_K = 3

STOPWORDS = {
    "a", "an", "the", "and", "or", "of", "to", "in", "on", "for", "is",
    "are", "was", "were", "do", "does", "did", "you", "your", "we", "our",
    "i", "me", "my", "it", "its", "this", "that", "with", "at", "by", "can",
    "could", "how", "what", "when", "where", "who", "why", "is", "there",
    "here", "please", "if", "so", "as", "be", "have", "has", "had", "will",
}

NOT_IN_DOCUMENTS = (
    "I could not find that in our documents. "
    "Please contact the clinic directly for questions that are not "
    "covered by the clinic information in this demo."
)


def tokenize(text: str) -> list[str]:
    """Lowercase word tokens, dropping stopwords."""
    return [t for t in re.findall(r"[a-z0-9]+", text.lower()) if t not in STOPWORDS]


def load_chunks(data_dir: str | Path) -> list[dict]:
    """Split every ``*.md`` file in ``data_dir`` into ``##`` sections."""
    chunks: list[dict] = []
    for path in sorted(Path(data_dir).glob("*.md")):
        text = path.read_text(encoding="utf-8")
        sections = re.split(r"^##\s+", text, flags=re.MULTILINE)
        for section in sections[1:]:
            lines = section.strip().splitlines()
            if not lines:
                continue
            title = lines[0].strip()
            body = "\n".join(lines[1:]).strip()
            if not body:
                continue
            chunks.append({
                "source": path.name,
                "title": title,
                "text": body,
                "full_text": f"{title}\n{body}",
            })
    return chunks


def _tfidf_vectors(chunks: list[dict]) -> tuple[list[dict], dict[str, float]]:
    """Return (chunk vectors, idf) using plain TF-IDF cosine scoring."""
    docs = [tokenize(c["full_text"]) for c in chunks]
    doc_count = len(docs)
    doc_freq: dict[str, int] = {}
    for tokens in docs:
        for token in set(tokens):
            doc_freq[token] = doc_freq.get(token, 0) + 1
    idf = {
        token: math.log((doc_count + 1) / (freq + 1)) + 1.0
        for token, freq in doc_freq.items()
    }
    vectors: list[dict] = []
    for tokens in docs:
        vec: dict[str, float] = {}
        for token in tokens:
            vec[token] = vec.get(token, 0.0) + 1.0
        length = max(len(tokens), 1)
        vec = {t: (count / length) * idf[t] for t, count in vec.items()}
        norm = math.sqrt(sum(v * v for v in vec.values())) or 1.0
        vectors.append({t: v / norm for t, v in vec.items()})
    return vectors, idf


class Retriever:
    """TF-IDF retriever over the synthetic clinic documents."""

    def __init__(self, data_dir: str | Path) -> None:
        self.chunks = load_chunks(data_dir)
        self.vectors, self.idf = _tfidf_vectors(self.chunks)

    def retrieve(self, question: str, top_k: int = TOP_K) -> list[dict]:
        """Return the best ``top_k`` chunks with a cosine ``score``."""
        tokens = tokenize(question)
        if not tokens or not self.chunks:
            return []
        query: dict[str, float] = {}
        for token in tokens:
            query[token] = query.get(token, 0.0) + 1.0
        query = {
            t: (c / len(tokens)) * self.idf.get(t, 1.0)
            for t, c in query.items()
        }
        norm = math.sqrt(sum(v * v for v in query.values())) or 1.0
        query = {t: v / norm for t, v in query.items()}
        scored = []
        for chunk, vec in zip(self.chunks, self.vectors):
            score = sum(query.get(t, 0.0) * v for t, v in vec.items())
            scored.append({**chunk, "score": round(score, 4)})
        scored.sort(key=lambda c: c["score"], reverse=True)
        return scored[:top_k]

    def answer(self, question: str) -> dict:
        """Answer from the retrieved chunks, citing the source document.

        Returns ``{"answer", "sources", "score", "answered"}``. When nothing
        relevant is retrieved, ``answered`` is False and no source is cited.
        """
        results = self.retrieve(question)
        if not results or results[0]["score"] < MIN_SCORE:
            return {
                "answer": NOT_IN_DOCUMENTS,
                "sources": [],
                "score": results[0]["score"] if results else 0.0,
                "answered": False,
            }
        top = results[0]
        # PLUGGABLE LLM SPOT: if a provider is configured in llm.py, let
        # it draft from the retrieved context; otherwise use the extractive
        # answer below. The citation still comes from retrieval. If the
        # provider call fails (for example, it is not implemented yet),
        # fall back to the extractive answer instead of failing the request.
        try:
            from app.llm import generate_answer as _llm_answer
        except Exception:
            try:
                from llm import generate_answer as _llm_answer
            except Exception:
                _llm_answer = None
        llm_text = None
        if _llm_answer:
            try:
                llm_text = _llm_answer(question, top["full_text"])
            except Exception:
                llm_text = None
        if llm_text:
            body = llm_text.strip()
        else:
            body = _best_sentences(top["full_text"], question)
        sources = []
        for result in results:
            if result["score"] >= MIN_SCORE and result["source"] not in sources:
                sources.append(result["source"])
        return {
            "answer": f"{body}\n\nSource: {top['source']} - {top['title']}",
            "sources": sources,
            "score": top["score"],
            "answered": True,
        }


def _best_sentences(text: str, question: str, limit: int = 3) -> str:
    """Pick the sentences in ``text`` that share the most terms with the question."""
    wanted = set(tokenize(question))
    sentences = [s.strip() for s in re.split(r"(?<=[.!])\s+", text) if s.strip()]
    if not sentences:
        return text[:500]
    scored = sorted(
        sentences,
        key=lambda s: len(wanted & set(tokenize(s))),
        reverse=True,
    )
    chosen = [s for s in scored[:limit] if wanted & set(tokenize(s))]
    return " ".join(chosen or sentences[:1])
