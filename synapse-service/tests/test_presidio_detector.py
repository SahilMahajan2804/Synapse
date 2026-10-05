from types import SimpleNamespace

import pytest
from pydantic import SecretStr

from app.core.config import Settings
from app.core.errors import DetectionUnavailableError
from app.detection.presidio_detector import PresidioDetector


class FakeAnalyzer:
    def analyze(self, **kwargs):
        self.kwargs = kwargs
        return [
            SimpleNamespace(entity_type="PERSON", start=2, end=14, score=0.9),
            SimpleNamespace(entity_type="URL", start=0, end=1, score=1.0),
            SimpleNamespace(entity_type="EMAIL_ADDRESS", start=0, end=1, score=0.2),
        ]


def test_presidio_detector_filters_types_and_scores_and_maps_utf16() -> None:
    text = "😀 Rahul Sharma"
    analyzer = FakeAnalyzer()
    settings = Settings(
        internal_key=SecretStr("test-key"),
        score_threshold=0.35,
        ignored_types=["URL"],
    )

    entities = PresidioDetector(analyzer, settings).detect(text)

    assert analyzer.kwargs == {"text": text, "language": "en", "score_threshold": 0.35}
    assert len(entities) == 1
    assert entities[0].type == "PERSON"
    assert entities[0].text == "Rahul Sharma"
    assert entities[0].utf16_start == 3
    assert entities[0].utf16_end == 15


def test_presidio_failure_raises_text_free_detection_error() -> None:
    class BrokenAnalyzer:
        def analyze(self, **kwargs):
            del kwargs
            raise RuntimeError("private text must not escape")

    detector = PresidioDetector(BrokenAnalyzer(), Settings())

    with pytest.raises(DetectionUnavailableError) as error:
        detector.detect("private text")

    assert str(error.value) == "PII detection is unavailable"
    assert "private text" not in str(error.value)