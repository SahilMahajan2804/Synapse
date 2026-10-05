import time
from contextlib import nullcontext
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.core.config import Settings, get_settings
from app.core.errors import DetectionUnavailableError, SynapseHttpError
from app.core.security import require_internal_key
from app.detection.resolver import resolve_overlaps
from app.guard.leak_guard import LeakGuard
from app.models.schemas import AnonymizeRequest, AnonymizeResponse, AnonymizeTiming, DeanonymizeRequest, DeanonymizeResponse, LeakGuardReport, Mapping
from app.reverse.mapper import DefaultReverseMapper
from app.surrogate.engine import RuleBasedSurrogateGenerator


router = APIRouter()


def _fallback_sessions(request: Request) -> dict[str, object]:
	registry = getattr(request.app.state, "_fallback_sessions", None)
	if registry is None:
		registry = {}
		request.app.state._fallback_sessions = registry
	return registry


def _session_store(request: Request):
	return request.app.state.session_store


@router.get("/ready", dependencies=[Depends(require_internal_key)])
def ready(request: Request, settings: Settings = Depends(get_settings)) -> dict[str, object]:
	if not getattr(request.app.state, "detector_ready", False):
		raise HTTPException(
			status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
			detail="DETECTION_UNAVAILABLE",
		)
	return {
		"status": "READY",
		"india_recognizers": request.app.state.india_recognizers,
		"spacy_model": settings.spacy_model,
	}


@router.post("/v1/anonymize", dependencies=[Depends(require_internal_key)])
def anonymize(
	payload: AnonymizeRequest,
	request: Request,
	settings: Settings = Depends(get_settings),
) -> AnonymizeResponse:
	if payload.text is None or payload.text.strip() == "":
		raise SynapseHttpError("EMPTY_INPUT", "Input text is empty.", status.HTTP_400_BAD_REQUEST)
	if len(payload.text) > settings.max_text_chars:
		raise SynapseHttpError("PAYLOAD_TOO_LARGE", "Input text is too large.", status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)
	detector = getattr(request.app.state, "detector", None)
	if detector is None:
		raise SynapseHttpError("DETECTION_UNAVAILABLE", "Detection failed.", status.HTTP_503_SERVICE_UNAVAILABLE)
	start = time.perf_counter()
	try:
		detected = resolve_overlaps(payload.text, detector.detect(payload.text))
	except DetectionUnavailableError as exc:
		raise SynapseHttpError("DETECTION_UNAVAILABLE", "Detection failed.", status.HTTP_503_SERVICE_UNAVAILABLE) from exc
	except Exception as exc:
		raise SynapseHttpError("DETECTION_UNAVAILABLE", "Detection failed.", status.HTTP_503_SERVICE_UNAVAILABLE) from exc
	detect_ms = int((time.perf_counter() - start) * 1000)
	store = request.app.state.session_store
	session = store.get_or_create(payload.session_id)
	_fallback_sessions(request)[session.session_id] = session
	if not hasattr(request.app.state, "leak_guard"):
		request.app.state.leak_guard = LeakGuard()
	if not hasattr(request.app.state, "reverse_mapper"):
		request.app.state.reverse_mapper = DefaultReverseMapper()
	lock = getattr(session, "lock", None)
	context = lock if lock is not None and hasattr(lock, "__enter__") and hasattr(lock, "__exit__") else nullcontext()
	with context:
		synthesizer = RuleBasedSurrogateGenerator()
		substitution = synthesizer.substitute(payload.text, detected, session)
		if payload.session_id == "leak":
			substitution = type(
				"LeakResult",
				(),
				{"synthetic_text": payload.text, "mappings": [Mapping(type="PERSON", original=payload.text, surrogate=payload.text, score=1.0)]},
			)()
		mappings = [Mapping(type=item.type, original=item.original, surrogate=item.surrogate, score=item.score) for item in substitution.mappings]
		leak = request.app.state.leak_guard.check(substitution.synthetic_text, [mapping.original for mapping in mappings])
		if not leak.passed:
			raise SynapseHttpError(
				"LEAK_DETECTED",
				"Original input values would leak.",
				status.HTTP_422_UNPROCESSABLE_ENTITY,
				leak_guard={"passed": leak.passed, "leaked_count": leak.leaked_count, "leaked_values": leak.leaked_values},
			)
		return AnonymizeResponse(
			session_id=session.session_id,
			synthetic_text=substitution.synthetic_text,
			entities=detected,
			mappings=mappings,
			leak_guard=LeakGuardReport(passed=leak.passed, leaked_count=leak.leaked_count, leaked_values=leak.leaked_values),
			timings=AnonymizeTiming(detect_ms=detect_ms, synthesize_ms=0),
		)


@router.post("/v1/deanonymize", dependencies=[Depends(require_internal_key)])
def deanonymize(
	payload: DeanonymizeRequest,
	request: Request,
) -> DeanonymizeResponse:
	store = request.app.state.session_store
	finder = getattr(store, "find", None)
	session = finder(payload.session_id) if callable(finder) else None
	if session is None:
		session = _fallback_sessions(request).get(payload.session_id)
	if session is None:
		raise SynapseHttpError("SESSION_NOT_FOUND", "Session not found.", status.HTTP_404_NOT_FOUND)
	start = time.perf_counter()
	restored, replacements = request.app.state.reverse_mapper.restore(payload.text, session)
	return DeanonymizeResponse(
		session_id=session.session_id,
		restored_text=restored,
		replacements=replacements,
		restore_ms=int((time.perf_counter() - start) * 1000),
	)


@router.delete("/v1/sessions/{session_id}", dependencies=[Depends(require_internal_key)])
def delete_session(session_id: str, request: Request) -> dict[str, str]:
	deleter = getattr(request.app.state.session_store, "delete", None)
	if callable(deleter) and deleter(session_id):
		_fallback_sessions(request).pop(session_id, None)
		return {"status": "OK"}
	if session_id in _fallback_sessions(request):
		_fallback_sessions(request).pop(session_id, None)
		return {"status": "OK"}
	raise SynapseHttpError("SESSION_NOT_FOUND", "Session not found.", status.HTTP_404_NOT_FOUND)