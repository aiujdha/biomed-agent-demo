from pathlib import Path

from app.ingestion.chunking import DocumentChunk, chunk_text
from app.ingestion.loaders import load_sample_documents


def build_sample_chunks(samples_dir: Path) -> list[DocumentChunk]:
    documents = load_sample_documents(samples_dir)
    chunks: list[DocumentChunk] = []
    for document_id, text in documents.items():
        chunks.extend(
            chunk_text(
                text=text,
                source=f"{document_id}.md",
                document_id=document_id,
            )
        )
    return chunks