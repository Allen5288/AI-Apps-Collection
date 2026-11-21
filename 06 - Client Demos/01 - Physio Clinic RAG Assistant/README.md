# Physio Clinic RAG Assistant — Concept Demo

> **Concept demo only.** There is no real client, no real clinic, no testimonials and no revenue behind this case. All clinic information is synthetic demo data, invented for this demo.

## Problem

A physiotherapy clinic gets the same questions again and again — opening hours, prices, bulk billing, exercise handouts, bookings and cancellations. Staff time goes to repeating answers that already exist in the clinic's own documents, and patients wait for a reply.

This demo shows how a small retrieval-augmented generation (RAG) assistant could answer those questions from the clinic's own documents, with a citation for every answer, and say clearly when a question is not covered by those documents.

This is a concept demo, not a product for a real clinic and not medical advice. It does not diagnose, order scans, or advise on medicines.

## Build

- **Backend:** Python FastAPI (`app/main.py`). Endpoints: `GET /` (chat demo page), `GET /health`, `GET /documents`, `POST /ask`.
- **Retrieval:** TF-IDF cosine similarity over the demo documents, using only the Python standard library (`app/rag.py`). Documents in `data/` are split into sections (one `##` heading per chunk). No paid LLM key and no extra embedding library are needed to run it.
- **Answers and citations:** `Retriever.answer()` returns the best-matching chunk, quotes the most relevant sentences, and cites the source document, for example `Source: prices-and-hours.md - Prices`. If the best score is below the threshold (0.10), it answers "I could not find that in our documents" and cites no source.
- **Pluggable LLM:** `app/llm.py` is the pluggable spot for OpenAI or Claude later. `generate_answer()` returns `None` unless `LLM_PROVIDER` is set, so the demo runs without a key; the citation still comes from retrieval.
- **Frontend:** a simple HTML chat demo page (`web/index.html`) that posts questions to `/ask` and shows the answer and its sources. No build step is needed.
- **Evaluation:** `eval/evaluate.py` runs a golden set of 10 patient FAQs plus one out-of-scope question, and checks that each answer cites the right source and contains the expected key fact.

```
06 - Client Demos/01 - Physio Clinic RAG Assistant/
├── README.md
├── requirements.txt
├── app/
│   ├── main.py        # FastAPI backend, serves web/index.html
│   ├── rag.py         # TF-IDF retrieval, answers, citations, abstention
│   └── llm.py         # Pluggable LLM spot (OpenAI / Claude, optional)
├── data/              # Synthetic demo documents (see Demo data note)
│   ├── services.md
│   ├── prices-and-hours.md
│   ├── bulk-billing.md
│   ├── exercise-handouts.md
│   └── faqs.md
├── web/
│   └── index.html     # Chat demo page
└── eval/
    └── evaluate.py    # Golden test set: 10 FAQs + 1 out-of-scope check
```

## How to run

From this case folder:

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Then open <http://127.0.0.1:8000/> and try, for example:

- "What are your opening hours on Saturday?"
- "How much does an initial consultation cost?"
- "Do you bulk bill?"
- "What is my MRI result?" — this one is not in the documents, so the assistant says so.

Run the evaluation (no key needed):

```bash
python eval/evaluate.py
```

It prints a PASS/FAIL line for each golden question and a summary, and exits 0 only if every check passes.

You can also call the API directly:

```bash
curl -X POST http://127.0.0.1:8000/ask -H "Content-Type: application/json" -d '{"question": "Do you offer telehealth appointments?"}'
```

## Demo data note

**All data in `data/` is synthetic demo data, clearly labelled as such in every file.** Prices, hours, services, funding rules and exercise descriptions are invented for this demo. There is no real patient data, no real clinic, and no real client. Do not use these documents as real clinic information or as medical advice.

## Limitations

- Retrieval is keyword-based TF-IDF, not a semantic embedding model, so wording that is very different from the documents may score poorly.
- The demo has no authentication, no booking system and no connection to any real clinic system.
- Answers are extractive quotes from the demo documents unless an LLM provider is plugged in (see `app/llm.py`).
