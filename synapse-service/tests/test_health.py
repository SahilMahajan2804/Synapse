from fastapi.testclient import TestClient
from pydantic import SecretStr

from app.core.config import Settings
from app.main import create_app


class FakeAnalyzer:
    def analyze(self, text: str, language: str) -> list[object]:
        del text, language
        return []


def test_health_returns_up() -> None:
    settings = Settings(internal_key=SecretStr("test-key"), spacy_model="test-model")
    app = create_app(settings, lambda _: (FakeAnalyzer(), ["IN_AADHAAR", "IN_PAN"]))
    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "UP"}


def test_ready_requires_internal_key_and_reports_loaded_recognizers() -> None:
    settings = Settings(internal_key=SecretStr("test-key"), spacy_model="test-model")
    app = create_app(settings, lambda _: (FakeAnalyzer(), ["IN_AADHAAR", "IN_PAN"]))
    with TestClient(app) as client:
        unauthorized = client.get("/ready")
        response = client.get("/ready", headers={"X-Internal-Key": "test-key"})

    assert unauthorized.status_code == 401
    assert response.status_code == 200
    assert response.json() == {
        "status": "READY",
        "india_recognizers": ["IN_AADHAAR", "IN_PAN"],
        "spacy_model": "test-model",
    }


def test_ready_returns_503_when_analyzer_startup_fails() -> None:
    settings = Settings(internal_key=SecretStr("test-key"), spacy_model="test-model")

    def failed_builder(_: Settings) -> tuple[FakeAnalyzer, list[str]]:
        raise RuntimeError("model load details must not be returned")

    app = create_app(settings, failed_builder)
    with TestClient(app) as client:
        response = client.get("/ready", headers={"X-Internal-Key": "test-key"})

    assert response.status_code == 503
    assert "model load details" not in response.text