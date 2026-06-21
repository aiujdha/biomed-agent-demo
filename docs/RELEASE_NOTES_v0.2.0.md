# Release Notes — v0.2.0

## Summary

v0.2.0 extends **BioMed Knowledge API** from a basic local RAG service into a more complete backend demo for biomedical knowledge workflows. It adds pluggable LLM providers, LangGraph-based report orchestration, citation metadata, offline RAG evaluation, async ingestion jobs, and public demo packaging.

The default setup remains local-first: FakeLLM + HashEmbedding + in-memory FAISS. No external API key is required for tests, demos, or CI smoke checks.

---

## Capabilities

- **Document ingestion** — Load bundled biomedical sample documents into an in-memory FAISS vector index. Supports both synchronous (`POST /documents/ingest`) and async (`POST /documents/ingest-jobs`) ingestion.
- **Retrieval-augmented Q&A** — Return grounded answers with source chunks, scores, `citation_id`, excerpts, and metadata.
- **Structured trial extraction** — Extract clinical trial fields from a known document or raw text and validate them with Pydantic.
- **LangGraph report workflow** — Run a compiled StateGraph that retrieves evidence, extracts trial fields, summarizes findings, and returns inspectable step records.
- **Pluggable LLM providers** — Use the built-in FakeLLM for offline runs or an OpenAI-compatible text chat endpoint for real model calls.
- **RAG evaluation suite** — Run 4 offline retrieval cases that check expected source matching and key term coverage.
- **Demo automation** — Use `scripts/demo_smoke.sh` for a curl-based end-to-end walkthrough.

---

## Verification

All tests pass against the built-in FakeLLM and HashEmbedding, requiring no API keys or network access:

| Area | Test Count | Coverage |
|------|-----------:|----------|
| API smoke | 13 | Health, ingestion, query, extraction, agent, error responses |
| Chunking | 5 | Metadata, overlap, edge cases, validation |
| Health | 1 | Service identity and status |
| Async ingest jobs | 6 | Job creation, polling, lifecycle, failure path, query integration |
| LLM providers | 13 | Fake default, OpenAI-compatible requests, errors, redaction, invalid payloads |
| Loaders | 3 | Sample loading, markdown loading, missing file |
| RAG citations | 7 | citation_id format, excerpt truncation, metadata, backward compatibility |
| RAG evaluation | 4 | Eval script, case file, subprocess pass, expected case IDs |
| Report workflow | 5 | LangGraph execution, failure handling, step sequencing, skipped extraction |
| Trial schema | 3 | Valid payload, invalid phase, invalid sample size |

**Total: 60 automated tests** — run with:

```bash
uv run pytest
```

RAG evaluation:

```bash
uv run python evals/run_rag_eval.py
```

Demo smoke check against a running server:

```bash
BASE_URL=http://localhost:8000 scripts/demo_smoke.sh
```

Docker build and container smoke test:

```bash
docker build -t biomed-agent-demo:v0.2.0 .
docker run -d -p 8000:8000 biomed-agent-demo:v0.2.0
```

---

## Quickstart

```bash
uv sync
uv run uvicorn app.main:app --reload
# Open http://localhost:8000/docs
```

For a full API walkthrough, see [`DEMO_SCRIPT.md`](DEMO_SCRIPT.md).

---

## Package

| Artifact | Reference |
|----------|-----------|
| Source | https://github.com/aiujdha/biomed-agent-demo |
| Docker | Local build: `biomed-agent-demo:v0.2.0` |
| Python | >= 3.11 |

---

## Limitations

- **Local vector store** — The in-memory FAISS index does not persist across restarts. For production, replace it with a remote vector database.
- **In-memory job store** — Async ingestion job metadata is process-memory only. Jobs are lost on restart and are not visible across uvicorn workers.
- **No authentication** — The API has no built-in auth. Deploy behind a reverse proxy or VPN in non-local environments.
- **Research prototyping only** — Not validated for clinical decision support. Must not be used for medical diagnosis or treatment decisions.
- **Synthetic sample data** — All bundled documents are fabricated. Replace with de-identified real data for meaningful evaluation.
- **Single-user** — No multi-tenancy or concurrent session isolation.

---

## Roadmap

See [`ROADMAP.md`](ROADMAP.md) for planned work covering production LLM integration, persistent job stores, external vector databases, PDF ingestion, authentication, and observability.

---

## License

MIT
