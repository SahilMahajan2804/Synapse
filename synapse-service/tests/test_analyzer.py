from types import SimpleNamespace

import app.detection.analyzer as analyzer_module
from app.core.config import Settings


def test_analyzer_builder_adds_each_available_india_recognizer(monkeypatch) -> None:
    registered = []

    class FakeNlpEngineProvider:
        def __init__(self, nlp_configuration):
            self.configuration = nlp_configuration

        def create_engine(self):
            return object()

    class FakeRegistry:
        def __init__(self):
            pass

        def load_predefined_recognizers(self, languages, nlp_engine):
            assert languages == ["en"]
            assert nlp_engine is not None

        def add_recognizer(self, recognizer):
            registered.append(type(recognizer).__name__)

    class FakeAnalyzerEngine:
        def __init__(self, nlp_engine, registry, supported_languages):
            assert nlp_engine is not None
            assert registry is not None
            assert supported_languages == ["en"]

    class InAadhaarRecognizer:
        pass

    class InPanRecognizer:
        pass

    module = SimpleNamespace(InAadhaarRecognizer=InAadhaarRecognizer, InPanRecognizer=InPanRecognizer)
    monkeypatch.setattr(analyzer_module, "NlpEngineProvider", FakeNlpEngineProvider)
    monkeypatch.setattr(analyzer_module, "RecognizerRegistry", FakeRegistry)
    monkeypatch.setattr(analyzer_module, "AnalyzerEngine", FakeAnalyzerEngine)
    monkeypatch.setattr(analyzer_module.importlib, "import_module", lambda _: module)

    engine, india_entities = analyzer_module.build_analyzer(Settings(spacy_model="test-model"))

    assert isinstance(engine, FakeAnalyzerEngine)
    assert registered == ["InAadhaarRecognizer", "InPanRecognizer"]
    assert india_entities == ["IN_AADHAAR", "IN_PAN"]