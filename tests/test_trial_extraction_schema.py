import pytest
from pydantic import ValidationError

from app.extraction.schemas import ClinicalTrialExtraction


def test_trial_extraction_schema_accepts_valid_payload():
    payload = {
        "trial_id": "trial_adc_001",
        "phase": "Phase II",
        "indication": "HER2-positive solid tumors",
        "intervention": "ADC-101",
        "primary_endpoint": "Objective response rate",
        "secondary_endpoints": ["Progression-free survival", "Safety"],
        "sample_size": 120,
        "inclusion_criteria": ["Adult patients", "ECOG performance status 0-1"],
        "exclusion_criteria": ["Uncontrolled infection"],
    }

    result = ClinicalTrialExtraction.model_validate(payload)

    assert result.phase == "Phase II"
    assert result.sample_size == 120


def test_trial_extraction_schema_rejects_invalid_phase():
    payload = {
        "trial_id": "test",
        "phase": "Phase V",
        "indication": "Test",
        "intervention": "Test",
        "primary_endpoint": "Test",
    }

    with pytest.raises(ValidationError):
        ClinicalTrialExtraction.model_validate(payload)


def test_trial_extraction_schema_negative_sample_size():
    payload = {
        "trial_id": "test",
        "phase": "Phase I",
        "indication": "Test",
        "intervention": "Test",
        "primary_endpoint": "Test",
        "sample_size": -5,
    }

    with pytest.raises(ValidationError):
        ClinicalTrialExtraction.model_validate(payload)
