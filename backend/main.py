"""
ChatChonk - Main FastAPI Application Entry Point

This module initializes the FastAPI application with all necessary middleware,
routers, and configuration for the ChatChonk backend.

Author: Rip Jonesy
"""

import asyncio
import logging
import os
import platform
import time
import logging.config
from contextlib import asynccontextmanager, ContextDecorator
from pathlib import Path
from typing import Callable, Dict, List, Optional, Union
import uuid
from contextvars import ContextVar

import uvicorn  # Ensure uvicorn is installed: pip install uvicorn
from fastapi import FastAPI, HTTPException, Request, Response, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi.routing import APIRouter
from fastapi.staticfiles import StaticFiles  # Ensure fastapi is installed: pip install fastapi
from collections import defaultdict

# TraceID for correlating logs
trace_id_ctx_var = ContextVar("trace_id", default="")


class TraceID(ContextDecorator):
    """Context manager for handling trace IDs in logs"""

    def __enter__(self):
        self.token = trace_id_ctx_var.set(str(uuid.uuid4()))
        return self

    def __exit__(self, *exc):
        trace_id_ctx_var.reset(self.token)
        return False


# Add trace ID to log records
def trace_id_filter(record):
    """Add trace_id to log records"""
    record.trace_id = trace_id_ctx_var.get()
    return True


# Import application settings
from app.core.config import settings  # Import using relative path
logging.basicConfig(
    level=settings.LOG_LEVEL.value,
    format=settings.LOG_FORMAT,
)

# Configure detailed logging for better observability
log_config = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "detailed": {
            "format": "[%(asctime)s] %(levelname)s [%(name)s:%(filename)s:%(lineno)d] [trace_id=%(trace_id)s] - %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S %z",
        }
    },
    "filters": {
        "trace_id_filter": {
            "()": "logging.Filter",
            "name": "trace_id_filter"
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "detailed",
            "filters": ["trace_id_filter"]
        }
    },
    "root": {
        "level": settings.LOG_LEVEL.value,
        "handlers": ["console"]
    },
    "loggers": {
        "chatchonk": {
            "level": settings.LOG_LEVEL.value,
            "handlers": ["console"],
            "propagate": False,
        },
        "uvicorn": {
            "level": settings.LOG_LEVEL.value,
            "handlers": ["console"],
            "propagate": False,
        },
        "fastapi": {
            "level": settings.LOG_LEVEL.value,
            "handlers": ["console"],
            "propagate": False,
        }
    }
}

logging.config.dictConfig(log_config)
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
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
    root_path=settings.ROOT_PATH,  # Apply root path if configured
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
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

    with TraceID() as trace:
        # Log request details with structured data
        logger.info(
            "Request started",
            extra={
                "http_method": request.method,
                "path": request.url.path,
                "client_host": request.client.host if request.client else "unknown",
                "user_agent": request.headers.get("user-agent", "unknown"),
                "query_params": str(request.query_params),
                "trace_id": trace_id_ctx_var.get()
            }
        )

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
                "Request completed with error",
                extra={
                    "status_code": response.status_code,
                    "process_time": f"{process_time:.4f}s",
                    "path": request.url.path,
                    "trace_id": trace_id_ctx_var.get()
                }
            )
        else:
            metrics["successful_requests"] += 1
            logger.info(
                "Request completed successfully",
                extra={
                    "status_code": response.status_code,
                    "process_time": f"{process_time:.4f}s",
                    "path": request.url.path,
                    "trace_id": trace_id_ctx_var.get()
                }
            )

        # Add timing and tracing headers
        response.headers["X-Process-Time"] = f"{process_time:.4f}"
        response.headers["X-Trace-ID"] = trace_id_ctx_var.get()
        return response
    except Exception as e:
        metrics["error_requests"] += 1
        metrics["error_counts_by_path"][request.url.path] += 1
        logger.error(
            "Request failed with unhandled exception",
            extra={
                "error": str(e),
                "error_type": type(e).__name__,
                "path": request.url.path,
                "trace_id": trace_id_ctx_var.get()
            },
            exc_info=True
        )
        raise


