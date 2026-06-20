# BioMed Agent Demo

Biomedical RAG and Agent workflow demo — a FastAPI backend for biomedical document Q&A and structured information extraction.

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

## Health Check

```bash
curl http://localhost:8000/health
```

Expected response:

```json
{"status":"ok","service":"biomed-agent-demo"}
```

## Project Status

PR1 scaffold — FastAPI app, settings, health endpoint, and health check test.
