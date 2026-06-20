from pathlib import Path

from fastapi import APIRouter, BackgroundTasks

from app.core.container import embedding_model, vector_store
from app.core.errors import NotFoundError
from app.schemas.documents import (
    IngestJobCreateResponse,
    IngestJobRequest,
    IngestJobStatusResponse,
    IngestRequest,
    IngestResponse,
)
from app.services.document_service import DocumentService
from app.services.ingest_job_service import IngestJobService

router = APIRouter(prefix="/documents", tags=["documents"])

# Module-level singleton — in-memory for the lifetime of the process.
_ingest_job_service = IngestJobService()


@router.post("/ingest", response_model=IngestResponse)
def ingest_documents(_: IngestRequest) -> IngestResponse:
    service = DocumentService(
        samples_dir=Path("samples"),
        vector_store=vector_store,
        embedding_model=embedding_model,
    )
    return service.ingest_samples()


@router.post("/ingest-jobs", response_model=IngestJobCreateResponse, status_code=201)
def create_ingest_job(
    request: IngestJobRequest,
    bg_tasks: BackgroundTasks,
) -> IngestJobCreateResponse:
    record = _ingest_job_service.create_job(request.source, bg_tasks)
    return IngestJobCreateResponse(
        job_id=record.job_id,
        status=record.status,
        source=record.source,
    )


@router.get("/ingest-jobs/{job_id}", response_model=IngestJobStatusResponse)
def get_ingest_job(job_id: str) -> IngestJobStatusResponse:
    record = _ingest_job_service.get_job(job_id)
    if record is None:
        raise NotFoundError(detail=f"Ingest job not found: {job_id}")
    return IngestJobStatusResponse(
        job_id=record.job_id,
        status=record.status,
        source=record.source,
        document_count=record.document_count,
        chunk_count=record.chunk_count,
        error=record.error,
    )