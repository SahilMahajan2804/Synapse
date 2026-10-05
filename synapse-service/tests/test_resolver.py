from app.detection.regex_fallback import RegexFallbackDetector
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


def test_resolver_keeps_high_confidence_phone_over_overlapping_date() -> None:
    text = "Phone +91 98765 43210"
    number_start = text.index("98765")
    phone = RegexFallbackDetector().detect(text)[0]
    entities = [
        make_entity(text, number_start, len(text), "DATE_TIME", 0.85).model_copy(update={"source": "presidio"}),
        phone,
    ]

    resolved = resolve_overlaps(text, entities)

    assert [(entity.type, entity.text) for entity in resolved] == [
        ("PHONE_NUMBER", "+91 98765 43210")
    ]
