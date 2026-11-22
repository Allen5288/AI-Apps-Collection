# Medical AI Assistant — Evaluation and the Azure Swap

> Daily build note, started 2026-11-20. This file lives with the
> Medical AI Assistant in `04 - RAG/01 - Medical AI Assistant/` and
> will be extended over the next few days — one build, one file.
> See `README.md` in the same folder for the current architecture:
> FastAPI + LangChain, Google embeddings, Pinecone, Groq LLaMA 3.

## 2026-11-20 — Part 1: How to evaluate this RAG system, and how it maps to Azure

### Why evaluate here, not just in the notes repo

The Knowledge Notes repo (`01 - RAG.md` / `02 - RAG-Evaluation.md`)
covers the theory. This file is the practice for *this* system:
what to measure on medical PDFs, and what changes when the same
system runs on Azure instead of Pinecone + Groq + Google.

### Evaluation plan for this assistant

1. **Golden set first (20 questions).** Pick questions from the
   PDFs already ingested, e.g. "What are the symptoms of diabetes?"
   Record the relevant chunks, the acceptable answer, and any claim
   that must never appear. Store it as `eval/golden.jsonl` (next day).
2. **Retrieval: Recall@5.** For each question, how many of the
   human-judged relevant chunks are in the top 5? Target: ≥ 0.8
   before tuning generation.
3. **Generation: faithfulness.** Every factual claim must trace to
   a retrieved chunk. In medical answers this is a safety rule,
   not a nice-to-have — add a disclaimer and never present the
   answer as a diagnosis.
4. **Access control check.** Retrieval must filter by user/tenant
   before vector search, so one user's PDFs never leak into
   another user's answers (see Knowledge Notes, RAG §3).

### AWS / Azure / current-stack mapping

The same RAG shape runs on all three — only the managed services
change. That is the point of this collection: learn the pattern
once, swap the provider.

| Layer | Current (this project) | AWS equivalent | Azure equivalent |
|---|---|---|---|
| LLM | Groq, LLaMA 3 70B | Amazon Bedrock (Claude / Llama) | Azure OpenAI, GPT-4o |
| Embeddings | Google / HuggingFace | Bedrock Titan Embeddings | Azure OpenAI `text-embedding-3-large` |
| Vector store | Pinecone | OpenSearch Serverless / pgvector on RDS | Azure AI Search (vector) |
| API | FastAPI on Render | Lambda + API Gateway | Azure Functions + API Management |
| Storage | Local / Render | S3 | Azure Blob Storage |
| Queue / async ingest | — (sync upload today) | SQS + Lambda | Service Bus + Functions |

### The Azure swap, in order (next days)

- **Day 2:** swap only embeddings + vector store — Azure OpenAI
  embeddings + Azure AI Search — keep Groq for generation, so one
  change is measured at a time.
- **Day 3:** swap generation to Azure OpenAI, re-run the same
  golden set, compare faithfulness and cost per 100 questions.
- **Day 4:** move the FastAPI backend to Azure Container Apps,
  keep the `/upload_pdfs` and `/ask` endpoints unchanged.

Rule: one swap per day, re-run the golden set after each swap.
If Recall@5 drops, the swap does not ship.

## 2026-11-21 — Part 2: the golden set file and the Recall@5 scoring script

Day 1 planned the evaluation; today it becomes a file and a script.
The golden set lives in the repo so every swap (Azure embeddings,
Azure OpenAI, Container Apps) is scored against the same questions.

### `eval/golden.jsonl` — the format

One JSON object per line. Three example rows — real entries use the
PDFs already ingested, with chunk ids from the actual index:

