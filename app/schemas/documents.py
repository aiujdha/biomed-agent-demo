from typing import Literal

from pydantic import BaseModel, Field


class IngestRequest(BaseModel):
    source: str = Field(default="samples", pattern="^samples$")


class IngestResponse(BaseModel):
    document_count: int
    chunk_count: int
    vector_store_path: str


IngestJobStatus = Literal["pending", "running", "succeeded", "failed"]


class IngestJobRequest(BaseModel):
    source: str = Field(default="samples", pattern="^samples$")


class IngestJobCreateResponse(BaseModel):
    job_id: str
    status: IngestJobStatus
    source: str


class IngestJobStatusResponse(BaseModel):
    job_id: str
    status: IngestJobStatus
    source: str
    document_count: int | None = None
    chunk_count: int | None = None
    error: str | None = None