from pydantic import BaseModel


class DocumentChunk(BaseModel):
    document_id: str
    source: str
    chunk_index: int
    text: str


def chunk_text(
    text: str,
    source: str,
    document_id: str,
    chunk_size: int = 800,
    chunk_overlap: int = 120,
) -> list[DocumentChunk]:
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    if chunk_overlap < 0 or chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap must be >= 0 and smaller than chunk_size")

    chunks: list[DocumentChunk] = []
    start = 0
    chunk_index = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(
                DocumentChunk(
                    document_id=document_id,
                    source=source,
                    chunk_index=chunk_index,
                    text=chunk,
                )
            )
            chunk_index += 1
        if end == len(text):
            break
        start = end - chunk_overlap
    return chunks