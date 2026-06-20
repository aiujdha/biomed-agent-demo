from pathlib import Path

import pytest

from app.ingestion.loaders import load_markdown_file, load_sample_documents


def test_load_sample_documents_returns_three_samples():
    samples_dir = Path("samples")
    docs = load_sample_documents(samples_dir)

    assert len(docs) >= 3
    assert "sop_cell_culture" in docs
    assert "pubmed_adc_summary" in docs
    assert "trial_adc_001" in docs


def test_load_markdown_file_returns_non_empty_string():
    path = Path("samples/sop_cell_culture.md")
    content = load_markdown_file(path)

    assert isinstance(content, str)
    assert len(content) > 100
    assert "Cell Culture" in content


def test_load_markdown_file_not_found():
    path = Path("samples/nonexistent.md")
    with pytest.raises(FileNotFoundError):
        load_markdown_file(path)
