from app.models.schemas import DetectedEntity


def _utf16_index(text: str, index: int) -> int:
	return len(text[:index].encode("utf-16-le")) // 2


def resolve_overlaps(text: str, entities: list[DetectedEntity]) -> list[DetectedEntity]:
	ordered = sorted(
		entities,
		key=lambda entity: (-(entity.score), -(entity.end - entity.start), entity.start),
	)
	accepted: list[DetectedEntity] = []
	for entity in ordered:
		if entity.start < 0 or entity.end > len(text) or entity.start >= entity.end:
			continue
		if any(entity.start < current.end and entity.end > current.start for current in accepted):
			continue
		accepted.append(
			entity.model_copy(
				update={
					"text": text[entity.start : entity.end],
					"utf16_start": _utf16_index(text, entity.start),
					"utf16_end": _utf16_index(text, entity.end),
				}
			)
		)
	return sorted(accepted, key=lambda entity: entity.start)