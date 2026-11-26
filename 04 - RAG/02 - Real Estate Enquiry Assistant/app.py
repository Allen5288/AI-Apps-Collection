"""Ask endpoint for the Real Estate Enquiry Assistant.

FastAPI server: POST /ask retrieves matching listings with the
stdlib TF-IDF retriever, composes a grounded answer (see
answer.py), and returns the answer with citations. No LLM key is
needed yet — the answer is composed from the retrieved listings
themselves, and the provider call lands in commit 5 behind the
same response shape.

POST /enquiries captures an inspection enquiry (see enquiries.py):
name, phone, listing and inspection time, stored as JSON with a
duplicate guard by phone + listing, so the listing agent gets one
callback per person per property.

Run:
    pip install -r requirements.txt
    uvicorn app:app --reload        # -> http://127.0.0.1:8000/docs

Try:
    curl -X POST http://127.0.0.1:8000/ask \\
      -H "Content-Type: application/json" \\
      -d '{"question": "3 bed house in The Ponds under $1.2m"}'
    curl -X POST http://127.0.0.1:8000/enquiries \\
      -H "Content-Type: application/json" \\
      -d '{"name": "Alex Chen", "phone": "0400 000 000", "listing_id": "HB-001", "inspection": "Saturday 28 Nov 2026, 10:00-10:30am"}'
    curl http://127.0.0.1:8000/health
"""

from __future__ import annotations

import json

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from answer import compose_answer
from enquiries import (
    create_enquiry,
    load_enquiries,
    validate_enquiry,
)
from retrieval import DATA_PATH, Retriever

app = FastAPI(title="Real Estate Enquiry Assistant")


def _load_retriever() -> Retriever:
    listings = json.loads(DATA_PATH.read_text())
    return Retriever(listings)


RETRIEVER = _load_retriever()

# Minimum TF-IDF cosine for a listing to count as a match. Measured
# on the 6-listing set: genuine questions score 0.19 and up, an
# unrelated question ("castle with a moat") tops out at 0.09.
# Without this, the retriever returns *something* for every query
# and the "not in our listings" fallback can never fire. Re-tune
# on real data — the number is a property of the corpus, not a
# universal constant.


MIN_SCORE = 0.15


class AskRequest(BaseModel):
    question: str = Field(min_length=3, max_length=500)
    top_k: int = Field(default=3, ge=1, le=5)
    suburb: str | None = None
    max_price: int | None = None
    min_beds: int | None = None
    status: str | None = Field(default=None, pattern="^(sale|rent)$")


class Citation(BaseModel):
    n: int
    id: str
    address: str
    score: float


class AskResponse(BaseModel):
    answer: str
    citations: list[Citation]
    fallback: bool


class EnquiryRequest(BaseModel):
    name: str
    phone: str
    listing_id: str
    inspection: str
    message: str | None = None


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "listings": len(RETRIEVER.listings)}


@app.post("/ask", response_model=AskResponse)
def ask(body: AskRequest) -> AskResponse:
    results = [
        r
        for r in RETRIEVER.search(
            body.question,
            top_k=body.top_k,
            suburb=body.suburb,
            max_price=body.max_price,
            min_beds=body.min_beds,
            status=body.status,
        )
        if r["score"] >= MIN_SCORE
    ]
    composed = compose_answer(body.question, results)
    return AskResponse(
        answer=composed["answer"],
        citations=composed["citations"],
        fallback=composed["fallback"],
    )


@app.post("/enquiries", status_code=201)
def create_enquiry_endpoint(body: EnquiryRequest):
    """Capture an inspection enquiry. 201 with the stored record;
    409 when this phone already enquired about this listing; 422
    when the name, phone, listing or inspection does not check out.
    The 422 message says what is wrong — the caller (and the
    assistant that collected the details) can fix it and retry."""
    try:
        cleaned = validate_enquiry(
            body.model_dump(), RETRIEVER.listings
        )
    except ValueError as exc:
        return JSONResponse(
            status_code=422, content={"detail": str(exc)}
        )
    enquiries = load_enquiries()
    record, created = create_enquiry(cleaned, enquiries)
    if not created:
        return JSONResponse(
            status_code=409,
            content={
                "detail": "an enquiry from this phone already exists "
                f"for {cleaned['listing_id']}",
                "enquiry_id": record["id"],
            },
        )
    return record


@app.get("/enquiries")
def list_enquiries(status: str | None = None) -> dict:
    """Agent view: all enquiries, optionally filtered by status
    (`?status=new`). The agent works through the `new` ones and
    marks them contacted outside this API for now."""
    enquiries = load_enquiries()
    if status is not None:
        enquiries = [e for e in enquiries if e["status"] == status]
    return {"enquiries": enquiries}
