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

# Copy requirements file from the backend directory
COPY backend/requirements.txt .

# Install dependencies into a specific prefix directory
# This makes it easy to copy only the installed packages to the runtime stage
# Use pip cache for faster rebuilds when requirements don't change
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --prefix="/install" -r requirements.txt --root-user-action=ignore

# Stage 2: Runtime - Create the final application image
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

# Copy the backend application code into the image
COPY backend/ .

# Copy templates directory from the repository root
COPY templates/ ./templates

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
CMD ["sh", "-c", "gunicorn -w 2 -k uvicorn.workers.UvicornWorker main_minimal:app -b 0.0.0.0:${PORT}"]
