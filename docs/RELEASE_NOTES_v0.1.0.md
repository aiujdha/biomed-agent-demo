# Release Notes — v0.1.0

## Summary

Initial release of BioMed Knowledge API, a FastAPI-based service for biomedical document retrieval, RAG-based Q&A, structured clinical trial extraction, and multi-step agent report generation. Runs locally without external API keys using built-in hash-based embedding and a default fake LLM client.

## Quickstart

```bash
uv sync
uv run uvicorn app.main:app --reload
```

Open http://localhost:8000/docs for the Swagger UI.

## API Walkthrough

The following sequence walks through all core capabilities:

```bash
# 1. Health check
curl http://localhost:8000/health

# 2. Ingest sample documents
curl -X POST http://localhost:8000/documents/ingest \
  -H "Content-Type: application/json" \
  -d '{"source":"samples"}'

# 3. RAG query
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question":"What is the primary endpoint of the ADC trial?","top_k":3}'

# 4. Structured trial extraction (by document ID)
curl -X POST http://localhost:8000/extract/trial \
  -H "Content-Type: application/json" \
  -d '{"document_id":"trial_adc_001"}'

# 5. Structured trial extraction (by raw text)
curl -X POST http://localhost:8000/extract/trial \
  -H "Content-Type: application/json" \
  -d '{"text":"A Phase II trial of ADC-101 in HER2-positive advanced solid tumors with primary endpoint objective response rate."}'

# 6. Agent report workflow
curl -X POST http://localhost:8000/agent/report \
  -H "Content-Type: application/json" \
  -d '{"topic":"ADC clinical trial"}'
```

## Verification

Vetted through 25 automated tests covering:

| Area | Test Count | Coverage |
|------|-----------|----------|
| Ingest | 2 | Document loading, chunking, index rebuild |
| Query | 3 | With ingested data, empty index, edge cases |
| Extraction | 3 | By document ID, by raw text, missing document |
| Agent | 4 | Report generation, skipped steps, error handling |
| Smoke | 13 | Health, all endpoints, error responses, CORS, unknown routes |

All tests pass against the built-in FakeLLM and HashEmbedding, requiring no API keys or network access.

Docker build and container smoke test also validated:

```bash
docker build -t biomed-agent-demo:v0.1.0 .
docker run -d -p 8000:8000 biomed-agent-demo:v0.1.0
# All endpoints verified via curl in container
```

## Package

| Artifact | Reference |
|----------|-----------|
| Source repository | https://github.com/aiujdha/biomed-agent-demo |
| Docker image | Local build: `biomed-agent-demo:v0.1.0` |
| Python | >= 3.11 |

## Limitations

- **Local vector store** — The in-memory FAISS index does not persist across restarts. For production, replace with a remote vector database.
- **No authentication** — The API has no built-in auth. Deploy behind a reverse proxy or VPN in non-local environments.
- **Research prototyping only** — Not validated for clinical decision support. Must not be used for medical diagnosis or treatment decisions.
- **Synthetic sample data** — All bundled documents are fabricated. Replace with de-identified real data for meaningful evaluation.
- **Single-user** — No multi-tenancy or concurrent session isolation.

## Assets

- Source: https://github.com/aiujdha/biomed-agent-demo
- License: MIT
