from app.detection.resolver import resolve_overlaps
from app.models.schemas import DetectedEntity


def make_entity(text: str, start: int, end: int, entity_type: str, score: float) -> DetectedEntity:
    return DetectedEntity(
        type=entity_type,
        start=start,
        end=end,
        utf16_start=0,
        utf16_end=0,
        text="stale value",
        score=score,
        source="regex",
    )


def test_resolver_prefers_score_and_calculates_utf16_offsets() -> None:
    text = "😀 Rahul Sharma"
    name_start = 2
    entities = [
        make_entity(text, name_start, len(text), "PERSON", 0.9),
        make_entity(text, name_start, name_start + 5, "LOCATION", 0.8),
    ]

    resolved = resolve_overlaps(text, entities)

    assert len(resolved) == 1
    assert resolved[0].type == "PERSON"
    assert resolved[0].text == "Rahul Sharma"
    assert resolved[0].utf16_start == 3
    assert resolved[0].utf16_end == 15
