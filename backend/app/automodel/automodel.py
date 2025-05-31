"""
AutoModel - Main AI Model Interface

This module provides the primary AutoModel class that serves as the unified interface
for all AI processing in ChatChonk. It abstracts away the complexity of multiple
providers, model selection, and task routing to provide a simple, consistent API.

Author: Rip Jonesy
"""

import asyncio
import functools
import logging
import time
import uuid
from datetime import datetime
from functools import lru_cache
from typing import Any, Dict, List, Optional, Tuple, Union, cast

from pydantic import BaseModel, Field, ValidationError

from app.core.config import get_settings
from app.services.cache_service import CacheService

from .model_registry import ModelRegistry
from .providers.base import BaseProvider, ProviderResponse
from .task_router import TaskRouter
from . import (
    TaskType,
    ProviderType,
    ModelPriority,
    AutoModelError,
    ProviderNotAvailableError,
    ModelNotFoundError,
    TaskNotSupportedError,
    ProviderApiError,
    ProcessingError,
)

# Configure logging
logger = logging.getLogger("chatchonk.automodel")


# === Request/Response Models ===
class ProcessRequest(BaseModel):
    """Model for AI processing requests."""
    
    task_type: TaskType
    content: Union[str, Dict[str, Any], List[Dict[str, Any]]]
    provider: Optional[ProviderType] = None
    model_id: Optional[str] = None
    max_tokens: Optional[int] = None
    temperature: Optional[float] = 0.7
    top_p: Optional[float] = 0.95
    frequency_penalty: Optional[float] = 0.0
    presence_penalty: Optional[float] = 0.0
    stop_sequences: Optional[List[str]] = None
    session_id: Optional[str] = None
    template_id: Optional[str] = None
    template_vars: Optional[Dict[str, Any]] = None
    priority: ModelPriority = ModelPriority.MEDIUM
    cache_key: Optional[str] = None
    use_cache: bool = True
    metadata: Optional[Dict[str, Any]] = None


class ProcessResponse(BaseModel):
    """Model for AI processing responses."""
    
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    task_type: TaskType
    provider: ProviderType
    model_id: str
    content: Union[str, Dict[str, Any], List[Dict[str, Any]]]
    tokens_used: Optional[int] = None
    processing_time: float
    cached: bool = False
    session_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class PerformanceMetrics(BaseModel):
    """Model for tracking AI model performance."""
    
    provider: ProviderType
    model_id: str
    task_type: TaskType
    success: bool
    processing_time: float
    tokens_used: Optional[int] = None
    error: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# === AutoModel Class ===
