import re

from app.detection.verhoeff import is_valid
from app.models.schemas import DetectedEntity


_PHONE = re.compile(r"(?<!\d)(?:\+91[\s-]?|0)?[6-9]\d{4}[\s-]?\d{5}(?!\d)")
_EMAIL = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
_AADHAAR = re.compile(r"(?<!\d)[2-9]\d{3}[\s-]?\d{4}[\s-]?\d{4}(?!\d)")
_PAN = re.compile(r"\b[A-Z]{3}[ABCFGHJLPT][A-Z]\d{4}[A-Z]\b", re.IGNORECASE)
_AADHAAR_CONTEXT = re.compile(r"\b(?:aadhaar|aadhar|uid|uidai)\b", re.IGNORECASE)


def _utf16_index(text: str, index: int) -> int:
	return len(text[:index].encode("utf-16-le")) // 2


def _entity(text: str, match: re.Match[str], entity_type: str, score: float) -> DetectedEntity:
	return DetectedEntity(
		type=entity_type,
		start=match.start(),
		end=match.end(),
		utf16_start=_utf16_index(text, match.start()),
		utf16_end=_utf16_index(text, match.end()),
		text=match.group(),
		score=score,
		source="regex",
	)


class RegexFallbackDetector:
	def detect(self, text: str) -> list[DetectedEntity]:
		entities: list[DetectedEntity] = []
		for match in _PHONE.finditer(text):
			entities.append(_entity(text, match, "PHONE_NUMBER", 0.95))
		for match in _EMAIL.finditer(text):
			entities.append(_entity(text, match, "EMAIL_ADDRESS", 0.9))
		for match in _AADHAAR.finditer(text):
			digits = re.sub(r"\D", "", match.group())
			context_start = max(0, match.start() - 40)
			has_context = _AADHAAR_CONTEXT.search(text[context_start : match.start()]) is not None
			if is_valid(digits):
				score = 0.9
			elif has_context:
				score = 0.6
			else:
				continue
			entities.append(_entity(text, match, "IN_AADHAAR", score))
		for match in _PAN.finditer(text):
			entities.append(_entity(text, match, "IN_PAN", 0.85))
		return entities