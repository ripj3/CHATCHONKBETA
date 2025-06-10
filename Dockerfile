############################
# 1️⃣  FRONT‑END BUILD STAGE
############################
FROM node:18 AS frontend-builder
WORKDIR /opt/frontend_build

# Copy manifests first for cache efficiency
COPY frontend/package.json frontend/package-lock.json* ./
RUN if [ -f package-lock.json ]; then npm ci; else npm install; fi

# Copy the rest of the frontend source
COPY frontend/ ./

# Build frontend then explicitly export to the `out/` directory.
# Some Render builds failed to find the static files when relying solely on the
# built‑in export behavior, so we run `next export` explicitly.
RUN npm run build && npx next export

############################
# 2️⃣  PYTHON DEP STAGE
############################
FROM python:3.11-slim AS builder
WORKDIR /install
COPY backend/requirements.txt ./
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements.txt --prefix=/install --no-cache-dir

############################
# 3️⃣  RUNTIME STAGE
############################
FROM python:3.11-slim AS runtime
WORKDIR /app
ENV PYTHONUNBUFFERED=1
ENV PORT=${PORT:-8000}

# Python deps & backend code
COPY --from=builder /install /usr/local
COPY backend/ ./backend

# Static frontend bundle
# Next.js with `output: 'export'` writes the static site to the `out/` directory


COPY --from=frontend-builder /opt/frontend_build/out ./frontend_build

CMD ["bash", "-c", "uvicorn backend.main:app --host 0.0.0.0 --port $PORT"]
