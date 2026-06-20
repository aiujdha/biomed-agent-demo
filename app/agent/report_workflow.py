from typing import Any

from langgraph.graph import END, START, StateGraph

from app.agent.state import ReportState
from app.agent.tools import (
    extract_trial_fields,
    retrieve_documents,
    summarize_findings,
)
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


def _build_graph(
    query_service: QueryService,
    extraction_service: ExtractionService,
) -> Any:
    def retrieve_node(state: ReportState) -> dict:
        sources = retrieve_documents(query_service, state["topic"])
        summary = f"Retrieved {len(sources)} source chunks."
        step = AgentStep(name="retrieve_documents", status="success", summary=summary)
        return {"sources": sources, "steps": [step]}

    def extract_node(state: ReportState) -> dict:
        sources = state["sources"]
        selected_document_id = _select_trial_document_id(sources)
        trial_extraction: ClinicalTrialExtraction | None = None

        if selected_document_id:
            try:
                trial_extraction = extract_trial_fields(
                    extraction_service, selected_document_id
                )
            except (FileNotFoundError, ValueError) as exc:
                step = AgentStep(
                    name="extract_trial_fields",
                    status="failed",
                    summary=(
                        f"Could not extract structured trial fields from "
                        f"{selected_document_id}: {exc}"
                    ),
                )
                return {"extracted_trial": None, "steps": [step]}
            else:
                step = AgentStep(
                    name="extract_trial_fields",
                    status="success",
                    summary=(
                        f"Extracted structured trial fields from {selected_document_id}: "
                        f"{trial_extraction.phase}, primary endpoint "
                        f"{trial_extraction.primary_endpoint}."
                    ),
                )
                return {"extracted_trial": trial_extraction, "steps": [step]}
        else:
            summary = "No retrieved source was available for structured extraction."
            if sources:
                summary = (
                    "Retrieved sources did not include a clinical trial document "
                    "for structured extraction."
                )
            step = AgentStep(
                name="extract_trial_fields", status="skipped", summary=summary
            )
            return {"extracted_trial": None, "steps": [step]}

    def summarize_node(state: ReportState) -> dict:
        report = summarize_findings(
            state["topic"], state["sources"], state["extracted_trial"]
        )
        step = AgentStep(
            name="summarize_findings",
            status="success",
            summary="Generated a source-grounded report summary.",
        )
        return {"report": report, "steps": [step]}

    def return_node(state: ReportState) -> dict:
        step = AgentStep(
            name="return_response",
            status="success",
            summary="Returned report, steps, and source references.",
        )
        return {"steps": [step]}

    builder = StateGraph(ReportState)
    builder.add_node("retrieve_documents", retrieve_node)
    builder.add_node("extract_trial_fields", extract_node)
    builder.add_node("summarize_findings", summarize_node)
    builder.add_node("return_response", return_node)

    builder.add_edge(START, "retrieve_documents")
    builder.add_edge("retrieve_documents", "extract_trial_fields")
    builder.add_edge("extract_trial_fields", "summarize_findings")
    builder.add_edge("summarize_findings", "return_response")
    builder.add_edge("return_response", END)

    return builder.compile()


class ReportWorkflow:
    def __init__(
        self,
        query_service: QueryService,
        extraction_service: ExtractionService,
    ) -> None:
        self._graph = _build_graph(query_service, extraction_service)

    def run(self, topic: str) -> AgentReportResponse:
        initial: ReportState = {
            "topic": topic,
            "sources": [],
            "extracted_trial": None,
            "report": "",
            "steps": [],
            "error": None,
        }
        final = self._graph.invoke(initial)

        return AgentReportResponse(
            report=final["report"],
            steps=final["steps"],
            sources=[
                f"{source.source}#{source.chunk_index}"
                for source in final["sources"]
            ],
        )
