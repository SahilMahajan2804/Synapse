import logging
from collections.abc import Callable
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from presidio_analyzer import AnalyzerEngine

from app.api.routes import router
from app.core.config import Settings, get_settings
from app.detection.analyzer import build_analyzer
from app.detection.composite import CompositeDetector
from app.detection.presidio_detector import PresidioDetector
from app.detection.regex_fallback import RegexFallbackDetector


logger = logging.getLogger("synapse")


AnalyzerBuilder = Callable[[Settings], tuple[AnalyzerEngine, list[str]]]


def create_app(settings: Settings | None = None, analyzer_builder: AnalyzerBuilder | None = None) -> FastAPI:
    configured_settings = settings or get_settings()
    build = analyzer_builder or build_analyzer

    @asynccontextmanager
    async def lifespan(application: FastAPI) -> AsyncIterator[None]:
        application.state.detector_ready = False
        application.state.india_recognizers = []
        application.state.spacy_model = configured_settings.spacy_model
        try:
            analyzer, india_recognizers = build(configured_settings)
            analyzer.analyze(text="Rahul Sharma", language="en")
            application.state.analyzer = analyzer
            application.state.detector = CompositeDetector(
                PresidioDetector(analyzer, configured_settings),
                RegexFallbackDetector(),
            )
            application.state.india_recognizers = india_recognizers
            application.state.detector_ready = True
            logger.info(
                "presidio_initialized spacy_model=%s india_recognizers=%s",
                configured_settings.spacy_model,
                india_recognizers,
            )
        except Exception:
            logger.warning("presidio_initialization_failed detector_ready=false")
        yield

    application = FastAPI(
        title="Synapse Privacy Service",
        version="1.0.0",
        lifespan=lifespan,
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )
    application.dependency_overrides[get_settings] = lambda: configured_settings
    application.include_router(router)

    @application.get("/health")
    def health() -> dict[str, str]:
        return {"status": "UP"}

    return application


app = create_app()