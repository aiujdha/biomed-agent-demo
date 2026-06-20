from pydantic import BaseModel, Field


class SourceChunk(BaseModel):
    document_id: str
    source: str
    chunk_index: int
    score: float | None = None
    text: str


class QueryRequest(BaseModel):
    question: str = Field(min_length=3)
    top_k: int = Field(default=3, ge=1, le=8)


class QueryResponse(BaseModel):
    answer: str
    sources: list[SourceChunk]
    disclaimer: str