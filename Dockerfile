############################
# 1️⃣ FRONTEND BUILDER
############################
FROM node:20 AS frontend-builder
WORKDIR /app/frontend

# Copy only dependency files first for better caching
COPY frontend/package.json frontend/pnpm-lock.yaml ./

# Install dependencies
RUN npm install -g pnpm@8.15.6 && \
    pnpm install --frozen-lockfile

# Copy full frontend source
COPY frontend/ ./

# Build static export
RUN pnpm build

############################
# 2️⃣ BACKEND BUILDER
############################
FROM python:3.11-slim AS backend-builder
WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

############################
# 3️⃣ RUNTIME IMAGE
############################
FROM python:3.11-slim
WORKDIR /app
ENV PYTHONUNBUFFERED=1
ENV PORT=${PORT:-8000}

# Install runtime utilities (curl for health-check) and create non-root user
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/* && \
    addgroup --system app && \
    adduser  --system --ingroup app --home /app app

# Copy Python dependencies
COPY --from=backend-builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages

# Copy backend code
COPY backend/ ./backend

# Copy frontend build
COPY --from=frontend-builder /app/frontend/out ./frontend_build

# Ensure application files are owned by non-root user
RUN chown -R app:app /app

# Switch to non-root user for runtime
USER app

# Expose port and run server
EXPOSE $PORT
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:${PORT:-8000}/api/health || exit 1
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "$PORT"]