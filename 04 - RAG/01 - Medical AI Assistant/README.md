# Medical AI System Architecture Summary

## 1. System Components & Workflow

### Core System: Medical AI System  

Acts as the central hub integrating all modules.  

### 1.1 Data Ingestion & Preprocessing  

- **PDF Upload**  
  - Uses a PDF Loader for raw text extraction from uploaded PDFs.  
- **Text Chunking**  
  - Employs `RecursiveCharacterTextSplitter` to split text into manageable chunks while maintaining context.  

### 1.2 Embedding & Vectorization  

- **Embedding**  
  - Leverages Google Embedding Model or HuggingFace for converting text chunks into embeddings.  
- **Vector Store**  
  - Stores embeddings in Pinecone Vector Database for efficient similarity-based retrieval.  

### 1.3 Query Handling  

- **Query Processing**  
  - Performs query embedding and similarity search against the vector store to fetch relevant context.  

### 1.4 Response Generation  

- **RAG Chain**  
  - Combines retrieved context with LLM (LLaMA 3 via Groq) using LangChain, guided by a custom system prompt.  
- **Answer Generation**  
  - Produces grounded, human-readable responses using the augmented context.  

### 1.5 Backend & Endpoints (FastAPI Backend)  

- Exposes two key endpoints:  
  - `/upload_pdfs`: For PDF ingestion.  
  - `/ask`: To submit queries and get AI-generated responses.  

## 2. Core Tech Stack  

| Layer          | Tool/Framework                          |  
|----------------|-----------------------------------------|  
| LLM            | Groq (LLaMA 3 70B)                      |  
| Embeddings     | Google Generative AI or HuggingFace (HF) |  
| Vector Store   | Pinecone                                |  
| RAG Chain      | LangChain                               |  
| Backend API    | FastAPI                                 |  
| Deployment     | Render                                  |  

## 3. Key Processes  

1. **PDF → Text → Chunks**: Ingest medical documents, extract text, and split into context-aware chunks.  
2. **Embedding + Vector Storage**: Convert chunks to embeddings, store in Pinecone for fast retrieval.  
3. **Query → Context → Response**: Embed user queries, find matching context in the vector store, and use LLM (via RAG) to generate informed answers.  

This architecture combines RAG (Retrieval-Augmented Generation) with scalable tools to build a medical AI system that delivers accurate, document-grounded responses.

## 4. Project Setup commands

```bash
uv init .

uv venv

source .venv/Scripts/activate

cd server
uv pip install -r requirements.txt

```
