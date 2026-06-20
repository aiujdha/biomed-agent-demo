from typing import Literal

from pydantic import BaseModel, Field


AgentStepStatus = Literal["success", "skipped", "failed"]


class AgentStep(BaseModel):
    name: str
    status: AgentStepStatus
    summary: str


class AgentReportRequest(BaseModel):
    topic: str = Field(min_length=3)


class AgentReportResponse(BaseModel):
    report: str
    steps: list[AgentStep]
    sources: list[str]
