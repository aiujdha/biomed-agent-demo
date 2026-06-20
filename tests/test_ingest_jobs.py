"""Tests for async ingestion job endpoints."""

import time

from fastapi.testclient import TestClient

from app.main import app


class TestIngestJobs:
    """Cover create, query, succeeded, 404, and lifecycle."""

    def test_create_job_returns_201(self) -> None:
        client = TestClient(app)
        response = client.post("/documents/ingest-jobs", json={"source": "samples"})
        assert response.status_code == 201
        body = response.json()
        assert body["job_id"].startswith("ingest_")
        assert body["status"] == "pending"
        assert body["source"] == "samples"

    def test_get_job_returns_status_after_completion(self) -> None:
        client = TestClient(app)
        response = client.post("/documents/ingest-jobs", json={"source": "samples"})
        job_id = response.json()["job_id"]

        # Poll until the job completes (should be nearly instant).
        for _ in range(20):
            resp = client.get(f"/documents/ingest-jobs/{job_id}")
            assert resp.status_code == 200
            status = resp.json()["status"]
            if status in ("succeeded", "failed"):
                break
            time.sleep(0.05)

        body = resp.json()
        assert body["job_id"] == job_id
        assert body["status"] == "succeeded"
        assert isinstance(body["document_count"], int)
        assert body["document_count"] > 0
        assert isinstance(body["chunk_count"], int)
        assert body["chunk_count"] > 0

    def test_get_nonexistent_job_returns_404(self) -> None:
        client = TestClient(app)
        response = client.get("/documents/ingest-jobs/ingest_nonexistent")
        assert response.status_code == 404
        body = response.json()
        assert body["error"] == "not_found"

    def test_job_lifecycle_pending_to_succeeded(self) -> None:
        client = TestClient(app)
        response = client.post("/documents/ingest-jobs", json={"source": "samples"})
        job_id = response.json()["job_id"]

        # Immediately after creation the job may be pending or running.
        resp = client.get(f"/documents/ingest-jobs/{job_id}")
        assert resp.status_code == 200
        assert resp.json()["status"] in ("pending", "running", "succeeded")

        # Wait for completion.
        for _ in range(20):
            resp = client.get(f"/documents/ingest-jobs/{job_id}")
            status = resp.json()["status"]
            if status == "succeeded":
                break
            time.sleep(0.05)

        assert resp.json()["status"] == "succeeded"
        assert resp.json()["document_count"] == 3
