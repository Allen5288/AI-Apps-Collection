# Real Estate Enquiry Assistant — RAG for a Sydney real-estate agency

A retrieval-augmented assistant for a small Sydney real-estate
agency ("Harbourline Realty" — fictional). It answers buyer and
renter questions from the agency's own listing documents, and books
inspection enquiries. It never invents a price, an inspection time
nor an availability — if the answer is not in the listings, it says so.

## What it does for the business

- Answers after-hours questions ("is the The Ponds house pet
  friendly?", "when is the next inspection?") without an agent
  on the phone.
- Qualifies enquiries: suburb, budget, beds and rent-vs-buy are
  captured before an agent calls back.
- Routes inspection bookings to the listing agent, with the
  listing attached — no more "which property was that?".

## How it works

```
listings.json → chunks (one per listing) → TF-IDF retriever
  → top-k listings + filters → grounded answer + citations
  → "not in our listings" fallback (LLM generation lands in commit 5)
```

Same discipline as the Medical AI Assistant (see
`01 - Medical AI Assistant/EVALUATION.md`): a golden test set,
faithfulness checking, and cost measured per 100 questions before
any provider swap is judged.

## Data

`data/listings.json` — 6 synthetic Sydney listings (sale + rent).
All addresses, prices, agents and inspection times are invented
for this case; no real listings are used. Swap in the agency's
real export by keeping the same fields.

| Field | Meaning |
|---|---|
| id, address, suburb, type | Which property |
| beds, baths, parking | Size |
| price, price_type | Sale price, or weekly rent |
| status | `sale` or `rent` |
| inspection | Next inspection day/time |
| description, features | What the retriever searches |
| agent | Who the enquiry goes to |

## Run it (day 2 — ask endpoint)

```bash
cd "04 - RAG/02 - Real Estate Enquiry Assistant"
pip install -r requirements.txt
uvicorn app:app --reload        # -> http://127.0.0.1:8000/docs
```

```bash
curl -X POST http://127.0.0.1:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "3 bed house in The Ponds under $1.2m"}'
# -> answer naming the matching listing, with citations [1..k]
#    and "fallback": false

curl -X POST http://127.0.0.1:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "castle with a moat in Double Bay"}'
# -> "I could not find a listing..." with "fallback": true
```

Retrieval only (day 1) still works without installing anything:

```bash
python retrieval.py "3 bed house in The Ponds under $1.2m"
python retrieval.py "pet friendly rental" --status rent --top-k 2
python retrieval.py "apartment near Chatswood station" --suburb Chatswood
```

Python 3.11+; the retriever is standard library only, the server
needs FastAPI + uvicorn (see `requirements.txt`).

## How the answer stays grounded

- `answer.py` composes the answer from the retrieved listings
  only: every fact (price, beds, inspection time, agent) is copied
  from a listing the retriever returned, and each listing is cited
  with its retrieval score.
- When the retriever returns nothing, the endpoint answers
  "I could not find a listing..." (`fallback: true`) instead of
  guessing. A wrong answer costs the agency a wasted inspection;
  an honest "I don't know" costs nothing.
- A minimum relevance score (`MIN_SCORE = 0.15` in `app.py`)
  decides what "nothing" means: TF-IDF returns *something* for
  every query, so results below 0.15 are treated as no match.
  Measured on this 6-listing set — genuine questions score 0.19+,
  an unrelated question tops out at 0.09 — and it must be re-tuned
  when the agency's real listings replace the synthetic ones.
- The request is validated (`question` 3–500 chars, `top_k` 1–5,
  `status` only `sale`/`rent`), so a bad request gets a 422 from
  FastAPI, not a crash.

## Build plan (5 commits)

1. **Scaffold + data + retriever (done 2026-11-25):** README, synthetic
   listings, stdlib TF-IDF retriever with suburb/price/beds filters.
2. **Ask endpoint (this commit):** FastAPI server, `POST /ask` —
   retrieve, compose a grounded answer with citations +
   "not in our listings" fallback. No LLM key needed yet.
3. **Enquiry capture:** `POST /enquiries` — name, phone, listing,
   inspection time; stored as JSON; duplicate guard by phone+listing.
4. **Evaluation:** golden set + faithfulness check, reusing the
   Medical AI Assistant's eval pattern; cost per 100 questions.
5. **Provider swap + ship checklist:** Groq → Azure OpenAI via the
   provider abstraction; README runbook; case finished.
