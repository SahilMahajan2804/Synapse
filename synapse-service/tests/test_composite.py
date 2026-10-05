import pytest

from app.core.errors import DetectionUnavailableError
from app.detection.composite import CompositeDetector


class FailingPresidio:
    def detect(self, text: str):
        del text
        raise DetectionUnavailableError()


class TrackingRegex:
    called = False

    def detect(self, text: str):
        self.called = True
        del text
        return []


def test_presidio_failure_is_re_raised_without_regex_only_fallback() -> None:
    regex = TrackingRegex()
    detector = CompositeDetector(FailingPresidio(), regex)  # type: ignore[arg-type]

    with pytest.raises(DetectionUnavailableError):
        detector.detect("Aadhaar 2345 6789 0124")

    assert not regex.called
