# Synapse Privacy Service

Phase 1 FastAPI privacy service. It detects PII, replaces values with session-scoped synthetic values, checks protected text for leaks, and restores surrogates in a later response. It does not parse PDFs or call an LLM; those responsibilities belong to the Spring Boot backend.

## Run locally

Use Python 3.12. From this directory, install dependencies and a spaCy model:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m spacy download en_core_web_sm
Copy-Item .env.example .env
```

Set a private `SYNAPSE_INTERNAL_KEY` in the local environment before starting the service. The service defaults to `en_core_web_lg`; `.env.example` opts into `en_core_web_sm` for lower-memory development. Set `SPACY_MODEL` to choose the installed model.

```powershell
uvicorn app.main:app --reload
```

`GET /health` is unauthenticated. Every other endpoint requires `X-Internal-Key`:

- `GET /ready` reports detector readiness and India recognizers.
- `POST /v1/anonymize` accepts `{"text":"...","session_id":null}`.
- `POST /v1/deanonymize` accepts `{"session_id":"...","text":"..."}`.
- `DELETE /v1/sessions/{session_id}` deletes session mappings.

Sessions and mappings are held in a bounded in-memory TTL cache and are lost when the process exits. OCR, streaming, external session storage, and durable auditing are out of scope. Requests whose PII detector cannot initialize or fails during detection return 503.

## Test

```powershell
pytest
```

## Container

Build and run with a secret supplied by the deployment environment:

```powershell
docker build -t synapse-privacy .
docker run --rm -p 8000:8000 -e SYNAPSE_INTERNAL_KEY="$env:SYNAPSE_INTERNAL_KEY" synapse-privacy
```

The service does not log request text, entity values, surrogates, or model responses. Operational logs contain only session identifiers, entity counts, lengths, verdicts, and timings.
