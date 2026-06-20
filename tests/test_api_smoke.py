from fastapi.testclient import TestClient

from app.core.container import vector_store
from app.main import app


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

    assert response.status_code == 422


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

    assert response.status_code == 404
    assert "Document not found" in response.json()["detail"]
