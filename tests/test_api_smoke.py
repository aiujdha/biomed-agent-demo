from fastapi.testclient import TestClient

from app.core.container import vector_store
from app.main import app


def assert_error_response(response, status_code: int, error: str) -> dict:
    assert response.status_code == status_code
    body = response.json()
    assert body["error"] == error
    assert isinstance(body["message"], str)
    assert body["request_id"] is None
    return body


def test_ingest_samples_returns_counts():
    client = TestClient(app)
    response = client.post("/documents/ingest", json={"source": "samples"})

    assert response.status_code == 200
    body = response.json()
    assert body["document_count"] >= 3
    assert body["chunk_count"] >= 3
    assert body["chunk_count"] >= body["document_count"]
    assert vector_store.count == body["chunk_count"]
    assert vector_store.index.ntotal == body["chunk_count"]


def test_ingest_samples_is_idempotent():
    client = TestClient(app)

    first = client.post("/documents/ingest", json={"source": "samples"})
    second = client.post("/documents/ingest", json={"source": "samples"})

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json() == second.json()
    assert vector_store.count == second.json()["chunk_count"]
    assert vector_store.index.ntotal == second.json()["chunk_count"]


def test_query_returns_answer_and_sources():
    client = TestClient(app)
    # Ensure documents are ingested first
    client.post("/documents/ingest", json={"source": "samples"})

    response = client.post(
        "/query",
        json={"question": "What is the primary endpoint of the ADC trial?", "top_k": 3},
    )

    assert response.status_code == 200
    body = response.json()
    assert len(body["answer"]) > 0
    assert len(body["sources"]) > 0
    assert len(body["sources"]) <= 3
    assert all(source["score"] is not None for source in body["sources"])
    assert body["sources"][0]["source"] == "trial_adc_001.md"
    assert "Primary Endpoint" in body["sources"][0]["text"]
    assert "Primary Endpoint" in body["answer"]
    assert body["disclaimer"] == "This demo is for software engineering evaluation only and does not provide medical advice."


def test_query_without_ingest_returns_empty_sources():
    client = TestClient(app)
    vector_store.clear()

    response = client.post("/query", json={"question": "What is the primary endpoint?", "top_k": 3})

    assert response.status_code == 200
    body = response.json()
    assert body["answer"] == "The answer cannot be determined from the available documents."
    assert body["sources"] == []


def test_query_invalid_question():
    client = TestClient(app)
    response = client.post("/query", json={"question": "ab"})

    body = assert_error_response(response, 422, "validation_error")
    assert "question" in body["message"]


def test_extract_trial_by_document_id_returns_structured_result():
    client = TestClient(app)

    response = client.post("/extract/trial", json={"document_id": "trial_adc_001"})

    assert response.status_code == 200
    body = response.json()
    assert body["validation_status"] == "valid"
    assert body["result"]["trial_id"] == "trial_adc_001"
    assert body["result"]["phase"] == "Phase II"
    assert body["result"]["sample_size"] == 120


def test_extract_trial_by_text_returns_structured_result():
    client = TestClient(app)

    response = client.post(
        "/extract/trial",
        json={
            "text": "A Phase II trial of ADC-101 in HER2-positive advanced solid tumors "
            "with primary endpoint objective response rate."
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["validation_status"] == "valid"
    assert body["result"]["primary_endpoint"] == "Objective response rate"


def test_extract_trial_missing_document_returns_404():
    client = TestClient(app)

    response = client.post("/extract/trial", json={"document_id": "missing_trial"})

    body = assert_error_response(response, 404, "not_found")
    assert "Document not found" in body["message"]


def test_agent_report_returns_steps():
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
    assert len(body["sources"]) > 0
    assert len(body["report"]) > 0
    assert "Objective response rate" in body["report"]
    assert "sample size: 120" in body["report"]


def test_agent_report_without_ingest_skips_extraction():
    client = TestClient(app)
    vector_store.clear()

    response = client.post("/agent/report", json={"topic": "ADC clinical trial"})

    assert response.status_code == 200
    body = response.json()
    assert body["sources"] == []
    assert body["steps"][1]["name"] == "extract_trial_fields"
    assert body["steps"][1]["status"] == "skipped"
    assert "No supporting sources" in body["report"]


def test_agent_report_skips_extraction_for_non_trial_sources():
    client = TestClient(app)
    client.post("/documents/ingest", json={"source": "samples"})

    response = client.post("/agent/report", json={"topic": "cell culture SOP"})

    assert response.status_code == 200
    body = response.json()
    assert body["sources"]
    assert body["steps"][1]["name"] == "extract_trial_fields"
    assert body["steps"][1]["status"] == "skipped"
    assert "clinical trial document" in body["steps"][1]["summary"]
    assert "Objective response rate" not in body["report"]
    assert "sample size: 120" not in body["report"]


def test_agent_report_invalid_topic():
    client = TestClient(app)

    response = client.post("/agent/report", json={"topic": "ab"})

    body = assert_error_response(response, 422, "validation_error")
    assert "topic" in body["message"]


def test_unknown_route_returns_error_response():
    client = TestClient(app)

    response = client.get("/missing")

    body = assert_error_response(response, 404, "not_found")
    assert body["message"] == "Not Found"
