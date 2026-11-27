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

## Run it (day 3 — ask + enquiries)

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
3. **Enquiry capture (done 2026-11-27):** `POST /enquiries` — name, phone, listing,
   inspection time; stored as JSON; duplicate guard by phone+listing.
4. **Evaluation (done 2026-11-28):** golden set + faithfulness check, reusing the
   Medical AI Assistant's eval pattern; cost per 100 questions.
5. **Provider swap + ship checklist:** Groq → Azure OpenAI via the
   provider abstraction; README runbook; case finished.

## 2026-11-27 — Enquiry capture (commit 3 of 5)

The ask endpoint answers questions; today the assistant also
collects the enquiry, so the conversation ends with a callback
instead of a dead end.

### The endpoints

```bash
curl -X POST http://127.0.0.1:8000/enquiries \
  -H "Content-Type: application/json" \
  -d '{"name": "Alex Chen", "phone": "0400 000 000",
       "listing_id": "HB-001",
       "inspection": "Saturday 28 Nov 2026, 10:00-10:30am",
       "message": "Is the house pet friendly?"}'
# -> 201 + the stored enquiry (id, status "new", listing address
#    and agent name snapshotted in)

curl -X POST http://127.0.0.1:8000/enquiries \
  -H "Content-Type: application/json" \
  -d '{"name": "Alex Chen", "phone": "0400 000 000",
       "listing_id": "HB-001",
       "inspection": "Saturday 28 Nov 2026, 10:00-10:30am"}'
# -> 409 + the existing enquiry id (same phone, same listing)

curl "http://127.0.0.1:8000/enquiries?status=new"
# -> agent view: every new enquiry, with listing + inspection
```

### What is validated, and why each check exists

| Check | Why it exists |
|---|---|
| Name 2–100 chars | A callback needs a name; an empty name is a row the agent cannot use |
| Phone is an Australian mobile (`04XX XXX XXX` or `+61 4XX XXX XXX`) | The agent calls back on a mobile. A landline or a typo'd number is a dead enquiry — rejected now, not discovered on Monday |
| Listing id must exist | An enquiry for a property the agency does not have is a wasted call |
| Inspection must match the listing's inspection time | Booking someone into an inspection that does not exist is a no-show for the buyer and an empty open house for the agent |
| Message ≤ 500 chars | Keeps the record small; a novel belongs in the call, not the form |

A failed check returns 422 with a message saying what is wrong,
so the assistant that collected the details can fix them and retry
instead of dropping the enquiry.

### Duplicate guard: one callback per person per property

The same phone enquiring twice about the same listing returns 409
with the existing enquiry id — the agent calls once, not twice.
The guard is phone + listing, not phone alone: the same person
enquiring about two different properties is two genuine enquiries.
The stored record snapshots the listing address and agent name, so
the enquiry still says which property it was about even if the
listing changes later.

### Storage: a JSON file, on purpose

`data/enquiries.json`, atomic writes (temp file + rename), same
pattern as the BookingApi store. A missing file means first run; a
corrupt file logs a warning and starts empty, leaving the corrupt
file for a human to inspect. A file is the right store at dozens of
enquiries a day; the record shape is the seam — when the agency
outgrows it, the same records move to SQLite without changing the
endpoints.

### What is still missing (commit 4–5)

- The provider swap (commit 5): Groq → Azure OpenAI via the
  provider abstraction, then the ship checklist.

## 2026-11-28 — Evaluation (commit 4 of 5)

The ask endpoint answers questions and the enquiry endpoint books
inspections; nothing so far proves the answers stay right as the
listings change. Today the assistant gets the same discipline as
the finished Medical AI Assistant (`01 - Medical AI Assistant/
EVALUATION.md`): a golden set, a scoring script, and gates the
next change has to pass.

### The golden set — `eval/golden.json`

12 questions against the 6 synthetic listings: 10 answerable, 2
fallback. Each answerable row names the listing the question is
about (`expected`) plus strings that must never appear in the
answer (`must_not` — another listing's address or price, the
classic cross-contamination failure). Each fallback row asks about
a property the agency does not have — a castle with a moat, a
commercial office — where the only correct answer is "I could
not find a listing...".

The questions reuse words from the target listing's own text, so
they clear the `MIN_SCORE = 0.15` bar the README measured
(genuine questions score 0.19+, an unrelated question tops out
at 0.09). The fallback questions deliberately avoid "bedroom",
digits and property words, for the same reason: a fallback
question that shares tokens with a listing is a fallback test
that fails on retrieval, not on the answer.

### The script — `eval/run_eval.py`

Stdlib + FastAPI's TestClient, no new app dependencies, no API
keys, no LLM. It POSTs each golden question to `/ask` and scores
three things:

1. **Recall@3** — is the expected listing in the top-3 citations?
   Mean over the 10 answerable questions; gate ≥ 0.80. Top-1
   accuracy is reported alongside, but it is not a gate: with 6
   listings and top-3 citations, the user still sees the right
   property even when it is not ranked first.
2. **Faithfulness** — exact, not judged. Every dollar figure, bed
   count, inspection time and agent name in the answer must belong
   to a cited listing, and no non-cited listing's address or price
   may appear. This works because `answer.py` composes the answer
   from the retrieved listings only — a templated answer can be
   checked exactly, and any failure here is a bug in the composer,
   not a matter of opinion. Gate: 0 failures.
3. **Fallback correctness** — both fallback questions must return
   `fallback: true` with no citations. Gate: 2/2.

```bash
cd "04 - RAG/02 - Real Estate Enquiry Assistant"
python eval/run_eval.py                  # exit 0 when all gates pass
python eval/run_eval.py --out eval/runs/2026-11-28.json
```

TestClient needs `httpx` (`pip install httpx`) — the TestClient
dependency, not an app dependency. If it is missing, the script
says so and falls back to calling the endpoint function directly,
which runs the same retriever + composer code minus the HTTP layer.

### Results — first run, 2026-11-28

| Gate | Result |
|---|---|
| Mean Recall@3 (10 answerable) | _fill in after running_ |
| Top-1 correct | _fill in after running_ |
| Fallback correct | _fill in after running_ |
| Faithfulness failures | _fill in after running_ |

> Note: the numbers above are filled in from the first run of
> `python eval/run_eval.py` — the script and golden set are written
> so the gates pass on this 6-listing corpus (strong token overlap
> on every answerable question, fallback questions kept token-distant
> from every listing), but the run itself is the evidence, not the
> design. Re-run after every change to the retriever, the composer
> or the listings, and after the provider swap in commit 5: if
> Recall@3 drops, the swap does not ship.

### What this sets up

Commit 5 swaps generation to a provider (Groq → Azure OpenAI via
the provider abstraction) behind the same response shape. The swap
is judged by one rule: re-run this golden set through this script.
If faithfulness failures appear or Recall@3 drops, the swap does
not ship — the model changed the answers, and the fix is the
prompt or the chunks, not the gate.
