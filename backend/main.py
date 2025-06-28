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
import os
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi.routing import APIRouter
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from fastapi.responses import StreamingResponse
from fastapi import Depends
import traceback

# Import the AutoModel class and ProcessRequest model
from backend.app.automodel.automodel import AutoModel, ProcessRequest
# Import new coach-related services
from backend.app.services.coach_service import CoachService
from backend.app.services.persona_service import PersonaService
from backend.app.services.tts_service import TtsService
from backend.app.services.auth_service import get_current_user

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

# --------------------------------------------------------------------------- #
# Instantiate global service singletons
# --------------------------------------------------------------------------- #
coach_service = CoachService()
persona_service = PersonaService()
tts_service = TtsService()

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
    logger.info("Initializing AI models...")
    await AutoModel.initialize()

    # Initialize persona, TTS, and coach services
    logger.info("Initializing Persona, TTS and Coach services...")
    await persona_service.initialize()
    await tts_service.initialize()
    await coach_service.initialize()
    
    # Yield control to FastAPI
    yield
    
    # Shutdown: Clean up resources
    logger.info(f"{settings.PROJECT_NAME} backend shutting down...")
    
    # Shutdown AutoModel system
    await AutoModel.shutdown()
    
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

# Mount the static files directory
app.mount("/static", StaticFiles(directory=settings.STATIC_FILES_DIR), name="static")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    # Restrict origins to trusted frontend domains only
    allow_origins=[
        "http://localhost:3000",
        "https://chatchonkbeta.onrender.com",
    ],
    allow_credentials=True,
    # Restrict allowed HTTP methods
    allow_methods=["GET", "POST", "PUT", "DELETE"],
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
    # If DEBUG is enabled, include the exception details for easier debugging.
    # Otherwise, return a generic error message to avoid leaking sensitive data.
    if settings.DEBUG:
        error_detail = {
            "detail": str(exc),
            "traceback": traceback.format_exc(limit=5)  # limit to keep response size manageable
        }
    else:
        error_detail = {
            "detail": "An unexpected error occurred. Please try again later."
        }

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_detail,
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

from prometheus_fastapi_instrumentator import Instrumentator
from prometheus_client import push_to_gateway

instrumentator = Instrumentator()
instrumentator.instrument(app)

GRAFANA_CLOUD_ENDPOINT = os.environ.get("GRAFANA_CLOUD_ENDPOINT")
GRAFANA_CLOUD_API_KEY = os.environ.get("GRAFANA_CLOUD_API_KEY")
PROMETHEUS_PUSH_GATEWAY = GRAFANA_CLOUD_ENDPOINT  # Replace with your Grafana Cloud Prometheus remote write endpoint

@app.get("/metrics")
async def metrics():
    return instrumentator.expose()

# Push metrics to Grafana Cloud
@app.on_event("shutdown")
def push_metrics():
    try:
        push_to_gateway(
            PROMETHEUS_PUSH_GATEWAY,
            job="chatchonk-backend",  # Replace with your job name
            gateway_kwargs={
                "headers": {
                    "Authorization": f"Basic {GRAFANA_CLOUD_API_KEY}"  # Replace with your Grafana Cloud API key
                }
            },
        )
        print("Successfully pushed metrics to Grafana Cloud")
    except Exception as e:
        print(f"Failed to push metrics to Grafana Cloud: {e}")


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

# --------------------------------------------------------------------------- #
# Coach router – handles voice/text coach interactions
# --------------------------------------------------------------------------- #

class CoachRequest(BaseModel):
    """Request model for interacting with Sara the coach."""
    user_id: str
    text_input: str = Field(..., max_length=10000)
    session_id: Optional[str] = None

# Coach router
coach_router = APIRouter(prefix=f"{settings.API_V1_STR}/coach", tags=["Coach"])


@coach_router.post("/", response_class=StreamingResponse)
async def interact_with_coach(request: CoachRequest):
    """
    Stream audio response from the AI coach (Sara).
    The endpoint returns an audio/mpeg stream generated via Kokoro TTS.
    The full text reply is sent back in the `X-Coach-Text` response header.
    """
    try:
        reply_text = await coach_service.handle_request(
            user_id=request.user_id,
            text_input=request.text_input,
            session_id=request.session_id,
        )
        # Determine voice to use (default persona for now)
        persona = await persona_service.get_persona("sara_default")
        voice_id = persona.get("voice_config", {}).get("voice_id", "af_bella")

        # Stream TTS audio
        audio_iterator = tts_service.stream_speech(
            text=reply_text,
            voice_id=voice_id,
        )
        headers = {"X-Coach-Text": reply_text}
        return StreamingResponse(audio_iterator, media_type="audio/mpeg", headers=headers)
    except Exception as e:
        logger.error(f"Coach interaction failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process coach interaction.",
        )

# Include the Coach router
app.include_router(coach_router)

# Define the request model for template processing
class TemplateProcessRequest(BaseModel):
    """Request model for processing a conversation with a template."""
    conversation_content: str = Field(..., max_length=10000)
    template_id: str

# AI router - handles AI processing
ai_router = APIRouter(prefix=f"{settings.API_V1_STR}/ai", tags=["AI"])

# Add the template processing endpoint to the AI router
@ai_router.post("/process-template", response_model=dict)
async def process_template(
    request: TemplateProcessRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Process a conversation using a specified template.
    
    Args:
        request: TemplateProcessRequest containing conversation content and template ID
        
    Returns:
        Processed conversation with the template applied
    """
    try:
        # Process the conversation with the specified template
        result = await AutoModel._apply_template(
            conversation_content=request.conversation_content,
            template_id=request.template_id
        )
        
        # Return the processed result
        return {"result": result}
        
    except FileNotFoundError as e:
        # Handle case where template doesn't exist
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template not found: {request.template_id}"
        )
        
    except ValueError as e:
        # Handle invalid template format or processing errors
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

# Include the AI router in the app
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
