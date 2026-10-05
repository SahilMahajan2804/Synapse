from presidio_analyzer import AnalyzerEngine

from app.core.config import Settings
from app.core.errors import DetectionUnavailableError
from app.models.schemas import DetectedEntity


def _utf16_index(text: str, index: int) -> int:
	return len(text[:index].encode("utf-16-le")) // 2


class PresidioDetector:
	def __init__(self, analyzer: AnalyzerEngine, settings: Settings) -> None:
		self._analyzer = analyzer
		self._score_threshold = settings.score_threshold
		self._ignored_types = set(settings.ignored_types)

	def detect(self, text: str) -> list[DetectedEntity]:
		try:
			results = self._analyzer.analyze(
				text=text,
				language="en",
				score_threshold=self._score_threshold,
			)
			entities: list[DetectedEntity] = []
			for result in results:
				if result.entity_type in self._ignored_types or float(result.score) < self._score_threshold:
					continue
				entities.append(
					DetectedEntity(
						type=result.entity_type,
						start=result.start,
						end=result.end,
						utf16_start=_utf16_index(text, result.start),
						utf16_end=_utf16_index(text, result.end),
						text=text[result.start : result.end],
						score=float(result.score),
						source="presidio",
					)
				)
			return entities
		except Exception as exc:
			raise DetectionUnavailableError() from exc