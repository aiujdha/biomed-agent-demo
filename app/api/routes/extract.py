from fastapi import APIRouter, HTTPException

from app.core.container import llm_client
from app.extraction.trial_extractor import TrialExtractor
from app.schemas.extract import TrialExtractRequest, TrialExtractResponse
from app.services.extraction_service import ExtractionService

router = APIRouter(prefix="/extract", tags=["extract"])


@router.post("/trial", response_model=TrialExtractResponse)
def extract_trial(request: TrialExtractRequest) -> TrialExtractResponse:
    service = ExtractionService(
        extractor=TrialExtractor(llm_client=llm_client),
        samples_dir="samples",
    )
    try:
        result = service.extract_trial(document_id=request.document_id, text=request.text)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return TrialExtractResponse(result=result, validation_status="valid")
