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

### What I will add next in this file

- 2026-11-21: `eval/golden.jsonl` (20 questions) and the scoring
  script for Recall@5.
- 2026-11-22: Azure AI Search index design — fields, filters
  (`tenant_id`, `doc_type`), and chunk metadata.
- Later: cost per 100 questions, Pinecone + Groq vs Azure, and
  when the managed Azure path is worth it.
