from typing import Protocol

from app.models.schemas import DetectedEntity


class PiiDetector(Protocol):
    def detect(self, text: str) -> list[DetectedEntity]: ...