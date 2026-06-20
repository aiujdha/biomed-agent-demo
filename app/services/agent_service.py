from app.agent.report_workflow import ReportWorkflow
from app.schemas.agent import AgentReportResponse
from app.services.extraction_service import ExtractionService
from app.services.query_service import QueryService


class AgentService:
    def __init__(
        self,
        query_service: QueryService,
        extraction_service: ExtractionService,
    ) -> None:
        self.query_service = query_service
        self.extraction_service = extraction_service

    def generate_report(self, topic: str) -> AgentReportResponse:
        workflow = ReportWorkflow(
            query_service=self.query_service,
            extraction_service=self.extraction_service,
        )
        return workflow.run(topic=topic)
