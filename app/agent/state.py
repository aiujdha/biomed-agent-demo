from typing import Annotated, Optional, TypedDict

from app.extraction.schemas import ClinicalTrialExtraction
from app.schemas.agent import AgentStep
from app.schemas.query import SourceChunk


def _reduce_steps(
    current: list[AgentStep], update: list[AgentStep]
) -> list[AgentStep]:
    return current + update


class ReportState(TypedDict):
    topic: str
    sources: list[SourceChunk]
    extracted_trial: Optional[ClinicalTrialExtraction]
    report: str
    steps: Annotated[list[AgentStep], _reduce_steps]
    error: Optional[str]
