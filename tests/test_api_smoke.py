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
