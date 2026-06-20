from app.extraction.schemas import ClinicalTrialExtraction
from app.schemas.query import SourceChunk
from app.services.extraction_service import ExtractionService
from app.services.query_service import QueryService


def retrieve_documents(query_service: QueryService, topic: str) -> list[SourceChunk]:
    return query_service.retrieve_sources(question=topic, top_k=3)


def extract_trial_fields(
    extraction_service: ExtractionService,
    document_id: str,
) -> ClinicalTrialExtraction:
    return extraction_service.extract_trial(document_id=document_id)


def summarize_findings(
    topic: str,
    sources: list[SourceChunk],
    trial_extraction: ClinicalTrialExtraction | None = None,
) -> str:
    if not sources:
        return f"No supporting sources were found for: {topic}"
    joined_sources = ", ".join(f"{item.source}#{item.chunk_index}" for item in sources)
    summary = f"Summary for {topic}. Supporting sources: {joined_sources}."
    if trial_extraction:
        summary += (
            f" Extracted trial design: phase {trial_extraction.phase}; "
            f"primary endpoint: {trial_extraction.primary_endpoint}; "
            f"sample size: {trial_extraction.sample_size}."
        )
    return summary
