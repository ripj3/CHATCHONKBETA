# Stage 1: Frontend Builder
FROM node:18 AS frontend-builder
WORKDIR /opt/frontend_build
# Copy the entire frontend codebase
COPY frontend/ ./
# Install dependencies - use npm ci for clean install based on package-lock.json
RUN npm ci
# Build and export the frontend application, outputting to /opt/frontend_build/out
RUN npm run build && npm run export
# Verify the output directory exists
RUN ls -la /opt/frontend_build/out  # fail fast if 'out' missing

# Stage 2: Python Builder - Install dependencies
FROM python:3.11-slim AS builder
WORKDIR /install
# Copy requirements file from the backend directory
COPY backend/requirements.txt ./
# Install Python dependencies into a specific prefix directory
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --prefix="/install" -r requirements.txt --no-cache-dir

# Stage 3: Runtime - Create the final application image
FROM python:3.11-slim AS runtime

# Set environment variables for Python
ENV PYTHONUNBUFFERED=1

# Set default port, Render will override this with its own PORT variable (usually 10000)
ENV PORT=${PORT:-8000}

# Set working directory for the application
WORKDIR /app

# Copy installed Python packages from the builder stage
COPY --from=builder /install /usr/local

# Copy the backend application code into the image
COPY backend/ ./backend

# Copy built frontend assets from frontend-builder stage
COPY --from=frontend-builder /opt/frontend_build/out ./frontend_build

# Command to run the application using Uvicorn
CMD ["bash", "-c", "uvicorn backend.main:app --host 0.0.0.0 --port $PORT"]
