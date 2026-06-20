from app.agent.tools import extract_trial_fields, retrieve_documents, summarize_findings
from app.extraction.schemas import ClinicalTrialExtraction
from app.schemas.agent import AgentReportResponse, AgentStep
from app.schemas.query import SourceChunk
from app.services.extraction_service import ExtractionService
from app.services.query_service import QueryService


def _select_trial_document_id(sources: list[SourceChunk]) -> str | None:
    for source in sources:
        if "trial" in source.document_id:
            return source.document_id
    return None


class ReportWorkflow:
    def __init__(
        self,
        query_service: QueryService,
        extraction_service: ExtractionService,
    ) -> None:
        self.query_service = query_service
        self.extraction_service = extraction_service

    def run(self, topic: str) -> AgentReportResponse:
        steps: list[AgentStep] = []
        sources = retrieve_documents(self.query_service, topic)
        steps.append(
            AgentStep(
                name="retrieve_documents",
                status="success",
                summary=f"Retrieved {len(sources)} source chunks.",
            )
        )
        trial_extraction: ClinicalTrialExtraction | None = None
        selected_document_id = _select_trial_document_id(sources)
        if selected_document_id:
            try:
                trial_extraction = extract_trial_fields(
                    self.extraction_service,
                    selected_document_id,
                )
            except (FileNotFoundError, ValueError) as exc:
                steps.append(
                    AgentStep(
                        name="extract_trial_fields",
                        status="failed",
                        summary=f"Could not extract structured trial fields from {selected_document_id}: {exc}",
                    )
                )
            else:
                steps.append(
                    AgentStep(
                        name="extract_trial_fields",
                        status="success",
                        summary=(
                            f"Extracted structured trial fields from {selected_document_id}: "
                            f"{trial_extraction.phase}, primary endpoint "
                            f"{trial_extraction.primary_endpoint}."
                        ),
                    )
                )
        else:
            summary = "No retrieved source was available for structured extraction."
            if sources:
                summary = "Retrieved sources did not include a clinical trial document for structured extraction."
            steps.append(
                AgentStep(
                    name="extract_trial_fields",
                    status="skipped",
                    summary=summary,
                )
            )
        report = summarize_findings(topic, sources, trial_extraction)
        steps.append(
            AgentStep(
                name="summarize_findings",
                status="success",
                summary="Generated a source-grounded report summary.",
            )
        )
        steps.append(
            AgentStep(
                name="return_response",
                status="success",
                summary="Returned report, steps, and source references.",
            )
        )
        return AgentReportResponse(
            report=report,
            steps=steps,
            sources=[f"{source.source}#{source.chunk_index}" for source in sources],
        )
