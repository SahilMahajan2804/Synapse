# Synapse Phase 1

Step 1 creates the monorepo service skeleton. The backend has its Spring Boot build/configuration entry point; the FastAPI privacy service currently implements only `GET /health` and returns `{"status":"UP"}`. Pipeline behavior will be added in later steps.

## Docker Compose

Copy `.env.example` to `.env`, then start the backend and privacy service:

```powershell
docker compose up --build -d
docker compose ps
```

Compose automatically merges `docker-compose.override.yml` for local development and publishes the privacy service on port 8000. To use only the internal network configuration, specify `-f docker-compose.yml` explicitly. The backend is available on port 8080.

## Local checks

Build the backend from `backend/`:

```powershell
./mvnw -q -DskipTests package
```

Install and run the Python service from `synapse-service/`:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m spacy download en_core_web_lg
uvicorn app.main:app --port 8000
```

Then check `http://localhost:8000/health`; it should return `{"status":"UP"}`. No database or application pipeline is included in this step.
