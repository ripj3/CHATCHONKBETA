# Stage 1: Python Builder - Install dependencies
FROM python:3.11-slim-bullseye AS builder

# Set environment variables for Python and Pip
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100

# Set working directory for the build stage
WORKDIR /opt/app_build

# Copy requirements file from the backend directory
COPY backend/requirements.txt .

# Install dependencies into a specific prefix directory
# This makes it easy to copy only the installed packages to the runtime stage
# Use pip cache for faster rebuilds when requirements don't change
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --prefix="/install" -r requirements.txt --root-user-action=ignore

# Stage 2: Frontend Builder
FROM node:18-slim AS frontend-builder
WORKDIR /opt/frontend_build
# Copy package.json and package-lock.json (if available) first
COPY frontend/package.json frontend/package-lock.json* ./
# Install dependencies - use npm ci if package-lock.json is present and you want deterministic builds
# Using --only=production might be problematic if build scripts are in devDependencies
# For Next.js, build typically requires devDependencies.
RUN npm ci || npm install
# Copy the rest of the frontend code
COPY frontend/ ./
# Build the frontend - this should produce an 'out' directory with output: 'export'
RUN npm run build
# Expected output: /opt/frontend_build/out

# Stage 3: Runtime - Create the final application image
FROM python:3.11-slim-bullseye AS runtime

# Set environment variables for Python
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Set default port, Render will override this with its own PORT variable (usually 10000)
ENV PORT=8000

# Set working directory for the application
WORKDIR /app

# Create a non-root user and group for security
# Done before copying app files that might need specific ownership later, though COPY usually makes root owner.
RUN addgroup --system appgroup && \
    adduser --system --ingroup appgroup --no-create-home appuser

# Copy installed Python packages from the builder stage
COPY --from=builder /install /usr/local

# Copy built frontend assets from frontend-builder stage
# This assumes 'npm run build' in the frontend-builder stage creates an 'out' directory.
COPY --from=frontend-builder /opt/frontend_build/out ./frontend_build

# Copy the backend application code into the image
COPY backend/ .

# Copy templates directory from the repository root
COPY templates/ ./templates

# Create and set permissions for the uploads directory
# Ensure appuser can write here if uploads are saved locally by the app.
# If uploads go directly to cloud storage, this might just need to exist.
RUN mkdir -p uploads && chown appuser:appgroup uploads

# Switch to the non-root user
USER appuser

# Add Docker labels for metadata
LABEL maintainer="Rip Jonesy"
LABEL project="ChatChonk"
LABEL version="0.1.0"
LABEL description="ChatChonk FastAPI Backend - Tame the Chatter. Find the Signal."

# Expose the port the application will listen on internally
# Render will map its external PORT to this port
EXPOSE 8000

# Command to run the application using Gunicorn with Uvicorn workers
# Uses sh -c to allow environment variable expansion for $PORT
# Render provides the PORT environment variable (typically 10000)
# If PORT is not set, it defaults to 8000 (defined by ENV PORT=8000 above)
CMD ["sh", "-c", "gunicorn -w 2 -k uvicorn.workers.UvicornWorker main:app -b 0.0.0.0:${PORT}"]
