# syntax=docker/dockerfile:1

############################
# Stage 1 - builder: install Python dependencies into an isolated prefix
############################
FROM python:3.12.7-slim-bookworm AS builder

WORKDIR /build

ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Dependency file first -> this layer is cached until requirements.txt changes
COPY requirements.txt .
RUN pip install --prefix=/install -r requirements.txt

############################
# Stage 2 - runtime: only what is needed to run the app
############################
FROM python:3.12.7-slim-bookworm AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000

WORKDIR /app

# Run as a non-root user
RUN useradd --system --no-create-home --uid 10001 glowlog

# Copy only the installed packages from the builder (no pip cache, no build leftovers)
COPY --from=builder /install /usr/local

# Source code last -> editing code does not invalidate the dependency layers
COPY --chown=glowlog:glowlog . .

USER glowlog

EXPOSE 8000

HEALTHCHECK --interval=15s --timeout=3s --start-period=20s --retries=3 \
    CMD ["python", "-c", "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2).status == 200 else 1)"]

# Exec form: gunicorn is PID 1 and receives SIGTERM directly (clean `docker compose down`)
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "2", "--access-logfile", "-", "app:app"]
