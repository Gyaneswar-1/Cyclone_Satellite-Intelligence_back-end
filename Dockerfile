# Production Dockerfile for StormSense Live Cyclone Intelligence Backend
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PORT=8000 \
    APP_ENV=production \
    DATA_PROVIDER=mock \
    ENABLE_VISION_MODEL=false

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies (use CPU-only PyTorch to minimize image size and prevent build timeouts on free tiers)
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir -r /app/backend/requirements.txt --extra-index-url https://download.pytorch.org/whl/cpu

# Copy application source and dataset
COPY backend/ /app/backend/
COPY stormsense_dataset/ /app/stormsense_dataset/
COPY scripts/ /app/scripts/

# Expose default port
EXPOSE 8000

# Health check dynamically matching $PORT
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/health || exit 1

# Start the server with dynamic port support (Railway, Render, Koyeb inject $PORT)
CMD ["sh", "-c", "uvicorn backend.app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
