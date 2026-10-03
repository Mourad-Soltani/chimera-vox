# ChimeraVox — Render / Docker image
# Free-tier friendly: CPU only, Ken Burns + edge-tts by default

FROM python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=7860

# System deps: FFmpeg for Ken Burns / stitch / upscale
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Python deps first (better layer cache)
COPY requirements-space.txt /app/requirements.txt
RUN pip install --upgrade pip && pip install -r requirements.txt

# Application
COPY pyproject.toml README.md /app/
COPY chimera_vox /app/chimera_vox
COPY app.py spaces.toml /app/
COPY assets /app/assets

# Install package in editable-ish mode (path import works via WORKDIR)
ENV PYTHONPATH=/app

EXPOSE 7860

# Render sets PORT; Gradio must bind 0.0.0.0
CMD ["python", "app.py"]
