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
