import pytest

from app.ingestion.chunking import chunk_text


def test_chunk_text_keeps_metadata_and_overlap():
    chunks = chunk_text(
        text="A" * 1200,
        source="trial_adc_001.md",
        document_id="trial_adc_001",
        chunk_size=500,
        chunk_overlap=50,
    )

    assert len(chunks) == 3
    assert chunks[0].document_id == "trial_adc_001"
    assert chunks[0].source == "trial_adc_001.md"
    assert chunks[0].chunk_index == 0
    assert len(chunks[0].text) == 500


def test_chunk_text_single_chunk():
    chunks = chunk_text(
        text="Hello world",
        source="test.md",
        document_id="test",
        chunk_size=500,
        chunk_overlap=50,
    )
    assert len(chunks) == 1
    assert chunks[0].text == "Hello world"
    assert chunks[0].chunk_index == 0


def test_chunk_text_empty_string():
    chunks = chunk_text(
        text="",
        source="test.md",
        document_id="test",
    )
    assert len(chunks) == 0


def test_chunk_text_invalid_overlap():
    with pytest.raises(ValueError):
        chunk_text(
            text="test",
            source="test.md",
            document_id="test",
            chunk_size=100,
            chunk_overlap=100,
        )


def test_chunk_text_invalid_chunk_size():
    with pytest.raises(ValueError):
        chunk_text(
            text="test",
            source="test.md",
            document_id="test",
            chunk_size=0,
        )
