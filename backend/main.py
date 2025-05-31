"""
ChatChonk - Main FastAPI Application Entry Point

This module initializes the FastAPI application with all necessary middleware,
routers, and configuration for the ChatChonk backend.

Author: Rip Jonesy
"""

import logging
import os
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Callable, Dict, List, Optional, Union

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request, Response, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi.routing import APIRouter

# Load environment variables from .env file
load_dotenv()

# Import application settings
from backend.app.core.config import settings

# Configure logging
logging.basicConfig(
    level=settings.LOG_LEVEL.value,
    format=settings.LOG_FORMAT,
)
logger = logging.getLogger("chatchonk")

# Create necessary directories using settings
settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
settings.TEMP_DIR.mkdir(parents=True, exist_ok=True)
settings.EXPORT_DIR.mkdir(parents=True, exist_ok=True) # Ensure export directory exists
settings.STORAGE_PATH.mkdir(parents=True, exist_ok=True) # Ensure general storage exists
settings.EPHEMERAL_STORAGE_PATH.mkdir(parents=True, exist_ok=True) # Ensure ephemeral storage exists


# App lifecycle management
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application startup and shutdown events.
    Creates necessary directories and initializes resources.
    """
    # Startup: Initialize resources
    logger.info(f"{settings.PROJECT_NAME} backend starting up in {settings.ENVIRONMENT.value} environment...")
    
    # Initialize AutoModel system
    # This will be implemented in a separate module
    logger.info("Initializing AI models...")
    
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
    root_path=settings.ROOT_PATH, # Apply root path if configured
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


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next: Callable) -> Response:
    """Log request information and timing."""
    start_time = time.time()
    
    # Generate request ID
    request_id = f"req_{int(start_time * 1000)}"
    logger.info(f"[{request_id}] {request.method} {request.url.path}")
    
    # Process the request
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        logger.info(
            f"[{request_id}] Completed: {response.status_code} ({process_time:.4f}s)"
        )
        # Add timing header
        response.headers["X-Process-Time"] = f"{process_time:.4f}"
        return response
    except Exception as e:
        logger.error(f"[{request_id}] Request failed: {str(e)}")
        raise


# Custom exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors with user-friendly messages."""
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
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected errors gracefully."""
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
        "service": settings.PROJECT_NAME.lower().replace(" ", "-") + "-api",
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT.value,
        "debug_mode": settings.DEBUG,
    }


# Import and include API routers
# These will be implemented in separate modules

# Files router - handles file uploads and processing
files_router = APIRouter(prefix=f"{settings.API_V1_STR}/files", tags=["Files"])
# TODO: Implement file upload endpoints with 2GB limit
app.include_router(files_router)

# Templates router - handles template management
templates_router = APIRouter(prefix=f"{settings.API_V1_STR}/templates", tags=["Templates"])
# TODO: Implement template endpoints
app.include_router(templates_router)

# Export router - handles export generation
exports_router = APIRouter(prefix=f"{settings.API_V1_STR}/exports", tags=["Exports"])
# TODO: Implement export endpoints
app.include_router(exports_router)

# AI router - handles AI processing
ai_router = APIRouter(prefix=f"{settings.API_V1_STR}/ai", tags=["AI"])
# TODO: Implement AI endpoints
app.include_router(ai_router)


# Run the application if executed directly
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.RELOAD,
        log_level=settings.LOG_LEVEL.value.lower(),
    )
