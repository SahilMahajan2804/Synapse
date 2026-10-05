from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.core.config import Settings, get_settings
from app.core.security import require_internal_key


router = APIRouter()


@router.get("/ready", dependencies=[Depends(require_internal_key)])
def ready(request: Request, settings: Settings = Depends(get_settings)) -> dict[str, object]:
	if not request.app.state.detector_ready:
		raise HTTPException(
			status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
			detail="DETECTION_UNAVAILABLE",
		)
	return {
		"status": "READY",
		"india_recognizers": request.app.state.india_recognizers,
		"spacy_model": settings.spacy_model,
	}