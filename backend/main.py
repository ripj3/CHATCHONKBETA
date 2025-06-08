"""
ChatChonk - Main FastAPI Application Entry Point

This module initializes the FastAPI application with all necessary middleware,
routers, and configuration for the ChatChonk backend.

Author: Rip Jonesy
"""

import asyncio
import logging
import os
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Callable, Dict, List, Optional, Union
import uvicorn
from fastapi import FastAPI, HTTPException, Request, Response, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi.routing import APIRouter
from fastapi.staticfiles import StaticFiles
from collections import defaultdict

# Import application settings
from backend.app.core.config import settings
logging.basicConfig(
    level=settings.LOG_LEVEL.value,
    format=settings.LOG_FORMAT,
)

# Configure logging
logger = logging.getLogger("chatchonk")

# In-memory metrics storage (for demonstration purposes)
# In a real application, use a proper metrics library like Prometheus client or a time-series database
metrics = {
    "total_requests": 0,
    "successful_requests": 0,
    "error_requests": 0,
    "total_processing_time": 0.0,
    "request_counts_by_path": defaultdict(int),
    "error_counts_by_path": defaultdict(int),
    "status_code_counts": defaultdict(int),
}


# App lifecycle management
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application startup and shutdown events.
    Creates necessary directories and initializes resources.
    """
    # Startup: Initialize resources
    logger.info("ChatChonk backend starting up...")

    # Skip directory creation to avoid permission issues
    logger.info("Skipping directory creation in production environment")

    # Skip Discord bot and AI initialization for now
    if False:  # Disabled for initial deployment
        logger.info("Starting Discord bot...")
        try:
            from app.services.discord_service import get_discord_service, DiscordConfig

            discord_config = DiscordConfig(
                bot_token=settings.DISCORD_BOT_TOKEN.get_secret_value(),
                guild_id=settings.DISCORD_GUILD_ID,
                general_channel_id=settings.DISCORD_GENERAL_CHANNEL_ID,
                support_channel_id=settings.DISCORD_SUPPORT_CHANNEL_ID,
                announcements_channel_id=settings.DISCORD_ANNOUNCEMENTS_CHANNEL_ID,
                feedback_channel_id=settings.DISCORD_FEEDBACK_CHANNEL_ID,
                free_role_id=settings.DISCORD_FREE_ROLE_ID,
                lilbean_role_id=settings.DISCORD_LILBEAN_ROLE_ID,
                clawback_role_id=settings.DISCORD_CLAWBACK_ROLE_ID,
                bigchonk_role_id=settings.DISCORD_BIGCHONK_ROLE_ID,
                meowtrix_role_id=settings.DISCORD_MEOWTRIX_ROLE_ID,
                admin_role_id=settings.DISCORD_ADMIN_ROLE_ID,
                moderator_role_id=settings.DISCORD_MODERATOR_ROLE_ID,
                support_role_id=settings.DISCORD_SUPPORT_ROLE_ID,
            )

            discord_service = get_discord_service()
            await discord_service.initialize(discord_config)

            # Start Discord bot in background
            asyncio.create_task(discord_service.start())
            logger.info("Discord bot started successfully")

        except Exception as e:
            logger.error(f"Failed to start Discord bot: {e}")
    else:
        logger.info("Discord bot not configured - skipping Discord integration")

    # Yield control to FastAPI
    yield

    # Shutdown: Clean up resources
    logger.info(f"{settings.PROJECT_NAME} backend shutting down...")

    # Clean up temporary files
    logger.info("Cleaning up temporary files...")
    # TODO: Implement cleanup logic using settings.TEMP_DIR, settings.UPLOAD_DIR, settings.EPHEMERAL_STORAGE_PATH
    # Consider using a background task for cleanup


# Initialize FastAPI app with metadata and lifespan
app = FastAPI(
    title=settings.PROJECT_NAME + " API",
    description="""
    ChatChonk transforms AI chat conversations into structured, searchable knowledge bundles.

    "Tame the Chatter. Find the Signal."

    Designed for second-brain builders and neurodivergent thinkers.
    """,
    version=settings.APP_VERSION,
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
    root_path=settings.ROOT_PATH,  # Apply root path if configured
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add GZip compression
app.add_middleware(GZipMiddleware, minimum_size=1000)


# Request logging and metrics middleware
@app.middleware("http")
async def log_and_metric_requests(request: Request, call_next: Callable) -> Response:
    """Log request information, timing, and collect basic metrics."""
    start_time = time.time()

    # Generate request ID
    request_id = f"req_{int(start_time * 1000)}"
    logger.info(f"[{request_id}] {request.method} {request.url.path}")

    # Increment total requests
    metrics["total_requests"] += 1
    metrics["request_counts_by_path"][request.url.path] += 1

    # Process the request
    try:
        response = await call_next(request)
        process_time = time.time() - start_time

        metrics["total_processing_time"] += process_time
        metrics["status_code_counts"][response.status_code] += 1

        if response.status_code >= 400:
            metrics["error_requests"] += 1
            metrics["error_counts_by_path"][request.url.path] += 1
            logger.warning(
                f"[{request_id}] Completed with error: {response.status_code} ({process_time:.4f}s)"
            )
        else:
            metrics["successful_requests"] += 1
            logger.info(
                f"[{request_id}] Completed: {response.status_code} ({process_time:.4f}s)"
            )

        # Add timing header
        response.headers["X-Process-Time"] = f"{process_time:.4f}"
        return response
    except Exception as e:
        metrics["error_requests"] += 1
        metrics["error_counts_by_path"][request.url.path] += 1
        logger.error(f"[{request_id}] Request failed: {str(e)}")
        raise


# Custom exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors with user-friendly messages."""
    metrics["error_requests"] += 1  # Count validation errors as errors
    metrics["error_counts_by_path"][request.url.path] += 1
    metrics["status_code_counts"][status.HTTP_422_UNPROCESSABLE_ENTITY] += 1
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Invalid request data. Please check your input.",
            "errors": exc.errors(),
        },
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Custom HTTP exception handler with consistent format."""
    metrics["error_requests"] += 1  # Count HTTP exceptions as errors
    metrics["error_counts_by_path"][request.url.path] += 1
    metrics["status_code_counts"][exc.status_code] += 1
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected errors gracefully."""
    metrics["error_requests"] += 1  # Count general exceptions as errors
    metrics["error_counts_by_path"][request.url.path] += 1
    metrics["status_code_counts"][status.HTTP_500_INTERNAL_SERVER_ERROR] += 1
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An unexpected error occurred. Please try again later."},
    )


