"""In-memory async ingestion job service using FastAPI BackgroundTasks.

Notable limitations (by design):
- Jobs are process-memory only — lost on restart.
- Not visible across uvicorn workers.
- No cancellation or queue capacity control.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from pathlib import Path

from fastapi import BackgroundTasks

from app.core.container import embedding_model, vector_store
from app.schemas.documents import IngestJobStatus
from app.services.document_service import DocumentService


@dataclass
class IngestJobRecord:
    job_id: str
    status: IngestJobStatus
    source: str
    document_count: int = 0
    chunk_count: int = 0
    error: str | None = None


class IngestJobService:
    """Manages ingestion jobs in memory, executed via BackgroundTasks."""

    def __init__(self) -> None:
        self._jobs: dict[str, IngestJobRecord] = {}

    def create_job(self, source: str, bg_tasks: BackgroundTasks) -> IngestJobRecord:
        job_id = f"ingest_{uuid.uuid4().hex[:12]}"
        record = IngestJobRecord(job_id=job_id, status="pending", source=source)
        self._jobs[job_id] = record
        bg_tasks.add_task(self._run_job, job_id)
        return record

    def get_job(self, job_id: str) -> IngestJobRecord | None:
        return self._jobs.get(job_id)

    def _run_job(self, job_id: str) -> None:
        record = self._jobs[job_id]
        record.status = "running"
        try:
            service = DocumentService(
                samples_dir=Path("samples"),
                vector_store=vector_store,
                embedding_model=embedding_model,
            )
            result = service.ingest_samples()
            record.document_count = result.document_count
            record.chunk_count = result.chunk_count
            record.status = "succeeded"
        except Exception as exc:
            record.error = str(exc)
            record.status = "failed"
