# Synapse Phase 1

## Project Overview

Synapse is a context-preserving synthetic data router for cloud LLMs. Enterprises cannot send customer data (names, Aadhaar, PAN, phone, email, dates) directly to cloud LLMs. The request flow is:

1. The user enters a prompt and/or uploads a text PDF in the React UI.
2. Spring Boot extracts PDF text and orchestrates the request.
3. `synapse-service` detects PII with Microsoft Presidio and replaces values with realistic, context-preserving synthetic surrogates, never `[PERSON]` placeholders.
4. A leak guard verifies that no original value remains; if one does, the request is blocked.
5. Spring Boot sends only synthetic text to Gemini, OpenAI, or the mock LLM.
6. `synapse-service` maps surrogates in the LLM answer back to real values.
7. The UI displays Real Payload, Cloud Payload, Restored Response, mappings, leak-guard status, and timings.

| Responsibility                                | `backend/` | `synapse-service/` |
| --------------------------------------------- | ---------- | ------------------ |
| UI-facing REST API, CORS, and error responses | Yes        | No                 |
| PDF upload and PDFBox text extraction         | Yes        | No                 |
| Orchestration and timings                     | Yes        | No                 |
| Cloud LLM call                                | Yes        | Never              |
| PII detection (Presidio and India rules)      | No         | Yes                |
| Surrogate generation and date shifting        | No         | Yes                |
| Session mapping store                         | No         | Yes                |
| Leak guard                                    | No         | Yes                |
| Reverse mapping                               | No         | Yes                |

The React UI talks only to Spring Boot. `synapse-service` is internal-only.

## Hard Rules

- Never log raw user text, PII, surrogates, PDF text, or LLM text. Logs may contain only session IDs, entity-type counts, text lengths, leak-guard verdicts, HTTP status, and timings.
- Never include user text in exception messages.
- Fail closed: if `synapse-service` is unreachable or returns an error, the backend returns 503 and does not call the LLM. If Presidio fails, `synapse-service` returns 503. Never fall back to sending raw text.
- Load secrets only from environment variables. Never hardcode API keys. `.env` is git-ignored; provide `.env.example`.
- Service-to-service requests use `X-Internal-Key`; `synapse-service` rejects every request without the correct key except `GET /health`.
- Put every pipeline stage behind an interface or Protocol so Phase 2 can replace it.
- Out of scope: Ollama/local SLM, Redis, streaming/SSE, audit database, user login/Spring Security, OCR, multilingual support, and Kubernetes.
- Use small classes/modules, Java constructor injection, Python type hints, no Lombok, and unit tests for algorithms.

## End-to-End Acceptance Example

Input:

```text
Summarize Rahul Sharma's medical file. DOB 12/12/1980, Aadhaar 2345 6789 0124, phone +91 98765 43210, email rahul.sharma@gmail.com. He was admitted on 03/08/2026 and discharged on 08/08/2026.
```

Expected: seven entities (PERSON, DATE_TIME x3, IN_AADHAAR, PHONE_NUMBER, EMAIL_ADDRESS). A valid run replaces the name, identifiers, contact values, and dates with consistent synthetic values. The leak guard passes, only synthetic text reaches the LLM, and restoration returns the original values while preserving the five-day stay. `2345 6789 0124` is Verhoeff-valid; `2345 6789 0123` is invalid but should still be detected when preceded by Aadhaar context.