# Health check endpoint
@app.get("/health", tags=["System"])
async def health_check():
    """Health check endpoint for monitoring."""
    return {
        "status": "ok",
        "service": "chatchonk-api",
        "version": "0.1.0",
        "environment": "production",
        "debug_mode": False,
    }


# Simple root endpoint
@app.get("/", tags=["System"])
async def root():
    """Root endpoint."""
    return {"message": "ChatChonk API is running", "status": "ok"}


# Import and include API routers
try:
    # ModelSwapper router - handles model configuration and selection
    from app.api.routes.modelswapper import router as modelswapper_router

    app.include_router(modelswapper_router, prefix=settings.API_V1_STR)
    logger.info("ModelSwapper router loaded successfully")
except Exception as e:
    logger.warning(f"Could not load ModelSwapper router: {e}")

# Simple API router for basic endpoints
api_router = APIRouter(prefix="/api", tags=["API"])


@api_router.get("/status")
async def api_status():
    """API status endpoint."""
    return {"status": "ok", "message": "ChatChonk API is operational"}


@api_router.get("/metrics", tags=["System"])
async def get_metrics():
    """
    Exposes basic application metrics.
    NOTE: These are in-memory metrics and will reset on application restart.
    For production, use a dedicated metrics system (e.g., Prometheus).
    """
    avg_processing_time = (
        metrics["total_processing_time"] / metrics["total_requests"]
        if metrics["total_requests"] > 0
        else 0
    )
    return {
        "total_requests": metrics["total_requests"],
        "successful_requests": metrics["successful_requests"],
        "error_requests": metrics["error_requests"],
        "average_processing_time_seconds": f"{avg_processing_time:.4f}",
        "request_counts_by_path": dict(metrics["request_counts_by_path"]),
        "error_counts_by_path": dict(metrics["error_counts_by_path"]),
        "status_code_counts": dict(metrics["status_code_counts"]),
    }


app.include_router(api_router)

# TODO: Add other routers as they are implemented and tested
# Files, Templates, Exports, AI routers will be added incrementally

# Mount frontend static files (serve frontend from backend)
try:
    app.mount("/", StaticFiles(directory="frontend_build", html=True), name="frontend")
    logger.info("Frontend static files mounted successfully")
except Exception as e:
    logger.warning(f"Could not mount frontend static files: {e}")
    logger.info("Frontend will need to be deployed separately")


# Run the application if executed directly
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.RELOAD,
        log_level=settings.LOG_LEVEL.value.lower(),
    )
