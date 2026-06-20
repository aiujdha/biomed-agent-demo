from typing import Literal

from pydantic import BaseModel, Field


TrialPhase = Literal["Phase I", "Phase Ib", "Phase II", "Phase III", "Phase IV", "Unknown"]


class ClinicalTrialExtraction(BaseModel):
    trial_id: str
    phase: TrialPhase
    indication: str
    intervention: str
    primary_endpoint: str
    secondary_endpoints: list[str] = Field(default_factory=list)
    sample_size: int | None = Field(default=None, ge=1)
    inclusion_criteria: list[str] = Field(default_factory=list)
    exclusion_criteria: list[str] = Field(default_factory=list)