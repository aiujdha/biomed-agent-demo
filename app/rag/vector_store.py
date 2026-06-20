from pydantic import BaseModel
import faiss
import numpy as np

from app.ingestion.chunking import DocumentChunk


class SearchResult(BaseModel):
    chunk: DocumentChunk
    score: float


class FaissVectorStore:
    def __init__(self, dimension: int = 384) -> None:
        self.dimension = dimension
        self.index = faiss.IndexFlatIP(dimension)
        self.chunks: list[DocumentChunk] = []

    @property
    def count(self) -> int:
        return len(self.chunks)

    def clear(self) -> None:
        self.index = faiss.IndexFlatIP(self.dimension)
        self.chunks = []

    def add(self, chunks: list[DocumentChunk], vectors: list[list[float]]) -> None:
        if len(chunks) != len(vectors):
            raise ValueError("chunks and vectors length mismatch")
        if not chunks:
            return
        matrix = np.array(vectors, dtype="float32")
        self.index.add(matrix)
        self.chunks.extend(chunks)

    def search(self, query_vector: list[float], top_k: int) -> list[SearchResult]:
        if self.index.ntotal == 0:
            return []
        query = np.array([query_vector], dtype="float32")
        scores, indexes = self.index.search(query, top_k)
        results: list[SearchResult] = []
        for score, index in zip(scores[0], indexes[0], strict=False):
            if index < 0:
                continue
            results.append(SearchResult(chunk=self.chunks[index], score=float(score)))
        return results
