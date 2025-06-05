"""
ChatChonk - Minimal FastAPI Application for Initial Deployment

This is a simplified version to get the app running on Render quickly.
Complex features will be added incrementally.
"""

import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi.routing import APIRouter

# Configure basic logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("chatchonk")

# Directory creation will be handled in startup event


# App lifecycle management
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application startup and shutdown events."""
    logger.info("ChatChonk backend starting up...")
    logger.info("Minimal mode - skipping directory creation")
    yield
    logger.info("ChatChonk backend shutting down...")


# Initialize FastAPI app
app = FastAPI(
    title="ChatChonk API",
    description="ChatChonk transforms AI chat conversations into structured, searchable knowledge bundles.",
    version="0.1.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add GZip compression
app.add_middleware(GZipMiddleware, minimum_size=1000)


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next) -> Response:
    """Log request information and timing."""
    start_time = time.time()
    request_id = f"req_{int(start_time * 1000)}"
    logger.info(f"[{request_id}] {request.method} {request.url.path}")

    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        logger.info(
            f"[{request_id}] Completed: {response.status_code} ({process_time:.4f}s)"
        )
        response.headers["X-Process-Time"] = f"{process_time:.4f}"
        return response
    except Exception as e:
        logger.error(f"[{request_id}] Request failed: {str(e)}")
        raise


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "ChatChonk API is running", "status": "ok"}


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    return {
        "status": "ok",
        "service": "chatchonk-api",
        "version": "0.1.0",
        "environment": "production",
    }


# API router
api_router = APIRouter(prefix="/api", tags=["API"])


@api_router.get("/status")
async def api_status():
    """API status endpoint."""
    return {"status": "ok", "message": "ChatChonk API is operational"}


@api_router.get("/info")
async def api_info():
    """API information endpoint."""
    return {
        "name": "ChatChonk API",
        "version": "0.1.0",
        "description": "Tame the Chatter. Find the Signal.",
        "endpoints": {
            "health": "/health",
            "status": "/api/status",
            "docs": "/api/docs",
            "redoc": "/api/redoc",
        },
    }


app.include_router(api_router)


# Exception handlers
@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected errors gracefully."""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected error occurred. Please try again later."},
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main_minimal:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info",
    )
