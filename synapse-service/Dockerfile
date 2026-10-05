FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

ARG SPACY_MODEL=en_core_web_lg
ENV SPACY_MODEL=${SPACY_MODEL}

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && python -m spacy download ${SPACY_MODEL}

COPY app ./app
RUN useradd --create-home --shell /usr/sbin/nologin synapse \
    && chown -R synapse:synapse /app
USER synapse

EXPOSE 8000
HEALTHCHECK --interval=20s --timeout=4s --retries=5 --start-period=120s CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2)"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]