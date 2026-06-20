from pydantic import BaseModel, Field


class IngestRequest(BaseModel):
    source: str = Field(default="samples", pattern="^samples$")


class IngestResponse(BaseModel):
    document_count: int
    chunk_count: int
    vector_store_path: str