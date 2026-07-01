# --- Stage 1: Build Dependencies ---
FROM python:3.12-slim AS builder

WORKDIR /build

# Install build tools and libraries required for C extensions
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy and compile dependencies into local wheels
COPY requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /build/wheels -r requirements.txt


# --- Stage 2: Runtime Runner ---
FROM python:3.12-slim AS runner

WORKDIR /backend

# Create a non-privileged system user and group
RUN groupadd -g 10001 appgroup && \
    useradd -u 10001 -g appgroup -d /backend -s /bin/bash appuser

# Install minimal runtime dependencies (libpq5 for PostgreSQL, curl for health checks)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy wheels from builder and install python packages
COPY --from=builder /build/wheels /wheels
COPY requirements.txt .
RUN pip install --no-cache-dir --no-index --find-links=/wheels -r requirements.txt && \
    rm -rf /wheels

# Copy application source code and adjust ownership
COPY --chown=appuser:appgroup . .

# Expose API runtime port
EXPOSE 8000

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

# Switch to non-root execution context
USER appuser

# Launch uvicorn server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