```json
{"question": "What are the symptoms of diabetes?", "relevant": ["doc-12 chunk 3", "doc-12 chunk 4"], "answer": "Increased thirst, frequent urination, fatigue and blurred vision.", "must_not": ["diabetes is caused by eating too much sugar"]}
{"question": "What should a patient do if they miss a dose of metformin?", "relevant": ["doc-07 chunk 2"], "answer": "Take it as soon as remembered, unless it is almost time for the next dose — then skip it and never double up.", "must_not": ["take two doses at once"]}
{"question": "Does this document say anything about treating diabetes with insulin pumps?", "relevant": [], "answer": "The documents do not cover insulin pumps.", "must_not": ["insulin pumps are recommended"]}
```

Rules for writing rows:

- `relevant` is empty on purpose for unanswerable questions — the
  correct behaviour is to say the documents do not cover it.
- Keep the set at 20 questions: 12 factual lookups, 4 comparisons
  or multi-document questions, 4 unanswerable ones.
- Never put real patient data in the file. Questions come from the
  public PDFs in the corpus, not from any person's records.

### Scoring script — save as `eval/score_recall.py`

The script takes the golden file and a retrieval-run output
(`question` → list of retrieved chunk ids, top 5) and prints
per-question and average Recall@5. No LLM, no API keys — the point
is a number you can trust before any model judgement enters the loop.

```python
import json
import sys


def recall_at_k(relevant: list[str], retrieved: list[str], k: int = 5) -> float:
    if not relevant:
        return 1.0  # unanswerable question: nothing to retrieve
    found = set(relevant) & set(retrieved[:k])
    return len(found) / len(relevant)


def main(golden_path: str, run_path: str) -> None:
    golden = [json.loads(line) for line in open(golden_path) if line.strip()]
    run = {json.loads(line)["question"]: json.loads(line)["retrieved"]
           for line in open(run_path) if line.strip()}
    scores = []
    for row in golden:
        score = recall_at_k(row["relevant"], run.get(row["question"], []))
        scores.append(score)
        print(f"{score:.2f}  {row['question']}")
    print(f"\nRecall@5 (mean over {len(scores)} questions): "
          f"{sum(scores) / len(scores):.2f}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
```

Run it with `python eval/score_recall.py eval/golden.jsonl eval/run-2026-11-21.jsonl`.
The retrieval-run file is produced by a tiny runner that calls the
same retrieval code the API uses and dumps the top 5 chunk ids per
question — that runner is the next addition to this folder.

### What this sets up for the Azure swap

Day 2 swaps embeddings + vector store to Azure OpenAI + Azure AI
Search. The swap is judged by one rule: re-run the same golden set
through the same script. If mean Recall@5 drops below the Day 1
baseline, the swap does not ship — no matter how good the demo looks.

## 2026-11-22 — Part 3: Azure AI Search index design — the fields, filters and metadata that make retrieval safe

Day 2 of the Azure swap replaces Pinecone with Azure AI Search. The
swap is only as good as the index design: the fields decide what can
be filtered, the filters decide who can see what, and the metadata
decides whether an answer can be traced back to a page.

### Index fields

| Field | Type | Role |
|---|---|---|
| chunk_id | Edm.String, key | Stable id: document id + chunk number |
| content | Edm.String, searchable | The chunk text |
| content_vector | Collection(Edm.Single), 1536 dims | `text-embedding-3-large` vectors |
| title | Edm.String, searchable, filterable | Document title |
| doc_type | Edm.String, filterable, facetable | Guideline / drug leaflet / FAQ |
| tenant_id | Edm.String, filterable | **The access-control boundary** |
| source_page | Edm.Int32, filterable | Page in the source PDF, for citations |
| chunk_index | Edm.Int32, sortable | Order of the chunk inside its document |
| created_at | Edm.DateTimeOffset, filterable | Freshness / recency filter |

Two rules behind this shape: every field you will ever filter on must
be declared `filterable` up front — you cannot add it later without
rebuilding the index — and the vector dimension (1536) must match the
embedding model exactly, or every query fails.

### Filters are the security boundary

