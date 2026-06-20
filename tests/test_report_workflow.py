"""Tests that the LangGraph workflow is correctly compiled and executed."""

from fastapi.testclient import TestClient

from app.agent.report_workflow import ReportWorkflow
from app.core.container import embedding_model, llm_client, vector_store
from app.main import app
from app.schemas.query import SourceChunk
from app.services.query_service import QueryService


class TestGraphCompilation:
    """Verify the LangGraph graph compiles correctly end-to-end."""

    def test_workflow_runs_via_compiled_graph(self) -> None:
        """ReportWorkflow produces correct 4-step output via LangGraph."""
        from app.rag.vector_store import FaissVectorStore

        vs = FaissVectorStore()
        qs = QueryService(
            vector_store=vs, embedding_model=embedding_model, llm_client=llm_client
        )
        # Use a minimal ExtractionService that won't be called (no sources)
        from app.extraction.trial_extractor import TrialExtractor

        es = type("FakeExtractionService", (), {"extract_trial": lambda self, **kw: None})()
        wf = ReportWorkflow(query_service=qs, extraction_service=es)  # type: ignore[arg-type]
        result = wf.run(topic="anything")
        assert len(result.steps) == 4
        assert result.steps[0].name == "retrieve_documents"
        assert result.steps[1].name == "extract_trial_fields"
        # Without ingested data, extraction should be skipped
        assert result.steps[1].status == "skipped"

    def test_extraction_failure_is_recorded_as_failed_step(self) -> None:
        class FakeQueryService:
            def retrieve_sources(self, question: str, top_k: int) -> list[SourceChunk]:
                return [
                    SourceChunk(
                        document_id="trial_adc_001",
                        source="trial_adc_001.md",
                        chunk_index=0,
                        score=1.0,
                        text="Phase II clinical trial summary",
                    )
                ]

        class FailingExtractionService:
            def extract_trial(self, document_id: str):
                raise ValueError("invalid structured output")

        wf = ReportWorkflow(
            query_service=FakeQueryService(),  # type: ignore[arg-type]
            extraction_service=FailingExtractionService(),  # type: ignore[arg-type]
        )
        result = wf.run(topic="ADC clinical trial")

        assert [step.name for step in result.steps] == [
            "retrieve_documents",
            "extract_trial_fields",
            "summarize_findings",
            "return_response",
        ]
        assert result.steps[1].status == "failed"
        assert "invalid structured output" in result.steps[1].summary
        assert result.sources == ["trial_adc_001.md#0"]
        assert result.report.startswith("Summary for ADC clinical trial.")


class TestAgentEndpoint:
    """Verify the /agent/report endpoint behavior remains unchanged."""

    def test_step_order_and_success(self) -> None:
        client = TestClient(app)
        client.post("/documents/ingest", json={"source": "samples"})

        response = client.post("/agent/report", json={"topic": "ADC clinical trial"})
        assert response.status_code == 200
        body = response.json()
        step_names = [step["name"] for step in body["steps"]]
        assert step_names == [
            "retrieve_documents",
            "extract_trial_fields",
            "summarize_findings",
            "return_response",
        ]
        assert all(step["status"] == "success" for step in body["steps"])

    def test_without_ingest_skips_extraction(self) -> None:
        client = TestClient(app)
        vector_store.clear()

        response = client.post("/agent/report", json={"topic": "ADC clinical trial"})
        assert response.status_code == 200
        body = response.json()
        assert body["sources"] == []
        assert body["steps"][1]["name"] == "extract_trial_fields"
        assert body["steps"][1]["status"] == "skipped"

    def test_non_trial_source_skips_extraction(self) -> None:
        client = TestClient(app)
        client.post("/documents/ingest", json={"source": "samples"})

        response = client.post("/agent/report", json={"topic": "cell culture SOP"})
        assert response.status_code == 200
        body = response.json()
        assert body["sources"]
        assert body["steps"][1]["name"] == "extract_trial_fields"
        assert body["steps"][1]["status"] == "skipped"
