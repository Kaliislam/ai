# syntax=docker/dockerfile:1
# TurkishJARVIS Docker image — Python 3.11 slim, multi-stage build

# ---------------------------------------------------------------------------
# Stage 1: Dependencies
# ---------------------------------------------------------------------------
FROM python:3.11-slim AS builder

WORKDIR /app

# Install build dependencies for packages with native extensions
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libsndfile1 \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip and install wheels
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip setuptools wheel \
    && pip wheel --no-cache-dir --wheel-dir /app/wheels -r requirements.txt

# ---------------------------------------------------------------------------
# Stage 2: Runtime
# ---------------------------------------------------------------------------
FROM python:3.11-slim AS runtime

WORKDIR /app

# Create non-root user
RUN groupadd -r jarvis && useradd -r -g jarvis -d /app -s /bin/bash jarvis

# Install runtime system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libsndfile1 \
    libgomp1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy pre-built wheels and install
COPY --from=builder /app/wheels /wheels
RUN pip install --no-cache /wheels/* \
    && rm -rf /wheels

# Copy application code
COPY turkish_jarvis/ ./turkish_jarvis/
COPY docker/entrypoint.sh ./docker/entrypoint.sh
RUN chmod +x ./docker/entrypoint.sh

# Create data & models directories with correct ownership
RUN mkdir -p /app/data /app/models /app/data/uploads \
    && chown -R jarvis:jarvis /app

USER jarvis

# Expose FastAPI + Gradio port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

ENTRYPOINT ["./docker/entrypoint.sh"]
CMD ["python", "-m", "uvicorn", "turkish_jarvis.main:app", "--host", "0.0.0.0", "--port", "8000"]
