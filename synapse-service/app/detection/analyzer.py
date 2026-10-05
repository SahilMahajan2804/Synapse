import importlib
import logging
from typing import Any

from presidio_analyzer import AnalyzerEngine, RecognizerRegistry
from presidio_analyzer.nlp_engine import NlpEngineProvider

from app.core.config import Settings


logger = logging.getLogger("synapse.detection.analyzer")

_INDIA_RECOGNIZERS = (
	("InAadhaarRecognizer", "IN_AADHAAR"),
	("InPanRecognizer", "IN_PAN"),
	("InVoterRecognizer", "IN_VOTER"),
	("InPassportRecognizer", "IN_PASSPORT"),
	("InVehicleRegistrationRecognizer", "IN_VEHICLE_REGISTRATION"),
	("InGstinRecognizer", "IN_GSTIN"),
)


def _load_india_recognizers(registry: RecognizerRegistry) -> list[str]:
	loaded: list[str] = []
	for class_name, entity_name in _INDIA_RECOGNIZERS:
		try:
			module = importlib.import_module("presidio_analyzer.predefined_recognizers")
			recognizer_type: Any = getattr(module, class_name)
		except (ImportError, AttributeError):
			logger.warning("india_recognizer_unavailable recognizer=%s", class_name)
			continue
		registry.add_recognizer(recognizer_type())
		loaded.append(entity_name)
	return loaded


def build_analyzer(settings: Settings) -> tuple[AnalyzerEngine, list[str]]:
	nlp_engine = NlpEngineProvider(
		nlp_configuration={
			"nlp_engine_name": "spacy",
			"models": [{"lang_code": "en", "model_name": settings.spacy_model}],
		}
	).create_engine()
	registry = RecognizerRegistry()
	registry.load_predefined_recognizers(languages=["en"], nlp_engine=nlp_engine)
	india_recognizers = _load_india_recognizers(registry)
	analyzer = AnalyzerEngine(nlp_engine=nlp_engine, registry=registry, supported_languages=["en"])
	return analyzer, india_recognizers