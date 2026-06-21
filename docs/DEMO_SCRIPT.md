# Demo Script — BioMed Knowledge API

This script walks through all major API endpoints in sequence. It is designed for:
- **Live coding / screencast** — copy-paste friendly, with expected output for each step
- **Technical walkthrough** — shows the full lifecycle from ingestion to report generation
- **Quick sanity check** — validate a running instance after deployment

## Prerequisites

```bash
# Terminal 1: start the server
uv sync
uv run uvicorn app.main:app --reload

# Terminal 2: run the demo
# The server must be running on localhost:8000
```

---

## Step 1 — Health Check

Verify the service is running.

```bash
curl http://localhost:8000/health
```

**Expected output:**

```json
{"status":"ok","service":"biomed-agent-demo"}
```

---

## Step 2 — Async Document Ingestion

Submit an ingestion job via the async endpoint. The server loads the three sample documents, chunks them, embeds them, and stores them in the FAISS index.

```bash
# Submit the job
curl -s -X POST http://localhost:8000/documents/ingest-jobs \
  -H "Content-Type: application/json" \
  -d '{"source":"samples"}'
```

**Expected output** (job_id will differ):

```json
{"job_id":"ingest_a1b2c3d4e5f6","status":"pending","source":"samples"}
```

```bash
# Poll until completion — replace job_id with the one above
JOB_ID="ingest_a1b2c3d4e5f6"
for i in $(seq 1 10); do
  RESP=$(curl -s "http://localhost:8000/documents/ingest-jobs/$JOB_ID")
  STATUS=$(echo "$RESP" | python3 -c "import sys,json; print(json.load(sys.stdin)['status'])")
  echo "Attempt $i: status=$STATUS"
  if [ "$STATUS" = "succeeded" ] || [ "$STATUS" = "failed" ]; then
    echo "$RESP" | python3 -m json.tool
    break
  fi
  sleep 0.3
done
```

**Expected output snippet:**

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

> **Note:** The sync endpoint (`POST /documents/ingest`) produces the same result synchronously. The async variant demonstrates the job-based workflow.

---

## Step 3 — RAG Query with Citations

Ask a question grounded in the ingested documents. The response includes the generated answer, retrieved source chunks with similarity scores, and citation metadata.

```bash
curl -s -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question":"What is the primary endpoint of the ADC trial?","top_k":3}' | python3 -m json.tool
```

**Key fields in the response:**

```json
{
  "answer": "[citation:trial_adc_001.md#2] ...",
  "sources": [
    {
      "document_id": "trial_adc_001",
      "source": "trial_adc_001.md",
      "chunk_index": 2,
      "score": 0.1396,
      "citation_id": "trial_adc_001.md#2",
      "excerpt": "Primary Endpoint: Objective response rate ...",
      "metadata": {
        "document_id": "trial_adc_001",
        "source": "trial_adc_001.md",
        "chunk_index": 2
      }
    }
  ]
}
```

**Explain these concepts during a demo:**
- `citation_id` = `{source}#{chunk_index}` — unique citation key for traceability
- `excerpt` = first 240 characters of the chunk text
- `score` = cosine similarity via FAISS inner product
- The answer references citations inline with `[citation:...]` markers

Try another query:

```bash
curl -s -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question":"How to thaw cryopreserved cells?","top_k":2}' | python3 -m json.tool
```

---

## Step 4 — Structured Trial Extraction

Extract structured clinical trial metadata from a known document.

```bash
curl -s -X POST http://localhost:8000/extract/trial \
  -H "Content-Type: application/json" \
  -d '{"document_id":"trial_adc_001"}' | python3 -m json.tool
```

**Expected output:**

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

Also demonstrate extraction from raw text (no document lookup):

```bash
curl -s -X POST http://localhost:8000/extract/trial \
  -H "Content-Type: application/json" \
  -d '{"text":"A Phase III trial of Drug-X in metastatic breast cancer with primary endpoint overall survival, target 400 patients."}' | python3 -m json.tool
```

**Expected output:**

```json
{
  "result": {
    "trial_id": null,
    "phase": "Phase III",
    "indication": "Metastatic breast cancer",
    "intervention": "Drug-X",
    "primary_endpoint": "Overall survival",
    "secondary_endpoints": [],
    "sample_size": 400,
    "inclusion_criteria": [],
    "exclusion_criteria": []
  },
  "validation_status": "valid"
}
```

---

## Step 5 — Agent Report Workflow

Trigger the multi-step LangGraph pipeline. The agent retrieves documents, extracts trial fields, and produces a synthesized report.

```bash
curl -s -X POST http://localhost:8000/agent/report \
  -H "Content-Type: application/json" \
  -d '{"topic":"ADC clinical trial"}' | python3 -m json.tool
```

**Expected output:**

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

**Explain:**
- The workflow is a LangGraph `StateGraph` with 4 sequential nodes
- Each step records its own `name`, `status`, and `summary`
- If no trial content is found, the `extract_trial_fields` step is `skipped` (graceful degradation)

---

## Step 6 — RAG Evaluation

Run the offline evaluation suite. This is the same process used in CI to gate releases.

```bash
uv run python evals/run_rag_eval.py
```

**Expected output (exit 0):**

```
============================================================
RAG Evaluation — 4 cases, 0 failure(s)
============================================================
  [PASS] trial_primary_endpoint: What is the primary endpoint of the ADC trial?
  [PASS] cell_culture_passaging: What should be checked before passaging cells?
  [PASS] cell_culture_thawing: How to thaw cryopreserved cells?
  [PASS] adc_approval: Which ADC was first approved for solid tumors?
```

---

## Full Automation

See [`scripts/demo_smoke.sh`](../scripts/demo_smoke.sh) for a one-click script that runs the complete demo flow and exits with a summary.

---

## Edge Cases to Highlight

| Scenario | Endpoint | Expected Behavior |
|----------|----------|------------------|
| Query without ingest | `POST /query` | Empty `sources`, answer states insufficient data |
| Missing document | `POST /extract/trial` | `404` with `error: "not_found"` |
| Missing job ID | `GET /documents/ingest-jobs/{bad_id}` | `404` with `error: "not_found"` |
| Non-trial topic | `POST /agent/report` | `extract_trial_fields` step marked `skipped` |
| Empty question | `POST /query` | `422` validation error (FastAPI built-in) |
