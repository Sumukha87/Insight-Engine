# FastAPI + Celery worker image
FROM python:3.11-slim

WORKDIR /app

# Install system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies (excluding nlp.txt — torch/spaCy too large for API image)
COPY requirements/ingest.txt requirements/ingest.txt
COPY requirements/graph.txt requirements/graph.txt
COPY requirements/api.txt requirements/api.txt
COPY requirements/mlops.txt requirements/mlops.txt
RUN pip install --no-cache-dir \
    -r requirements/ingest.txt \
    -r requirements/graph.txt \
    -r requirements/api.txt \
    -r requirements/mlops.txt

COPY src/ ./src/

CMD ["uvicorn", "src.backend.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
