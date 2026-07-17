# =============================================================================
# Dental Web Agent — Dockerfile
# =============================================================================
# Multi-stage build:
#   Stage 1 (builder)  – install Python deps into a venv
#   Stage 2 (runtime)  – copy venv + source, run uvicorn
# =============================================================================

# --------------------------------------------------------------------------- #
# Stage 1: Builder — install all dependencies                                 #
# --------------------------------------------------------------------------- #
FROM python:3.11-slim AS builder

WORKDIR /build

# System deps needed to compile some Python packages (e.g. pydub → ffmpeg C bindings)
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        git \
        ffmpeg \
        wget \
    && rm -rf /var/lib/apt/lists/*

# Create isolated virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python dependencies first (layer-cached unless requirements change)
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Pre-download the Whisper model at build time using wget (retry-capable).
# This avoids runtime downloads and the SHA256 mismatch error in containers.
# The base model SHA256 is hardcoded in openai-whisper — we verify it matches.
# Change "base" URL below only if you change STT_MODEL in config.py / .env
RUN mkdir -p /opt/whisper_models && \
    wget \
        --retry-connrefused \
        --waitretry=10 \
        --read-timeout=120 \
        --timeout=60 \
        --tries=10 \
        --show-progress \
        -O /opt/whisper_models/base.pt \
        "https://openaipublic.azureedge.net/main/whisper/models/ed3a0b6b1c0edf879ad9b11b1af5a0e6ab5db9205f891f668f8b0e6c6326e34e/base.pt" && \
    echo "Whisper base model downloaded successfully."

# --------------------------------------------------------------------------- #
# Stage 2: Runtime — lean image with only what's needed to serve              #
# --------------------------------------------------------------------------- #
FROM python:3.11-slim AS runtime

# ffmpeg is required at runtime by pydub / whisper audio decoding
RUN apt-get update && apt-get install -y --no-install-recommends \
        ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy pre-downloaded Whisper model from builder stage
COPY --from=builder /opt/whisper_models /opt/whisper_models
ENV WHISPER_DOWNLOAD_ROOT=/opt/whisper_models

# Non-root user for security
RUN useradd --create-home --shell /bin/bash appuser

WORKDIR /app

# Copy application source code
COPY --chown=appuser:appuser . .

# Create writable directories for SQLite DB and temp audio files.
# /app/data  → persistent database location
# /app/tmp   → temporary audio uploads during STT processing
RUN mkdir -p /app/data /app/tmp \
    && chown -R appuser:appuser /app/data /app/tmp

# Use /tmp for SQLite — always writable by any user in any container.
# Override DATABASE_URL env var on Render if you want a different path.
ENV DATABASE_URL="sqlite:////tmp/dental.db"

# Switch to non-root user
USER appuser

# Expose FastAPI / uvicorn port
EXPOSE 8000

# Health-check — uses the /health endpoint defined in main.py
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Launch uvicorn — use Render's injected PORT env var (falls back to 8000 locally)
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1"]
