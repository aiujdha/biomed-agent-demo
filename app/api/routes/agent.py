from fastapi import APIRouter

from app.core.container import embedding_model, llm_client, vector_store
from app.extraction.trial_extractor import TrialExtractor
from app.schemas.agent import AgentReportRequest, AgentReportResponse
from app.services.agent_service import AgentService
from app.services.extraction_service import ExtractionService
from app.services.query_service import QueryService

router = APIRouter(prefix="/agent", tags=["agent"])


@router.post("/report", response_model=AgentReportResponse)
def generate_agent_report(request: AgentReportRequest) -> AgentReportResponse:
    query_service = QueryService(
        vector_store=vector_store,
        embedding_model=embedding_model,
        llm_client=llm_client,
    )
    extraction_service = ExtractionService(
        extractor=TrialExtractor(llm_client=llm_client),
        samples_dir="samples",
    )
    service = AgentService(
        query_service=query_service,
        extraction_service=extraction_service,
    )
    return service.generate_report(topic=request.topic)