Vector search has no notion of ownership: it returns whatever is
closest to the query. So every query must carry a filter, for example
`tenant_id eq 'clinic-07'`, and the filter value must come from the
authenticated session — never from the request body, where a caller
could set it to someone else's tenant. This is the same rule as
Knowledge Notes RAG §3: filter *before* vector search, and never rely
on the embedding to keep tenants apart. One user's PDFs must never
leak into another user's answers.

### Python: create the index and run a hybrid query

```python
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex, SimpleField, SearchableField, SearchField,
    SearchFieldDataType, VectorSearch, HnswAlgorithmConfiguration,
    VectorSearchProfile,
)
from azure.search.documents.models import VectorizedQuery

SERVICE = "https://<your-search-service>.search.windows.net"
KEY = "<key from env in real code — never commit it>"
INDEX = "medical-chunks"

fields = [
    SimpleField(name="chunk_id", type=SearchFieldDataType.String, key=True),
    SearchableField(name="content", type=SearchFieldDataType.String),
    SearchField(
        name="content_vector",
        type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
        searchable=True, vector_search_dimensions=1536,
        vector_search_profile_name="default",
    ),
    SimpleField(name="tenant_id", type=SearchFieldDataType.String, filterable=True),
    SimpleField(name="doc_type", type=SearchFieldDataType.String, filterable=True, facetable=True),
    SearchableField(name="title", type=SearchFieldDataType.String),
    SimpleField(name="source_page", type=SearchFieldDataType.Int32, filterable=True),
    SimpleField(name="chunk_index", type=SearchFieldDataType.Int32, sortable=True),
]

index = SearchIndex(
    name=INDEX, fields=fields,
    vector_search=VectorSearch(
        algorithms=[HnswAlgorithmConfiguration(name="hnsw")],
        profiles=[VectorSearchProfile(name="default", algorithm_configuration_name="hnsw")],
    ),
)
SearchIndexClient(SERVICE, AzureKeyCredential(KEY)).create_or_update_index(index)


def search(question: str, embedding: list[float], tenant_id: str, k: int = 5):
    client = SearchClient(SERVICE, INDEX, AzureKeyCredential(KEY))
    results = client.search(
        search_text=question,  # keyword half of hybrid search
        vector_queries=[VectorizedQuery(vector=embedding, k_nearest_neighbors=k, fields="content_vector")],
        filter=f"tenant_id eq '{tenant_id}'",  # the access-control boundary
        top=k,
    )
    return [{"chunk_id": r["chunk_id"], "content": r["content"], "score": r["@search.score"]} for r in results]
```

Notes: hybrid search runs keyword and vector retrieval together and
merges the rankings — keyword catches exact drug names, vector catches
meaning. `tenant_id` must be validated (alphanumeric, from the
session) before it is interpolated into the filter string. HNSW is the
default approximate-nearest-neighbour algorithm; exact search is
slower and unnecessary at this scale.

### Chunk metadata rules

- Keep `chunk_index` and `source_page` on every chunk, so an answer
  can cite the exact page it came from.
- Keep the 400–600 token chunk size from Part 1. Changing chunk size
  means re-embedding and re-indexing everything — do it deliberately.
- Never index raw patient data. The corpus is public PDFs only.
- Changing the embedding model means a full re-index: old vectors
  are meaningless to the new model. Budget for it before swapping.

### What this sets up

The Day 2 swap is judged by one rule: re-run the same golden set
through the same `eval/score_recall.py` from Part 2. If mean Recall@5
drops below the Pinecone baseline, the swap does not ship — no matter
how good the demo looks.

### What I will add next in this file

- 2026-11-24: the Day 3 generation swap to Azure OpenAI, scored
  against the same golden set — faithfulness and cost per 100
  questions, side by side.
- Later: moving the FastAPI backend to Azure Container Apps.

## 2026-11-23 — Part 4: cost per 100 questions — Pinecone + Groq vs Azure AI Search + Azure OpenAI

