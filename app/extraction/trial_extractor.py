from pydantic import ValidationError

from app.extraction.schemas import ClinicalTrialExtraction
from app.llm.client import LLMClient


TRIAL_EXTRACTION_PROMPT = """Extract clinical trial fields as JSON.
Return only JSON matching the ClinicalTrialExtraction schema."""


class TrialExtractor:
    def __init__(self, llm_client: LLMClient) -> None:
        self.llm_client = llm_client

    def extract(self, text: str) -> ClinicalTrialExtraction:
        raw = self.llm_client.generate(
            system_prompt=TRIAL_EXTRACTION_PROMPT,
            user_prompt=text,
        )
        try:
            return ClinicalTrialExtraction.model_validate_json(raw)
        except ValidationError as exc:
            raise ValueError(f"Trial extraction validation failed: {exc}") from exc