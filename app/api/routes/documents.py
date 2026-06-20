from pathlib import Path

from fastapi import APIRouter

from app.core.container import embedding_model, vector_store
from app.schemas.documents import IngestRequest, IngestResponse
from app.services.document_service import DocumentService

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/ingest", response_model=IngestResponse)
def ingest_documents(_: IngestRequest) -> IngestResponse:
    service = DocumentService(
        samples_dir=Path("samples"),
        vector_store=vector_store,
        embedding_model=embedding_model,
    )
    return service.ingest_samples()