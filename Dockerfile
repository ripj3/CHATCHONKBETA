############################
# 1️⃣  FRONT‑END BUILD STAGE
############################
FROM node:20 AS frontend-builder
WORKDIR /opt/frontend_build

# Install pnpm globally
RUN npm install -g pnpm@latest

# Copy manifests first for cache efficiency
COPY frontend/package.json frontend/pnpm-lock.yaml ./
RUN rm -f pnpm-lock.yaml && npx pnpm install && npx pnpm update
RUN rm -rf frontend/node_modules
RUN npx pnpm install --prefix frontend

# Copy the rest of the frontend source
COPY frontend/ ./

# Build → static export (no extra npm script needed)
RUN npx pnpm build

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
