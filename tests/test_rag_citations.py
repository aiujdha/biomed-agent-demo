"""Tests for enhanced RAG citation fields."""

from fastapi.testclient import TestClient

from app.main import app


class TestCitationSchema:
    """SourceChunk must include new citation fields while keeping old ones."""

    def test_query_response_includes_citation_id(self) -> None:
        client = TestClient(app)
        client.post("/documents/ingest", json={"source": "samples"})
        response = client.post(
            "/query",
            json={"question": "What is the primary endpoint?", "top_k": 3},
        )
        assert response.status_code == 200
        body = response.json()
        assert len(body["sources"]) > 0
        source = body["sources"][0]
        assert "citation_id" in source
        assert isinstance(source["citation_id"], str)
        assert source["citation_id"] != ""

    def test_citation_id_format(self) -> None:
        client = TestClient(app)
        client.post("/documents/ingest", json={"source": "samples"})
        response = client.post(
            "/query",
            json={"question": "ADC trial", "top_k": 3},
        )
        body = response.json()
        for src in body["sources"]:
            expected = f"{src['source']}#{src['chunk_index']}"
            assert src["citation_id"] == expected, (
                f"expected {expected!r}, got {src['citation_id']!r}"
            )

    def test_query_response_includes_excerpt(self) -> None:
        client = TestClient(app)
        client.post("/documents/ingest", json={"source": "samples"})
        response = client.post(
            "/query",
            json={"question": "What is the primary endpoint?", "top_k": 3},
        )
        body = response.json()
        for src in body["sources"]:
            assert "excerpt" in src
            assert isinstance(src["excerpt"], str)
            # excerpt should be a truncated version of text
            assert src["excerpt"] == src["text"][:240]

    def test_excerpt_is_truncated_to_240_chars(self) -> None:
        client = TestClient(app)
        client.post("/documents/ingest", json={"source": "samples"})
        response = client.post(
            "/query",
            json={"question": "What is the primary endpoint?", "top_k": 3},
        )
        body = response.json()
        for src in body["sources"]:
            assert len(src["excerpt"]) <= 240

    def test_text_field_still_present(self) -> None:
        client = TestClient(app)
        client.post("/documents/ingest", json={"source": "samples"})
        response = client.post(
            "/query",
            json={"question": "What is the primary endpoint?", "top_k": 3},
        )
        body = response.json()
        for src in body["sources"]:
            assert "text" in src
            assert isinstance(src["text"], str)
            assert len(src["text"]) > 0

    def test_metadata_field_structure(self) -> None:
        client = TestClient(app)
        client.post("/documents/ingest", json={"source": "samples"})
        response = client.post(
            "/query",
            json={"question": "ADC trial", "top_k": 1},
        )
        body = response.json()
        src = body["sources"][0]
        assert "metadata" in src
        md = src["metadata"]
        assert md["document_id"] == src["document_id"]
        assert md["source"] == src["source"]
        assert md["chunk_index"] == src["chunk_index"]

    def test_score_field_still_present(self) -> None:
        client = TestClient(app)
        client.post("/documents/ingest", json={"source": "samples"})
        response = client.post(
            "/query",
            json={"question": "What is the primary endpoint?", "top_k": 3},
        )
        body = response.json()
        for src in body["sources"]:
            assert "score" in src
