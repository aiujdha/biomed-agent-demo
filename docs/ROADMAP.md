# Roadmap — BioMed Knowledge API

> Current release candidate: **v0.2.0** (see [RELEASE_NOTES_v0.2.0.md](RELEASE_NOTES_v0.2.0.md))

This document outlines planned development after v0.2.0. Items are ordered by priority and grouped by theme.

---

## v0.3.0 — Production Foundation

### Real LLM Integration

- **Multi-provider support with structured output:** Add support for tool-use / function-calling LLM providers (OpenAI, Anthropic, etc.) for structured trial extraction and deterministic report generation.
- **Provider health checks:** Endpoint-level health check for the configured LLM provider, with graceful fallback to FakeLLM.
- **Request-level provider override:** Allow per-request `llm_provider` / `llm_model` overrides in query and extraction endpoints.

### Persistent Job Store

- **Replace in-memory dict with SQLite or Redis:** Persistent job metadata across restarts, with TTL-based cleanup for completed/failed jobs.
- **Job cancellation:** `DELETE /documents/ingest-jobs/{job_id}` to cancel a running job.
- **Job queue with capacity control:** Configurable concurrency limit and queue depth to prevent resource exhaustion.

### Production Vector Store

- **Replace in-memory FAISS with a vector database:** Options include Qdrant (self-hosted), pgvector (PostgreSQL), or Milvus.
- **Document-level CRUD:** `PUT /documents/{id}`, `DELETE /documents/{id}` with vector index synchronization.
- **Collection/namespace isolation:** Multi-tenant separation of vector indexes via collection names.

### PDF Ingestion

- **PDF parsing pipeline:** Extract text from PDF documents (pypdf or pdfplumber), with fallback to OCR for scanned documents.
- **PDF-specific chunking:** Section-aware chunking based on heading detection, with figure/table caption extraction.
- **Metadata extraction:** Author, date, journal, PMID/DOI from PDF metadata fields.

### Authentication & Audit

- **API key authentication:** Static API key validation via header, with key rotation support.
- **Request audit log:** Structured log of all ingestion, query, and extraction events with timestamp, client ID, and payload digest.
- **Rate limiting:** Per-client rate limiting for query and report endpoints.

---

## v0.4.0 — Advanced Features

### Multi-Modal Support

- **Image understanding in PDFs:** Extract and caption figures, charts, and tables from biomedical PDFs.
- **Multi-modal LLM queries:** Pass extracted images to vision-capable LLMs for figure interpretation.

### Hybrid Search

- **BM25 + vector hybrid retrieval:** Combine keyword matching (BM25) with dense retrieval for improved recall on biomedical terminology.
- **Re-ranking:** Cross-encoder re-ranking of top-k results for precision improvement.
- **Query expansion:** Automatic expansion of biomedical acronyms and abbreviations at query time.

### Streaming & Real-Time

- **Streaming query responses:** SSE-based streaming for the query and report endpoints.
- **WebSocket agent reports:** Real-time step status updates during agent workflow execution.

---

## v0.5.0 — Deployment & Scale

- **Helm chart for Kubernetes:** Production-grade deployment configuration.
- **Prometheus metrics:** Request latency, error rate, vector store size, queue depth.
- **Horizontal scaling:** Stateless API layer with shared vector database and job backend.
- **Grafana dashboard:** Pre-built dashboard for monitoring system health and usage patterns.

---

## Non-Goals (Explicitly Out of Scope)

- Clinical decision support or medical device certification
- HIPAA compliance or PHI handling
- Multi-modal model training or fine-tuning
- Real-time inference serving (< 100ms latency targets)
- Natural language batch querying or report scheduling

---

## Contribution Ideas

The following are well-scoped, independently implementable features suitable for external contributors:

1. **PDF ingestion** — Add a PDF document loader in `app/ingestion/loaders.py`
2. **Qdrant vector store** — Implement `VectorStore` interface backed by Qdrant client
3. **API key auth** — Add a middleware in `app/core/auth.py`
4. **Job cancellation** — Add `DELETE` endpoint and cancellation signal to `IngestJobService`
5. **Swagger examples** — Add `OpenAPI` example values to all request/response models