# Custom exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors with user-friendly messages."""
    metrics["error_requests"] += 1  # Count validation errors as errors
    metrics["error_counts_by_path"][request.url.path] += 1
    metrics["status_code_counts"][status.HTTP_422_UNPROCESSABLE_ENTITY] += 1
    
    logger.warning(
        "Request validation failed",
        extra={
            "path": request.url.path,
            "method": request.method,
            "validation_errors": exc.errors(),
            "trace_id": trace_id_ctx_var.get()
        }
    )
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Invalid request data. Please check your input.",
            "errors": exc.errors(),
            "trace_id": trace_id_ctx_var.get()
        },
        headers={"X-Trace-ID": trace_id_ctx_var.get()}
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Custom HTTP exception handler with consistent format."""
    metrics["error_requests"] += 1  # Count HTTP exceptions as errors
    metrics["error_counts_by_path"][request.url.path] += 1
    metrics["status_code_counts"][exc.status_code] += 1
    
    logger.warning(
        "HTTP exception occurred",
        extra={
            "status_code": exc.status_code,
            "error_detail": exc.detail,
            "path": request.url.path,
            "method": request.method,
            "trace_id": trace_id_ctx_var.get()
        }
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "trace_id": trace_id_ctx_var.get()
        },
        headers={"X-Trace-ID": trace_id_ctx_var.get()}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected errors gracefully."""
    metrics["error_requests"] += 1  # Count general exceptions as errors
    metrics["error_counts_by_path"][request.url.path] += 1
    metrics["status_code_counts"][status.HTTP_500_INTERNAL_SERVER_ERROR] += 1
    
    logger.error(
        "Unhandled exception occurred",
        extra={
            "error_type": type(exc).__name__,
            "error_message": str(exc),
            "path": request.url.path,
            "method": request.method,
            "trace_id": trace_id_ctx_var.get()
        },
        exc_info=True
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "An unexpected error occurred. Please try again later.",
            "trace_id": trace_id_ctx_var.get()
        },
        headers={"X-Trace-ID": trace_id_ctx_var.get()}
    )


# Health check endpoint
@app.get("/health", tags=["System"])
async def health_check():
    """Health check endpoint for monitoring with detailed diagnostic information."""
    health_info = {
        "status": "ok",
        "service": "chatchonk-api",
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "debug_mode": settings.DEBUG,
        "system_info": {
            "python_version": platform.python_version(),
            "platform": platform.platform(),
        },
        "settings": {
            "host": settings.HOST,
            "port": settings.PORT,
            "root_path": settings.ROOT_PATH,
            "allowed_origins": settings.allowed_origins_list,
            "log_level": settings.LOG_LEVEL.value,
        },
        "resources": {
            "frontend_build": str(Path("frontend_build").absolute()),
            "static_dirs": {
                "_next": Path("frontend_build/_next").exists(),
                "admin": Path("frontend_build/admin").exists(),
                "images": Path("frontend_build/images").exists(),
                "icons": Path("frontend_build/icons").exists(),
            }
        },
        "metrics": {
            "total_requests": metrics["total_requests"],
            "successful_requests": metrics["successful_requests"],
            "error_requests": metrics["error_requests"],
            "status_codes": dict(metrics["status_code_counts"]),
        }
    }
    return health_info


# Simple API router for basic endpoints
api_router = APIRouter(prefix="/api", tags=["API"])

@api_router.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    return {
        "status": "ok",
        "service": "chatchonk-api",
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
    }

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

# Configure and mount frontend static files
def configure_static_files(app: FastAPI) -> None:
    try:
        # Use absolute path instead of relative path
        frontend_dir = Path("C:/DEV/DEV_PROJECTS/B15B_CHATCHONK7/frontend_build")
        logger.info(f"[STATIC_FILES] Looking for frontend build at: {frontend_dir}")
        
        if not frontend_dir.exists():
            logger.error(f"[STATIC_FILES] Frontend build directory not found at: {frontend_dir}")
            raise FileNotFoundError(f"Frontend build directory not found at: {frontend_dir}")

        logger.info(f"[STATIC_FILES] Found frontend build directory at: {frontend_dir}")
        logger.info("[STATIC_FILES] Frontend build contents:")
        for item in frontend_dir.iterdir():
            logger.info(f"[STATIC_FILES] - {item.name}")

        # First mount API router before any static files
        logger.info("Mounting API router at /api")
        app.include_router(api_router)
        
        # Then mount specific static directories
        static_mounts = {
            "/_next/static": frontend_dir / "_next" / "static",
            "/admin": frontend_dir / "admin",
            "/images": frontend_dir / "images",
            "/icons": frontend_dir / "icons",
        }

        for path, directory in static_mounts.items():
            if directory.exists():
                logger.info(f"[STATIC_FILES] Mounting {path} from {directory}")
                app.mount(path, StaticFiles(directory=str(directory), html=True), name=path.strip("/").replace("/", "-"))
                logger.info(f"[STATIC_FILES] Successfully mounted {path}")
            else:
                logger.warning(f"[STATIC_FILES] Directory not found: {directory}")

        # Mount root directory last to handle all other paths
        logger.info("[STATIC_FILES] Mounting root directory")
        root_files = StaticFiles(directory=str(frontend_dir), html=True)
        app.mount("/", root_files, name="frontend")
        logger.info("[STATIC_FILES] Mounted root directory")

    except Exception as e:
        logger.error(f"[STATIC_FILES] Error configuring static files: {str(e)}")
        raise

# Configure static files
try:
    logger.info("[STATIC_FILES] Configuring static files...")
    configure_static_files(app)
    logger.info("[STATIC_FILES] Static file configuration complete")
except Exception as e:
    logger.error(f"[STATIC_FILES] Failed to mount frontend static files: {str(e)}")
    logger.warning("If running in development mode, make sure to run build_and_copy_frontend.ps1 first")
    logger.info("Frontend will need to be served separately if not mounted")
    raise  # Re-raise the exception to ensure the server doesn't start with missing static files


# Run the application if executed directly
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.RELOAD,
        log_level=settings.LOG_LEVEL.value.lower(),
    )
