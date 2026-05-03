# syntax=docker/dockerfile:1
# ── Stage 1: build dependencies ───────────────────────────────────────────────
FROM python:3.10.12-slim AS builder

WORKDIR /build
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ── Stage 2: runtime image ─────────────────────────────────────────────────────
FROM python:3.10.12-slim AS runtime

# Install Playwright system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 libcups2 \
    libdrm2 libxkbcommon0 libxcomposite1 libxdamage1 libxfixes3 \
    libxrandr2 libgbm1 libasound2 libpango-1.0-0 libcairo2 \
    libx11-6 libxext6 libxrender1 libxtst6 \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Install Playwright browsers (Chromium only)
RUN playwright install chromium --with-deps 2>/dev/null || \
    python -m playwright install chromium

# Create non-root user
RUN useradd -m -u 1000 appuser

WORKDIR /app
COPY src/ ./src/
COPY pyproject.toml ./

# Install the package itself
RUN pip install --no-cache-dir -e .

# Switch to non-root
USER appuser

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=5000 \
    LOG_LEVEL=INFO \
    MAX_STEPS=8

EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/health')"

CMD ["python", "-m", "browseragent.app"]
