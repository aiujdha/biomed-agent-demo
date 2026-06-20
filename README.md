# BioMed Knowledge API

**A local-first FastAPI service for biomedical document retrieval, RAG-based Q&A, structured trial information extraction, and multi-step agent report workflows.**

Built with FastAPI, FAISS, and Pydantic. Runs without external dependencies or API keys in its default configuration — clone, install, and start querying in minutes.

---

## Features

- **Document Ingestion** — Load biomedical sample documents (SOPs, literature summaries, clinical trial briefs) into an in-memory FAISS vector index.
- **Retrieval-Augmented Q&A** — Retrieve relevant document chunks and generate sourced answers grounded in the ingested content.
- **Structured Trial Extraction** — Extract structured clinical trial fields (phase, indication, endpoints, sample size, criteria) validated against a Pydantic schema.
- **Agent Report Workflow** — Multi-step pipeline that chains retrieval, extraction, and summarization into an inspectable report with per-step status.
- **No-Key Default** — Built-in hash-based embedding and a fake LLM client allow the full pipeline to run without any API keys. Swap in an OpenAI-compatible LLM when needed.

---

## Quickstart

```bash
uv sync
uv run uvicorn app.main:app --reload
```

Open http://localhost:8000/docs for the Swagger UI.

Run tests:

```bash
uv run pytest
```

Run with Docker (optional):

```bash
docker compose up --build
```

The API is available at http://localhost:8000. The `uv` workflow is the fastest path while iterating.

---

## API Reference

### Health

```bash
curl http://localhost:8000/health
```

```json
{"status":"ok","service":"biomed-agent-demo"}
```

### Ingest Documents

Load the bundled sample documents into the in-memory FAISS index. Repeated calls rebuild the index rather than appending duplicate chunks.

```bash
curl -X POST http://localhost:8000/documents/ingest \
  -H "Content-Type: application/json" \
  -d '{"source":"samples"}'
```

```json
{"document_count":3,"chunk_count":12,"vector_store_path":".local/faiss"}
```

### Query

Ask a question against the ingested document index. Responses include retrieved source chunks with similarity scores.

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question":"What is the primary endpoint of the ADC trial?","top_k":3}'
```

```json
{
  "answer": "...",
  "sources": [
    {
      "document_id": "trial_adc_001",
      "source": "trial_adc_001.md",
      "chunk_index": 2,
      "score": 0.1396,
      "text": "..."
    }
  ],
  "disclaimer": "This project is intended for development and research workflow prototyping. It does not provide medical advice."
}
```

If no documents have been ingested, the endpoint returns an empty `sources` list and states that the answer cannot be determined from available documents.

### Extract Trial Fields

Extract structured clinical trial metadata from a sample document or raw text.

```bash
curl -X POST http://localhost:8000/extract/trial \
  -H "Content-Type: application/json" \
  -d '{"document_id":"trial_adc_001"}'
```

Pass text directly instead of a document ID:

```bash
curl -X POST http://localhost:8000/extract/trial \
  -H "Content-Type: application/json" \
  -d '{"text":"A Phase II trial of ADC-101 in HER2-positive advanced solid tumors with primary endpoint objective response rate."}'
```

```json
{
  "result": {
    "trial_id": "trial_adc_001",
    "phase": "Phase II",
    "indication": "HER2-positive solid tumors",
    "intervention": "ADC-101",
    "primary_endpoint": "Objective response rate",
    "secondary_endpoints": ["Progression-free survival", "Safety"],
    "sample_size": 120,
    "inclusion_criteria": ["Adult patients", "ECOG performance status 0-1"],
    "exclusion_criteria": ["Uncontrolled infection"]
  },
  "validation_status": "valid"
}
```

Returns `404` for missing documents. All errors follow a shared response shape:

```json
{
  "error": "not_found",
  "message": "Document not found: samples/missing_trial.md",
  "request_id": null
}
```

### Agent Report

Generate a source-grounded report with an inspectable multi-step workflow. Each step records its name, status, and summary.

```bash
curl -X POST http://localhost:8000/agent/report \
  -H "Content-Type: application/json" \
  -d '{"topic":"ADC clinical trial"}'
```

```json
{
  "report": "Summary for ADC clinical trial. ... Extracted trial design: phase Phase II; primary endpoint: Objective response rate; sample size: 120.",
  "steps": [
    {"name": "retrieve_documents", "status": "success", "summary": "Retrieved 3 source chunks."},
    {"name": "extract_trial_fields", "status": "success", "summary": "Extracted structured trial fields from trial_adc_001: Phase II, primary endpoint Objective response rate."},
    {"name": "summarize_findings", "status": "success", "summary": "Generated a source-grounded report summary."},
    {"name": "return_response", "status": "success", "summary": "Returned report, steps, and source references."}
  ],
  "sources": ["trial_adc_001.md#0", "pubmed_adc_summary.md#1"]
}
```

If no sources are available or the retrieved content does not contain clinical trial data, the `extract_trial_fields` step is marked as `skipped`.

---

## Architecture

```
app/
├── api/routes/         # HTTP endpoints (health, documents, query, extract, agent)
├── core/               # Configuration, dependency container, error handling
├── ingestion/          # File loading and text chunking
├── rag/               # Embedding, FAISS vector store, retrieval, prompts
├── extraction/         # Pydantic schemas and structured field extraction
├── llm/               # LLM client (fake default; OpenAI-compatible)
├── agent/             # Tool functions and report workflow
├── services/          # Business logic orchestration
└── schemas/           # Request/response models
```

The service layer sits between the HTTP routes and the domain modules. Each module has a single responsibility and can be replaced independently — for example, the FAISS vector store can be swapped for a remote vector database without touching the API routes.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| API | FastAPI, Uvicorn |
| Validation | Pydantic v2 |
| Vector Store | FAISS (in-memory) |
| Embedding | HashEmbedding (default, no key required) / OpenAI-compatible |
| LLM | FakeLLM (default) / OpenAI-compatible |
| Tests | pytest, FastAPI TestClient |
| Packaging | uv |
| Container | Docker |

---

## Sample Data

The repository includes three synthetic biomedical documents for demonstration:

| File | Type | Content |
|------|------|---------|
| `samples/sop_cell_culture.md` | Standard Operating Procedure | Cell culture thawing, passaging, cryopreservation |
| `samples/pubmed_adc_summary.md` | Literature Review | ADC oncology review with clinical trial results |
| `samples/trial_adc_001.md` | Clinical Trial Summary | Phase II ADC-101 trial design and endpoints |

These are fabricated samples and do not contain real patient data or proprietary information.

---

## Limitations

- **Local vector store** — The in-memory FAISS index is not persisted across restarts and does not support multi-tenancy or distributed querying. Production deployments should use a remote vector database.
- **No authentication** — The API has no built-in auth layer. It should be deployed behind a reverse proxy or VPN in any non-local environment.
- **Research prototyping only** — The system is designed for development workflow prototyping and software evaluation. It is not validated for clinical decision support and must not be used for medical diagnosis or treatment decisions.
- **Synthetic sample data** — All bundled documents are fabricated. Replace with real (de-identified) data for any meaningful evaluation.

---

## Project Status

v0.1.0 — Core retrieval, extraction, and agent workflows are functional over built-in sample documents.