# Real Estate Enquiry Assistant — RAG for a Sydney real-estate agency

A retrieval-augmented assistant for a small Sydney real-estate
agency ("Harbourline Realty" — fictional). It answers buyer and
renter questions from the agency's own listing documents, and books
inspection enquiries. It never invents a price, an inspection time
or an availability — if the answer is not in the listings, it says so.

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
  → top-k listings + filters → LLM prompt (provider abstraction)
  → answer with citations → "not in our listings" fallback
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

## Run it (day 1 — retrieval only)

```bash
cd "04 - RAG/02 - Real Estate Enquiry Assistant"
python retrieval.py "3 bed house in The Ponds under $1.2m"
python retrieval.py "pet friendly rental" --status rent --top-k 2
python retrieval.py "apartment near Chatswood station" --suburb Chatswood
```

Python 3.11+, standard library only — no install step.

## Build plan (5 commits)

1. **Scaffold + data + retriever (this commit):** README, synthetic
   listings, stdlib TF-IDF retriever with suburb/price/beds filters.
2. **Ask endpoint:** FastAPI server, `POST /ask` — retrieve, prompt,
   answer with citations + "not in our listings" fallback.
3. **Enquiry capture:** `POST /enquiries` — name, phone, listing,
   inspection time; stored as JSON; duplicate guard by phone+listing.
4. **Evaluation:** golden set + faithfulness check, reusing the
   Medical AI Assistant's eval pattern; cost per 100 questions.
5. **Provider swap + ship checklist:** Groq → Azure OpenAI via the
   provider abstraction; README runbook; case finished.
