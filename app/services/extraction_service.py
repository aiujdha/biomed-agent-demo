from pathlib import Path

from app.extraction.schemas import ClinicalTrialExtraction
from app.extraction.trial_extractor import TrialExtractor
from app.ingestion.loaders import load_markdown_file


class ExtractionService:
    def __init__(
        self,
        extractor: TrialExtractor,
        samples_dir: str = "samples",
    ) -> None:
        self.extractor = extractor
        self.samples_dir = Path(samples_dir)

    def extract_trial(
        self,
        document_id: str | None = None,
        text: str | None = None,
    ) -> ClinicalTrialExtraction:
        if text:
            return self.extractor.extract(text)
        if document_id:
            path = self.samples_dir / f"{document_id}.md"
            text = load_markdown_file(path)
            return self.extractor.extract(text)
        raise ValueError("document_id or text is required")