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

Run with Docker:

```bash
docker compose up --build
```

The API will be available at http://localhost:8000. Docker is optional for local development; the default `uv` workflow above is the fastest path while iterating.

## Health Check

```bash
curl http://localhost:8000/health
```

Expected response:

```json
{"status":"ok","service":"biomed-agent-demo"}
```

## Ingest Sample Documents

Load the bundled biomedical sample documents into the in-memory FAISS index:

```bash
curl -X POST http://localhost:8000/documents/ingest \
  -H "Content-Type: application/json" \
  -d '{"source":"samples"}'
```

Expected response:

```json
{"document_count":3,"chunk_count":12,"vector_store_path":".local/faiss"}
```

Repeated ingest requests rebuild the in-memory sample index instead of appending duplicate chunks.

## Query Documents

Ask a question against the ingested sample index:

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question":"What is the primary endpoint of the ADC trial?","top_k":3}'
```

Expected response fields:

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
  "disclaimer": "This demo is for software engineering evaluation only and does not provide medical advice."
}
```

If no documents have been ingested, `/query` returns an empty `sources` list and states that the answer cannot be determined from available documents.

## Extract Trial Metadata

Extract structured clinical trial fields from a sample document:

```bash
curl -X POST http://localhost:8000/extract/trial \
  -H "Content-Type: application/json" \
  -d '{"document_id":"trial_adc_001"}'
```

You can also pass raw text:

```bash
curl -X POST http://localhost:8000/extract/trial \
  -H "Content-Type: application/json" \
  -d '{"text":"A Phase II trial of ADC-101 in HER2-positive advanced solid tumors with primary endpoint objective response rate."}'
```

Expected response fields:

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

Missing sample documents return `404`.

Error responses use a shared shape:

```json
{
  "error": "not_found",
  "message": "Document not found: samples/missing_trial.md",
  "request_id": null
}
```

## Agent Report Workflow

Generate a short, source-grounded report with inspectable workflow steps:

```bash
curl -X POST http://localhost:8000/agent/report \
  -H "Content-Type: application/json" \
  -d '{"topic":"ADC clinical trial"}'
```

Expected response fields:

```json
{
  "report": "Summary for ADC clinical trial. ... Extracted trial design: phase Phase II; primary endpoint: Objective response rate; sample size: 120.",
  "steps": [
    {"name": "retrieve_documents", "status": "success", "summary": "..."},
    {"name": "extract_trial_fields", "status": "success", "summary": "..."},
    {"name": "summarize_findings", "status": "success", "summary": "..."},
    {"name": "return_response", "status": "success", "summary": "..."}
  ],
  "sources": ["trial_adc_001.md#0", "pubmed_adc_summary.md#1"]
}
```

Run `/documents/ingest` first to populate the in-memory sample index. If no sources are available, or the retrieved sources are not clinical trial documents, the workflow still returns all steps and marks `extract_trial_fields` as `skipped`.

The current version uses an explicit Python workflow for observability and local reliability. A later version can replace this with LangGraph while keeping the same API contract.

## Project Status

MVP1-ready — local RAG query, structured trial extraction, explicit agent report workflow, shared error responses, and Docker packaging over sample documents.
