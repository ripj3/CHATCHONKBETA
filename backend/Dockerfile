# Stage 1: Builder - Install dependencies
FROM python:3.11-slim-bullseye AS builder

# Set environment variables for Python and Pip
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100

# Set working directory for the build stage
WORKDIR /opt/app_build

# Copy requirements file from the build context (backend/ directory)
COPY requirements.txt .

# Install dependencies into a specific prefix directory
# This makes it easy to copy only the installed packages to the runtime stage
RUN pip install --no-cache-dir --prefix="/install" -r requirements.txt

# Stage 2: Frontend Builder - Build the Next.js frontend
FROM node:18-alpine AS frontend_builder

WORKDIR /app/frontend

# Copy frontend files
COPY frontend/package*.json ./
COPY frontend/ ./

# Install dependencies and build the frontend
RUN npm install && npm run build

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
RUN addgroup --system appgroup && \
    adduser --system --ingroup appgroup --no-create-home appuser

# Copy installed Python packages from the builder stage to the standard Python path
COPY --from=builder /install /usr/local

# Copy the application code from the build context (backend/ directory) into the image
# This assumes main.py and the app/ module are in the backend/ directory
COPY . .

# Copy the built frontend from the frontend_builder stage to the backend's static directory
COPY --from=frontend_builder /app/frontend/out /app/static

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

# Set environment variable for static files directory
ENV STATIC_FILES_DIR=/app/static

# Command to run the application using Gunicorn with Uvicorn workers
# Uses sh -c to allow environment variable expansion for $PORT
# Render provides the PORT environment variable (typically 10000)
# If PORT is not set, it defaults to 8000 (defined by ENV PORT=8000 above)
CMD ["sh", "-c", "gunicorn -w 2 -k uvicorn.workers.UvicornWorker main:app -b 0.0.0.0:${PORT}"]