class AutoModel:
    """
    Unified interface for AI processing across multiple providers.
    
    This class provides a simple, consistent API for all AI tasks in ChatChonk,
    handling the complexity of provider selection, model routing, caching,
    performance tracking, and error handling.
    
    Example:
        ```python
        # Basic usage
        result = await AutoModel.process(
            task_type=TaskType.SUMMARIZATION,
            content="Your long text to summarize...",
        )
        
        # Advanced usage with specific model
        result = await AutoModel.process(
            task_type=TaskType.TOPIC_EXTRACTION,
            content="Your chat log content...",
            provider=ProviderType.ANTHROPIC,
            model_id="claude-3-opus-20240229",
            max_tokens=2000,
            temperature=0.7,
        )
        ```
    """
    
    # Class-level storage for initialization state
    _initialized: bool = False
    _model_registry: Optional[ModelRegistry] = None
    _task_router: Optional[TaskRouter] = None
    _cache_service: Optional[CacheService] = None
    _active_sessions: Dict[str, Dict[str, Any]] = {}
    _performance_metrics: List[PerformanceMetrics] = []
    
    @classmethod
    async def initialize(cls) -> None:
        """
        Initialize the AutoModel system.
        
        This method sets up the model registry, task router, and cache service.
        It should be called during application startup.
        """
        if cls._initialized:
            return
        
        logger.info("Initializing AutoModel system...")
        
        # Initialize model registry
        cls._model_registry = ModelRegistry()
        await cls._model_registry.initialize()
        
        # Initialize task router
        cls._task_router = TaskRouter(cls._model_registry)
        
        # Initialize cache service
        settings = get_settings()
        cls._cache_service = CacheService()
        
        # Mark as initialized
        cls._initialized = True
        logger.info("AutoModel system initialized successfully")
    
    @classmethod
    async def shutdown(cls) -> None:
        """
        Shutdown the AutoModel system.
        
        This method cleans up resources and should be called during application shutdown.
        """
        if not cls._initialized:
            return
        
        logger.info("Shutting down AutoModel system...")
        
        # Clean up active sessions
        cls._active_sessions.clear()
        
        # Clean up model registry
        if cls._model_registry:
            await cls._model_registry.shutdown()
        
        # Clean up cache service
        if cls._cache_service:
            await cls._cache_service.close()
        
        # Mark as uninitialized
        cls._initialized = False
        logger.info("AutoModel system shut down successfully")
    
    @classmethod
    async def ensure_initialized(cls) -> None:
        """Ensure the AutoModel system is initialized."""
        if not cls._initialized:
            await cls.initialize()
    
    @classmethod
    async def process(
        cls,
        task_type: TaskType,
        content: Union[str, Dict[str, Any], List[Dict[str, Any]]],
        provider: Optional[ProviderType] = None,
        model_id: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = 0.7,
        top_p: Optional[float] = 0.95,
        frequency_penalty: Optional[float] = 0.0,
        presence_penalty: Optional[float] = 0.0,
        stop_sequences: Optional[List[str]] = None,
        session_id: Optional[str] = None,
        template_id: Optional[str] = None,
        template_vars: Optional[Dict[str, Any]] = None,
        priority: ModelPriority = ModelPriority.MEDIUM,
        cache_key: Optional[str] = None,
        use_cache: bool = True,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ProcessResponse:
        """
        Process content using AI models.
        
        This is the main method for all AI processing in ChatChonk. It handles
        provider selection, model routing, caching, and error handling.
        
        Args:
            task_type: Type of AI task to perform
            content: Content to process (text, dict, or list)
            provider: Optional specific provider to use
            model_id: Optional specific model ID to use
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0.0-1.0)
            top_p: Nucleus sampling parameter (0.0-1.0)
            frequency_penalty: Frequency penalty (0.0-2.0)
            presence_penalty: Presence penalty (0.0-2.0)
            stop_sequences: Sequences to stop generation
            session_id: Optional session ID for multi-turn conversations
            template_id: Optional template ID for structured outputs
            template_vars: Optional variables for template rendering
            priority: Priority level for model selection
            cache_key: Optional custom cache key
            use_cache: Whether to use cache for this request
            metadata: Optional additional metadata
        
        Returns:
            ProcessResponse: The processed result
        
        Raises:
            AutoModelError: Base class for all AutoModel errors
            ProviderNotAvailableError: When a requested provider is not available
            ModelNotFoundError: When a requested model is not found
            TaskNotSupportedError: When a task is not supported by the selected model
            ProviderApiError: When there's an error from the provider's API
            ProcessingError: When there's an error during processing
        """
        # Ensure system is initialized
        await cls.ensure_initialized()
        
        # Create request object
        request = ProcessRequest(
            task_type=task_type,
            content=content,
            provider=provider,
            model_id=model_id,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            frequency_penalty=frequency_penalty,
            presence_penalty=presence_penalty,
            stop_sequences=stop_sequences,
            session_id=session_id,
            template_id=template_id,
            template_vars=template_vars,
            priority=priority,
            cache_key=cache_key,
            use_cache=use_cache,
            metadata=metadata or {},
        )
        
        # Generate request ID
        request_id = str(uuid.uuid4())
        logger.info(f"Processing request {request_id} for task {task_type}")
        
        # Try to get from cache if enabled
        if use_cache and cls._cache_service:
            cache_result = await cls._try_cache(request)
            if cache_result:
                logger.info(f"Cache hit for request {request_id}")
                return cache_result
        
        # Start timing
        start_time = time.time()
        
        try:
            # Get session context if session_id is provided
            session_context = cls._get_session_context(session_id) if session_id else None
            
            # Apply template if template_id is provided
            if template_id:
                content = await cls._apply_template(template_id, content, template_vars)
            
            # Route to appropriate provider and model
            provider_instance, model = await cls._route_request(request)
            
            # Process the request
            provider_response = await provider_instance.process(
                task_type=task_type,
                model_id=model.id,
                content=content,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                frequency_penalty=frequency_penalty,
                presence_penalty=presence_penalty,
                stop_sequences=stop_sequences,
                session_context=session_context,
            )
            
            # Update session context if session_id is provided
            if session_id and provider_response.session_context:
                cls._update_session_context(session_id, provider_response.session_context)
            
            # Calculate processing time
            processing_time = time.time() - start_time
            
            # Create response
            response = ProcessResponse(
                request_id=request_id,
                task_type=task_type,
                provider=provider_instance.provider_type,
                model_id=model.id,
                content=provider_response.content,
                tokens_used=provider_response.tokens_used,
                processing_time=processing_time,
                cached=False,
                session_id=session_id,
                metadata=metadata,
            )
            
            # Cache the response if caching is enabled
            if use_cache and cls._cache_service:
                await cls._cache_response(request, response)
            
            # Track performance metrics
            cls._track_performance(
                provider=provider_instance.provider_type,
                model_id=model.id,
                task_type=task_type,
                success=True,
                processing_time=processing_time,
                tokens_used=provider_response.tokens_used,
            )
            
            logger.info(
                f"Request {request_id} processed successfully in {processing_time:.2f}s "
                f"using {provider_instance.provider_type}/{model.id}"
            )
            
            return response
            
        except Exception as e:
            # Calculate processing time for failed requests
            processing_time = time.time() - start_time
            
            # Track performance metrics for failed requests
            if provider and model_id:
                cls._track_performance(
                    provider=provider,
                    model_id=model_id,
                    task_type=task_type,
                    success=False,
                    processing_time=processing_time,
                    error=str(e),
                )
            
            # Log the error
            logger.error(f"Error processing request {request_id}: {str(e)}", exc_info=True)
            
            # Handle different error types
            if isinstance(e, (ProviderNotAvailableError, ModelNotFoundError, TaskNotSupportedError)):
                # Try fallback if specific provider/model was requested but not available
                if (provider or model_id) and not getattr(request, "is_fallback", False):
                    logger.info(f"Attempting fallback for request {request_id}")
                    fallback_request = request.copy()
                    fallback_request.provider = None
                    fallback_request.model_id = None
                    fallback_request.is_fallback = True  # Mark as fallback to prevent infinite recursion
                    try:
                        return await cls.process(**fallback_request.dict(exclude={"is_fallback"}))
                    except Exception as fallback_e:
                        logger.error(f"Fallback failed for request {request_id}: {str(fallback_e)}")
            
            # Re-raise the original exception
            raise
    
    @classmethod
    async def _route_request(
        cls, request: ProcessRequest
    ) -> Tuple[BaseProvider, Any]:
        """
        Route a request to the appropriate provider and model.
        
        Args:
            request: The processing request
        
        Returns:
            Tuple of provider instance and model
        
        Raises:
            ProviderNotAvailableError: When a requested provider is not available
            ModelNotFoundError: When a requested model is not found
            TaskNotSupportedError: When a task is not supported by the selected model
        """
        assert cls._model_registry is not None, "Model registry not initialized"
        assert cls._task_router is not None, "Task router not initialized"
        
        # If specific provider and model are requested, use them
        if request.provider and request.model_id:
            provider = cls._model_registry.get_provider(request.provider)
            if not provider:
                raise ProviderNotAvailableError(f"Provider {request.provider} is not available")
            
            model = provider.get_model(request.model_id)
            if not model:
                raise ModelNotFoundError(f"Model {request.model_id} not found for provider {request.provider}")
            
            if not provider.supports_task(model.id, request.task_type):
                raise TaskNotSupportedError(
                    f"Task {request.task_type} not supported by {request.provider}/{request.model_id}"
                )
            
            return provider, model
        
        # Otherwise, route based on task type and priority
        return cls._task_router.route(
            task_type=request.task_type,
            priority=request.priority,
            content=request.content,
        )
    
    @classmethod
    async def _try_cache(cls, request: ProcessRequest) -> Optional[ProcessResponse]:
        """
        Try to get a response from cache.
        
        Args:
            request: The processing request
        
        Returns:
            Cached response or None if not found
        """
        if not cls._cache_service:
            return None
        
        # Generate cache key if not provided
        cache_key = request.cache_key
        if not cache_key:
            # Create a deterministic cache key from request parameters
            key_parts = [
                str(request.task_type),
                str(request.content) if isinstance(request.content, str) else str(hash(str(request.content))),
                str(request.provider) if request.provider else "",
                str(request.model_id) if request.model_id else "",
                str(request.max_tokens) if request.max_tokens else "",
                str(request.temperature) if request.temperature else "",
                str(request.template_id) if request.template_id else "",
            ]
            cache_key = ":".join(key_parts)
        
        # Try to get from cache
        cached_data = await cls._cache_service.get(f"automodel:{cache_key}")
        if not cached_data:
            return None
        
        try:
            # Create response from cached data
            response = ProcessResponse.parse_raw(cached_data)
            response.cached = True
            return response
        except ValidationError:
            logger.warning(f"Invalid cached data for key {cache_key}")
            return None
    
    @classmethod
    async def _cache_response(cls, request: ProcessRequest, response: ProcessResponse) -> None:
        """
        Cache a response for future use.
        
        Args:
            request: The processing request
            response: The response to cache
        """
        if not cls._cache_service:
            return
        
        # Generate cache key if not provided
        cache_key = request.cache_key
        if not cache_key:
            # Create a deterministic cache key from request parameters
            key_parts = [
                str(request.task_type),
                str(request.content) if isinstance(request.content, str) else str(hash(str(request.content))),
                str(request.provider) if request.provider else "",
                str(request.model_id) if request.model_id else "",
                str(request.max_tokens) if request.max_tokens else "",
                str(request.temperature) if request.temperature else "",
                str(request.template_id) if request.template_id else "",
            ]
            cache_key = ":".join(key_parts)
        
        # Cache the response
        settings = get_settings()
        ttl = settings.CACHE_TTL if hasattr(settings, "CACHE_TTL") else 3600  # Default 1 hour
        await cls._cache_service.set(f"automodel:{cache_key}", response.json(), ttl=ttl)
    
    @classmethod
    def _get_session_context(cls, session_id: str) -> Dict[str, Any]:
        """
        Get context for a chat session.
        
        Args:
            session_id: The session ID
        
        Returns:
            Session context or empty dict if not found
        """
        return cls._active_sessions.get(session_id, {})
    
    @classmethod
    def _update_session_context(cls, session_id: str, context: Dict[str, Any]) -> None:
        """
        Update context for a chat session.
        
        Args:
            session_id: The session ID
            context: The new context
        """
        cls._active_sessions[session_id] = context
    
    @classmethod
    async def create_session(cls) -> str:
        """
        Create a new chat session.
        
        Returns:
            New session ID
        """
        session_id = str(uuid.uuid4())
        cls._active_sessions[session_id] = {}
        return session_id
    
    @classmethod
    async def delete_session(cls, session_id: str) -> None:
        """
        Delete a chat session.
        
        Args:
            session_id: The session ID to delete
        """
        if session_id in cls._active_sessions:
            del cls._active_sessions[session_id]
    
    @classmethod
    def _track_performance(
        cls,
        provider: ProviderType,
        model_id: str,
        task_type: TaskType,
        success: bool,
        processing_time: float,
        tokens_used: Optional[int] = None,
        error: Optional[str] = None,
    ) -> None:
        """
        Track performance metrics for a request.
        
        Args:
            provider: The provider type
            model_id: The model ID
            task_type: The task type
            success: Whether the request was successful
            processing_time: Processing time in seconds
            tokens_used: Number of tokens used
            error: Error message if unsuccessful
        """
        # Create metrics object
        metrics = PerformanceMetrics(
            provider=provider,
            model_id=model_id,
            task_type=task_type,
            success=success,
            processing_time=processing_time,
            tokens_used=tokens_used,
            error=error,
        )
        
        # Add to metrics list (with size limit)
        cls._performance_metrics.append(metrics)
        if len(cls._performance_metrics) > 1000:  # Limit to last 1000 metrics
            cls._performance_metrics = cls._performance_metrics[-1000:]
        
        # TODO: In a production system, we would persist these metrics to a database
    
    @classmethod
    async def get_performance_metrics(
        cls,
        provider: Optional[ProviderType] = None,
        model_id: Optional[str] = None,
        task_type: Optional[TaskType] = None,
        success: Optional[bool] = None,
        limit: int = 100,
    ) -> List[PerformanceMetrics]:
        """
        Get performance metrics with optional filtering.
        
        Args:
            provider: Filter by provider
            model_id: Filter by model ID
            task_type: Filter by task type
            success: Filter by success status
            limit: Maximum number of metrics to return
        
        Returns:
            List of performance metrics
        """
        # Filter metrics based on criteria
        filtered_metrics = cls._performance_metrics
        
        if provider:
            filtered_metrics = [m for m in filtered_metrics if m.provider == provider]
        
        if model_id:
            filtered_metrics = [m for m in filtered_metrics if m.model_id == model_id]
        
        if task_type:
            filtered_metrics = [m for m in filtered_metrics if m.task_type == task_type]
        
        if success is not None:
            filtered_metrics = [m for m in filtered_metrics if m.success == success]
        
        # Sort by timestamp (newest first) and limit
        sorted_metrics = sorted(filtered_metrics, key=lambda m: m.timestamp, reverse=True)
        return sorted_metrics[:limit]
    
    @classmethod
    async def _apply_template(
        cls,
        template_id: str,
        content: Union[str, Dict[str, Any], List[Dict[str, Any]]],
        template_vars: Optional[Dict[str, Any]] = None,
    ) -> Union[str, Dict[str, Any]]:
        """
        Apply a template to content.
        
        Args:
            template_id: The template ID
            content: The content to process
            template_vars: Variables for template rendering
        
        Returns:
            Processed content with template applied
        
        Raises:
            ValueError: When template is not found
        """
        # TODO: Implement template application
        # This would integrate with the template system
        # For now, just return the original content
        logger.warning(f"Template application not implemented yet for template {template_id}")
        return content
    
    @classmethod
    async def process_media(
        cls,
        media_type: str,
        media_content: bytes,
        task_type: TaskType = TaskType.MEDIA_ANALYSIS,
        prompt: Optional[str] = None,
        **kwargs,
    ) -> ProcessResponse:
        """
        Process media content (images, audio, video).
        
        Args:
            media_type: MIME type of the media
            media_content: Binary content of the media
            task_type: Type of media analysis to perform
            prompt: Optional text prompt to guide the analysis
            **kwargs: Additional parameters for processing
        
        Returns:
            ProcessResponse: The processed result
        
        Raises:
            TaskNotSupportedError: When media processing is not supported
            ProcessingError: When there's an error during processing
        """
        # Ensure system is initialized
        await cls.ensure_initialized()
        
        # Start timing
        start_time = time.time()
        
        try:
            # Create content object with media data
            content = {
                "media_type": media_type,
                "media_content": media_content,
                "prompt": prompt or "",
            }
            
            # Process with appropriate model (vision models for images, etc.)
            return await cls.process(
                task_type=task_type,
                content=content,
                **kwargs,
            )
            
        except Exception as e:
            # Calculate processing time for failed requests
            processing_time = time.time() - start_time
            
            # Log the error
            logger.error(f"Error processing media: {str(e)}", exc_info=True)
            
            # Re-raise as ProcessingError
            raise ProcessingError(f"Error processing media: {str(e)}") from e
