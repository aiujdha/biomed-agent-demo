from pathlib import Path

from app.ingestion.pipeline import build_sample_chunks
from app.rag.embeddings import HashEmbeddingModel
from app.rag.vector_store import FaissVectorStore
from app.schemas.documents import IngestResponse


class DocumentService:
    def __init__(
        self,
        samples_dir: Path,
        vector_store: FaissVectorStore,
        embedding_model: HashEmbeddingModel,
        vector_store_path: str = ".local/faiss",
    ) -> None:
        self.samples_dir = samples_dir
        self.vector_store = vector_store
        self.embedding_model = embedding_model
        self.vector_store_path = vector_store_path

    def ingest_samples(self) -> IngestResponse:
        chunks = build_sample_chunks(self.samples_dir)
        vectors = self.embedding_model.embed_documents([chunk.text for chunk in chunks])
        self.vector_store.clear()
        self.vector_store.add(chunks, vectors)
        document_count = len({chunk.document_id for chunk in chunks})
        return IngestResponse(
            document_count=document_count,
            chunk_count=len(chunks),
            vector_store_path=self.vector_store_path,
        )
