############################
# 1️⃣  FRONT‑END BUILD
############################
FROM node:18 AS frontend-builder
WORKDIR /opt/frontend_build
# copy manifests first for better cache
COPY frontend/package.json frontend/package-lock.json* ./

# If a lockfile exists ➜ use npm ci, else fallback to npm install
RUN if [ -f package-lock.json ]; then npm ci; else npm install; fi

# copy the rest of the frontend code
COPY frontend/ ./
RUN npm run build && npm run export           # creates /opt/frontend_build/out
RUN test -d out                               # fail early if export missing

############################
# 2️⃣  PYTHON DEPS (unchanged)
############################
FROM python:3.11-slim AS builder
WORKDIR /install
COPY backend/requirements.txt ./
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements.txt --prefix=/install --no-cache-dir

############################
# 3️⃣  RUNTIME
############################
FROM python:3.11-slim AS runtime
WORKDIR /app
ENV PYTHONUNBUFFERED=1
ENV PORT=${PORT:-8000}

# Python deps & backend code
COPY --from=builder /install /usr/local
COPY backend/ ./backend

# Static bundle
COPY --from=frontend-builder /opt/frontend_build/out ./frontend_build

CMD ["bash", "-c", "uvicorn backend.main:app --host 0.0.0.0 --port $PORT"]
