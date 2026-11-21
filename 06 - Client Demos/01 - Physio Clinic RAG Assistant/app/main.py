"""FastAPI backend for the Physio Clinic RAG Assistant (concept demo).

Run locally (from this case folder)::

    pip install -r requirements.txt
    uvicorn app.main:app --reload

Then open http://127.0.0.1:8000/ for the chat demo, or POST a question to
``/ask``. No LLM key is needed - retrieval is TF-IDF over ``data/``
(see ``rag.py``), and answers cite their source document.
"""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel

try:
    from app.rag import Retriever
except ImportError:  # running as ``python app/main.py``
    from rag import Retriever

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
WEB_DIR = BASE_DIR / "web"

app = FastAPI(title="Physio Clinic RAG Assistant (concept demo)")
retriever = Retriever(DATA_DIR)


class AskRequest(BaseModel):
    question: str


class AskResponse(BaseModel):
    answer: str
    sources: list[str]
    score: float
    answered: bool


@app.get("/")
def demo_page():
    """Serve the chat demo page."""
    return FileResponse(WEB_DIR / "index.html")


@app.get("/health")
def health():
    return {
        "status": "ok",
        "demo": True,
        "documents": sorted({c["source"] for c in retriever.chunks}),
        "chunks": len(retriever.chunks),
    }


@app.get("/documents")
def documents():
    return {"documents": sorted({c["source"] for c in retriever.chunks})}


@app.post("/ask", response_model=AskResponse)
def ask(request: AskRequest):
    """Answer a question from the clinic documents, with a citation."""
    return retriever.answer(request.question.strip())


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
