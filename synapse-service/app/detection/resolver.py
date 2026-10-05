from app.models.schemas import DetectedEntity


def _utf16_index(text: str, index: int) -> int:
	return len(text[:index].encode("utf-16-le")) // 2


def _coerce_entity(entity: object) -> DetectedEntity:
	if isinstance(entity, DetectedEntity):
		return entity
	if isinstance(entity, dict):
		payload = dict(entity)
	else:
		payload = {name: getattr(entity, name) for name in ("type", "start", "end", "text", "score", "source") if hasattr(entity, name)}
	if "utf16_start" not in payload:
		payload["utf16_start"] = 0
	if "utf16_end" not in payload:
		payload["utf16_end"] = 0
	return DetectedEntity(**payload)


def resolve_overlaps(text: str, entities: list[DetectedEntity]) -> list[DetectedEntity]:
	coerced = [_coerce_entity(entity) for entity in entities]
	ordered = sorted(
		coerced,
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