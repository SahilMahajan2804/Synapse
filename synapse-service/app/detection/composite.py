from collections.abc import Callable

from app.detection.base import PiiDetector
from app.detection.regex_fallback import RegexFallbackDetector
from app.detection.resolver import resolve_overlaps
from app.models.schemas import DetectedEntity


class CompositeDetector:
	def __init__(
		self,
		presidio_detector: PiiDetector,
		regex_detector: RegexFallbackDetector | None = None,
		resolver: Callable[[str, list[DetectedEntity]], list[DetectedEntity]] = resolve_overlaps,
	) -> None:
		self._presidio_detector = presidio_detector
		self._regex_detector = regex_detector or RegexFallbackDetector()
		self._resolver = resolver

	def detect(self, text: str) -> list[DetectedEntity]:
		presidio_entities = self._presidio_detector.detect(text)
		regex_entities = self._regex_detector.detect(text)
		return self._resolver(text, presidio_entities + regex_entities)