import random

from fastapi.testclient import TestClient
from pydantic import SecretStr

from app.core.config import Settings
from app.main import create_app


class FakeDetector:
    def __init__(self) -> None:
        self.calls = 0

    def detect(self, text: str):
        self.calls += 1
        if text == "bad":
            raise RuntimeError("boom")
        return [
            type(
                "Entity",
                (),
                {"type": "PERSON", "start": 0, "end": 5, "text": "Rahul", "score": 0.9, "source": "regex"},
            )(),
            type(
                "Entity",
                (),
                {"type": "PHONE_NUMBER", "start": 0, "end": 0, "text": "", "score": 0.8, "source": "regex"},
            )(),
        ]


def build_app() -> TestClient:
    detector = FakeDetector()
    app = create_app(Settings(internal_key=SecretStr("dev-key"), spacy_model="en_core_web_lg"))
    app.state.detector = detector
    app.state.detector_ready = True
    app.state.india_recognizers = ["IN_AADHAAR", "IN_PAN"]
    app.state.session_store = type("Store", (), {"get_or_create": lambda self, session_id=None: type("S", (), {"session_id": session_id or "sess-1", "by_original": {}, "by_surrogate": {}, "used_surrogates": set(), "persons": [], "date_map": {}, "type_counters": {}, "lock": random.Random(1), "day_offset": 30})()})()
    return TestClient(app)


def test_anonymize_and_deanonymize_round_trip() -> None:
    client = build_app()
    anonymize = client.post("/v1/anonymize", headers={"X-Internal-Key": "dev-key"}, json={"session_id": "demo", "text": "Rahul"})
    assert anonymize.status_code == 200
    body = anonymize.json()
    assert body["session_id"] == "demo"
    assert body["synthetic_text"]
    assert "mappings" in body

    deanonymize = client.post("/v1/deanonymize", headers={"X-Internal-Key": "dev-key"}, json={"session_id": "demo", "text": body["synthetic_text"]})
    assert deanonymize.status_code == 200
    assert "Rahul" in deanonymize.json()["restored_text"]


def test_missing_key_and_unknown_session() -> None:
    client = build_app()
    unauthorized = client.post("/v1/anonymize", json={"text": "Rahul"})
    assert unauthorized.status_code == 401

    missing = client.post("/v1/deanonymize", headers={"X-Internal-Key": "dev-key"}, json={"session_id": "missing", "text": "Rahul"})
    assert missing.status_code == 404


def test_uninitialized_app_state_returns_service_unavailable() -> None:
    app = create_app(Settings(internal_key=SecretStr("dev-key"), spacy_model="en_core_web_lg"))
    client = TestClient(app)

    ready = client.get("/ready", headers={"X-Internal-Key": "dev-key"})
    assert ready.status_code == 503
    assert ready.json()["detail"] == "DETECTION_UNAVAILABLE"

    anonymize = client.post("/v1/anonymize", headers={"X-Internal-Key": "dev-key"}, json={"session_id": "demo", "text": "Rahul"})
    assert anonymize.status_code == 503
    assert anonymize.json()["error"] == "DETECTION_UNAVAILABLE"


def test_anonymize_with_real_session_lock_completes() -> None:
    app = create_app(Settings(internal_key=SecretStr("dev-key"), spacy_model="en_core_web_lg"))
    app.state.detector = FakeDetector()
    app.state.detector_ready = True
    client = TestClient(app)

    response = client.post(
        "/v1/anonymize",
        headers={"X-Internal-Key": "dev-key"},
        json={"session_id": "real-session", "text": "Rahul"},
    )

    assert response.status_code == 200
    assert response.json()["synthetic_text"] != "Rahul"


def test_leak_and_detection_failure() -> None:
    client = build_app()
    leak = client.post("/v1/anonymize", headers={"X-Internal-Key": "dev-key"}, json={"session_id": "leak", "text": "Rahul"})
    assert leak.status_code == 422
    assert leak.json()["error"] == "LEAK_DETECTED"

    app = create_app(Settings(internal_key=SecretStr("dev-key"), spacy_model="en_core_web_lg"))
    app.state.detector = type("Bad", (), {"detect": lambda self, text: (_ for _ in ()).throw(RuntimeError("boom"))})()
    app.state.detector_ready = True
    app.state.india_recognizers = []
    app.state.session_store = type("Store", (), {"get_or_create": lambda self, session_id=None: type("S", (), {"session_id": session_id or "n", "by_original": {}, "by_surrogate": {}, "used_surrogates": set(), "persons": [], "date_map": {}, "type_counters": {}, "lock": random.Random(2), "day_offset": 30})()})()
    bad = TestClient(app)
    resp = bad.post("/v1/anonymize", headers={"X-Internal-Key": "dev-key"}, json={"text": "Rahul"})
    assert resp.status_code == 503
