import json
from typing import Protocol


class LLMClient(Protocol):
    def generate(self, system_prompt: str, user_prompt: str) -> str: ...


class FakeLLMClient:
    def generate(self, system_prompt: str, user_prompt: str) -> str:
        if "JSON" in system_prompt and "extract" in system_prompt.lower():
            return self._mock_extraction(user_prompt)

        lines = [line.strip() for line in user_prompt.splitlines() if line.strip()]
        context_lines = [line for line in lines if line.startswith("[source:")]
        if not context_lines:
            return "The answer cannot be determined from the available documents."
        return "Based on the retrieved context: " + context_lines[0]

    def _mock_extraction(self, text: str) -> str:
        mock = {
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
        return json.dumps(mock)
