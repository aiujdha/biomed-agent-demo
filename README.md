# BioMed Knowledge API

**A local-first FastAPI service for biomedical document retrieval, RAG-based Q&A, structured clinical trial extraction, and multi-step agent report workflows.**

Built with FastAPI, FAISS, LangGraph, and Pydantic. Runs without external API keys in its default configuration, using a built-in hash-based embedding model and a fake LLM client for offline development and CI.

---

## Features

- **Document Ingestion** — Load biomedical sample documents (SOPs, literature summaries, clinical trial briefs) into an in-memory FAISS vector index. Synchronous and async (BackgroundTasks) ingestion endpoints.
- **Retrieval-Augmented Q&A** — Retrieve relevant document chunks with similarity scores and citation metadata. Generate grounded answers using the configured LLM provider.
- **Structured Trial Extraction** — Extract structured clinical trial fields (phase, indication, endpoints, sample size, criteria) from document content or raw text, validated against a Pydantic schema.
- **Agent Report Workflow** — Multi-step pipeline built with LangGraph StateGraph that chains retrieval, extraction, and summarization into an inspectable report with per-step status and source references.
- **Pluggable LLM Providers** — Built-in fake LLM (zero-config default for CI/offline) and an OpenAI-compatible text chat client supporting any provider with a `/chat/completions` endpoint (DeepSeek, Qwen, Ollama, vLLM, etc.).
- **RAG Evaluation Suite** — Standalone evaluation runner with predefined cases covering document-level source matching and key term coverage. Exit-code-gated for CI pipelines.

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

Run with Docker:

```bash
docker compose up --build
```

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

### Async Ingest Job

Submit an ingestion request that runs in the background via FastAPI BackgroundTasks. The job ID is returned immediately and can be polled for status.

```bash
curl -X POST http://localhost:8000/documents/ingest-jobs \
  -H "Content-Type: application/json" \
  -d '{"source":"samples"}'
```

```json
{"job_id":"ingest_a1b2c3d4e5f6","status":"pending","source":"samples"}
```

Poll the job status:

```bash
curl http://localhost:8000/documents/ingest-jobs/ingest_a1b2c3d4e5f6
```

```json
{
  "job_id": "ingest_a1b2c3d4e5f6",
  "status": "succeeded",
  "source": "samples",
  "document_count": 3,
  "chunk_count": 12,
  "error": null
}
```

The job transitions through `pending` → `running` → `succeeded` (or `failed`). A missing job ID returns `404`.

> **Note:** The job store is in-memory only — jobs are lost on restart and not visible across uvicorn workers. This is suitable for development and single-worker deployments.

### Query

Ask a question against the ingested document index. Responses include retrieved source chunks with similarity scores and citation metadata.

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
      "text": "...",
      "citation_id": "trial_adc_001.md#2",
      "excerpt": "Primary Endpoint: Objective response rate ...",
      "metadata": {
        "citation_id": "trial_adc_001.md#2",
        "document_id": "trial_adc_001",
        "source": "trial_adc_001.md",
        "chunk_index": 2,
        "score": 0.1396
      }
    }
  ],
  "disclaimer": "This project is intended for research and development prototyping. It does not provide medical advice."
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

## Configuration

The default configuration is local-only and does not require API keys:

```env
LLM_PROVIDER=fake
```

To use a text-only OpenAI-compatible chat completion endpoint:

```env
LLM_PROVIDER=openai-compatible
LLM_API_KEY=your-provider-key
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-4o-mini
```

`LLM_BASE_URL` may point to any provider that exposes an OpenAI-compatible `/chat/completions` API (DeepSeek, Qwen, SiliconFlow, OpenRouter, Ollama, local vLLM). The current scope does not include multimodal input, image understanding, OCR, streaming, or tool-calling support.

---

## Architecture

```
app/
├── api/routes/         # HTTP endpoints (health, documents, query, extract, agent)
├── core/               # Configuration (pydantic-settings), dependency container, error handling
├── ingestion/          # File loading and text chunking
├── rag/               # Embedding, FAISS vector store, retrieval, prompt templates
├── extraction/         # Pydantic validation schemas and structured field extraction
├── llm/               # LLM client protocol, fake default, OpenAI-compatible text client
├── agent/             # LangGraph-compiled StateGraph workflow, state definition, tool functions
├── services/          # Business logic orchestration (document, query, extraction, ingest jobs)
└── schemas/           # Request/response Pydantic models
```

The service layer decouples HTTP routes from domain logic. Each module has a single responsibility and can be replaced independently — for example, the FAISS vector store can be swapped for a remote vector database without modifying the API routes.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| API framework | FastAPI, Uvicorn |
| Validation | Pydantic v2 |
| Vector store | FAISS (in-memory, IndexFlatIP) |
| Embedding | HashEmbedding (deterministic, no external service) |
| LLM | FakeLLM (default) / OpenAI-compatible text chat |
| Workflow orchestration | LangGraph (StateGraph) |
| Testing | pytest, FastAPI TestClient |
| Packaging | uv |
| Container | Docker, Docker Compose |

---

## Evaluation

Run the lightweight RAG evaluation suite to verify source retrieval and term coverage on the bundled sample documents:

```bash
uv run python evals/run_rag_eval.py
```

The evaluator loads the three sample documents, runs each predefined question through `QueryService`, and checks:

- The top retrieved source matches the expected document.
- Key terms appear in the answer or source text.

All cases must pass (exit 0) before a release. The evaluator uses the built-in `FakeLLMClient` and `HashEmbeddingModel` — no external API keys are required.

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

## Demo Script

See [`docs/DEMO_SCRIPT.md`](docs/DEMO_SCRIPT.md) for a complete walkthrough covering all API endpoints.

---

## Roadmap

See [`docs/ROADMAP.md`](docs/ROADMAP.md) for the post-v0.2.0 roadmap and feature backlog.

---

## Release Notes

See [`docs/RELEASE_NOTES_v0.2.0.md`](docs/RELEASE_NOTES_v0.2.0.md) for the current release candidate. Historical notes are available in [`docs/RELEASE_NOTES_v0.1.0.md`](docs/RELEASE_NOTES_v0.1.0.md).

---

## Limitations

- **Local vector store** — The in-memory FAISS index is not persisted across restarts and does not support multi-tenancy or distributed querying. Production deployments should use a remote vector database.
- **In-memory job store** — The async ingestion job store is process-memory only. Jobs are lost on restart, are not visible across uvicorn workers, and do not support cancellation or queue capacity control.
- **No authentication** — The API has no built-in auth layer. It should be deployed behind a reverse proxy or VPN in any non-local environment.
- **Research prototyping only** — The system is designed for research and development workflow prototyping. It is not validated for clinical decision support and must not be used for medical diagnosis or treatment decisions.
- **Synthetic sample data** — All bundled documents are fabricated. Replace with real (de-identified) data for any meaningful evaluation.

---

## License

MIT
