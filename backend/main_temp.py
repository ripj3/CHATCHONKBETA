"""
ChatChonk - Main FastAPI Application Entry Point (Temporary)

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
from app.core.config import settings

# Configure logging
logging.basicConfig(
    level=settings.LOG_LEVEL.value,
    format=settings.LOG_FORMAT,
)
logger = logging.getLogger("chatchonk")

# In-memory metrics storage
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
    """Manage application startup and shutdown events."""
    logger.info("ChatChonk backend starting up...")
    yield
    logger.info("Shutting down...")

# Initialize FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME + " API",
    description="ChatChonk transforms AI chat conversations into structured, searchable knowledge bundles.",
    version=settings.APP_VERSION,
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
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

# Create API router
api_router = APIRouter()

# Mount frontend static files (serve frontend from backend)
try:
    # Mount Next.js static assets
    app.mount("/_next", StaticFiles(directory="frontend_build/_next"), name="next-static")
    # Mount other static asset directories if they exist
    if os.path.exists("frontend_build/images"):
        app.mount("/images", StaticFiles(directory="frontend_build/images"), name="images")
    if os.path.exists("frontend_build/icons"):
        app.mount("/icons", StaticFiles(directory="frontend_build/icons"), name="icons")
    # Mount the root directory last for index.html and other pages
    app.mount("/", StaticFiles(directory="frontend_build", html=True), name="frontend")
    logger.info("Frontend static files mounted successfully")
except Exception as e:
    logger.error(f"Could not mount frontend static files: {e}")
    logger.warning("If running in development mode, make sure to run build_and_copy_frontend.ps1 first")
    logger.info("Frontend will need to be served separately if the error persists")

# Include routers
app.include_router(api_router)

# Run the application
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.RELOAD,
        log_level=settings.LOG_LEVEL.value.lower(),
    )
