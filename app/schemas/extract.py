from pydantic import BaseModel, Field, model_validator

from app.extraction.schemas import ClinicalTrialExtraction


class TrialExtractRequest(BaseModel):
    document_id: str | None = None
    text: str | None = Field(default=None, min_length=20)

    @model_validator(mode="after")
    def require_document_id_or_text(self) -> "TrialExtractRequest":
        if not self.document_id and not self.text:
            raise ValueError("document_id or text is required")
        return self


class TrialExtractResponse(BaseModel):
    result: ClinicalTrialExtraction
    validation_status: str