Day 3 of the Azure swap is a generation change, but before swapping
the model it is worth pricing the two stacks. A RAG system's cost
has three parts: embeddings (cheap, mostly one-off at ingest),
retrieval (the vector store), and generation (the LLM — this is
where the money goes).

### The cost model

Per question, the LLM sees the prompt plus the retrieved chunks and
writes an answer. With 5 chunks of ~250 tokens, a ~300-token prompt
and a ~150-token answer:

- Input tokens per question: ~1,800
- Output tokens per question: ~150
- Query embedding: ~10 tokens (documents are embedded once, at
  ingest — a one-off cost, not per question)

### Indicative rates — verify on the pricing page before budgeting

Rates move. Treat these as November 2026 list prices and update
`eval/cost.py` when they change:

| Service | Indicative rate |
|---|---|
| Groq LLaMA 3 70B | ~$0.59 / 1M input tokens, ~$0.79 / 1M output |
| Azure OpenAI GPT-4o | ~$2.50 / 1M input tokens, ~$10.00 / 1M output |
| Azure OpenAI text-embedding-3-large | ~$0.13 / 1M tokens |
| Pinecone serverless | usage-based reads/writes; no fixed monthly tier |
| Azure AI Search, Basic tier | ~$75 / month, fixed |

### Worked cost per 100 questions

| | Current: Groq + Pinecone | Azure: GPT-4o + AI Search |
|---|---|---|
| Generation (100 x 1,800 in + 150 out) | ~$0.12 | ~$0.60 |
| Embeddings (100 queries) | under $0.01 | under $0.01 |
| Vector store | usage-based, cents | ~$75 / month fixed |
| **Total per 100 questions** | **~$0.12 + usage** | **~$0.60 + $75 / month** |

The generation swap alone makes each question about 5x more
expensive in tokens — but both are under a dollar per 100
questions, so at this volume the LLM is not the decision. The
decision is the fixed $75/month search tier: it only makes sense
once the question volume, or the need for a managed service with
an SLA and Azure data residency, justifies a standing monthly
cost. At low volume Pinecone serverless + Groq is far cheaper;
the Azure path buys operational simplicity, not savings.

### The calculator — save as `eval/cost.py`

```python
# Rates are indicative list prices (Nov 2026) — update from the
# provider pricing pages before budgeting.
RATES = {
    "groq_llama3_70b": {"input": 0.59, "output": 0.79},   # $ per 1M tokens
    "azure_gpt4o": {"input": 2.50, "output": 10.00},
    "azure_embedding_3_large": 0.13,
}
AZURE_SEARCH_BASIC_MONTHLY = 75.0

def cost_per_100_questions(model: str, input_tokens: int = 1800,
                           output_tokens: int = 150) -> float:
    r = RATES[model]
    per_question = (input_tokens * r["input"]
                    + output_tokens * r["output"]) / 1_000_000
    return round(per_question * 100, 4)

if __name__ == "__main__":
    for model in ("groq_llama3_70b", "azure_gpt4o"):
        print(model, "$", cost_per_100_questions(model), "per 100 questions")
    print("Azure AI Search Basic: $", AZURE_SEARCH_BASIC_MONTHLY, "/ month fixed")
```

### When the managed Azure path is worth it

- **Volume:** thousands of questions a month, so the fixed tier
  amortises and the ops time saved exceeds $75.
- **One vendor:** the whole stack (identity, storage, search,
  models) under Azure AD with one audit trail.
- **Data residency / compliance:** documents must stay in a region
  or boundary Azure guarantees and Pinecone/Groq do not.
- **Not worth it for:** saving money. If cost is the driver, stay
  on the usage-based stack and re-check the rates each quarter.

### What this sets up

The Day 3 swap (generation to Azure OpenAI) is now a measured
trade-off, not a guess: ~5x the token cost per question, plus a
fixed search tier, in exchange for a managed stack. The swap ships
only if the golden set scores from Parts 2 and 3 hold — a cheaper
answer that is less faithful is not a saving.
