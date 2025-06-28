"""
AutoModel - Unified Interface for AI Processing

This module provides a unified interface for AI processing within the ChatChonk application.
It abstracts away the complexities of multiple AI providers, model selection, and task routing.

Author: Rip Jonesy
"""

import asyncio
import json
import logging
import time
import uuid
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union

import pystache
import yaml
from pydantic import BaseModel, Field, validator

from app.automodel import ModelPriority, ProviderType, TaskType
from app.automodel.model_registry import ModelRegistry
from app.automodel.task_router import TaskRouter
from app.core.config import settings
from app.services.cache_service import CacheService

logger = logging.getLogger("chatchonk.automodel")

# Global instances (initialized by AutoModel.initialize())
_model_registry: Optional[ModelRegistry] = None
_task_router: Optional[TaskRouter] = None
_cache_service: Optional[CacheService] = None


class ProcessRequest(BaseModel):
    """Request model for AI processing."""

    task_type: TaskType
    content: Union[str, Dict[str, Any], List[Dict[str, Any]]]
    model_id: Optional[str] = None
    max_tokens: Optional[int] = None
    temperature: float = 0.7
    top_p: float = 0.95
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    stop_sequences: Optional[List[str]] = None
    session_id: Optional[str] = None
    session_context: Optional[Dict[str, Any]] = None
    response_format: Optional[str] = None  # "text", "json_object", etc.
    priority: ModelPriority = ModelPriority.STANDARD
    excluded_providers: Optional[Set[ProviderType]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class PerformanceMetrics(BaseModel):
    """Performance metrics for AI processing."""

    request_id: str
    task_type: TaskType
    model_id: str
    provider_type: ProviderType
    start_time: float
    end_time: float
    processing_time: float
    success: bool
    tokens_used: Optional[int] = None
    error: Optional[str] = None


class ProcessResponse(BaseModel):
    """Response model for AI processing."""

    request_id: str
    content: Union[str, Dict[str, Any], List[Dict[str, Any]]]
    model_id: str
    provider_type: ProviderType
    tokens_used: Optional[int] = None
    finish_reason: Optional[str] = None
    metrics: PerformanceMetrics
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ProviderNotAvailableError(Exception):
    """Raised when no suitable provider is available for a task."""

    pass


class ModelNotFoundError(Exception):
    """Raised when a specified model is not found."""

    pass


class ProcessingError(Exception):
    """Raised when AI processing fails."""

    pass


class AutoModel:
    """
    Unified interface for AI processing.

    This class provides a single entry point for all AI processing within the
    ChatChonk application. It abstracts away the complexities of multiple AI providers,
    model selection, and task routing.
    """

    @classmethod
    async def initialize(cls) -> None:
        """
        Initialize the AutoModel system.

        This method initializes the ModelRegistry, TaskRouter, and CacheService.
        It should be called once at application startup.
        """
        global _model_registry, _task_router, _cache_service

        logger.info("Initializing AutoModel system...")

        # Initialize ModelRegistry
        _model_registry = ModelRegistry()
        await _model_registry.initialize()
        logger.info(f"ModelRegistry initialized with {len(_model_registry.get_all_models())} models")

        # Initialize TaskRouter
        _task_router = TaskRouter(_model_registry)
        logger.info("TaskRouter initialized")

        # Initialize CacheService
        _cache_service = CacheService()
        logger.info("CacheService initialized")

        logger.info("AutoModel system initialization complete")

    @classmethod
    async def shutdown(cls) -> None:
        """
        Shutdown the AutoModel system.

        This method gracefully shuts down all components of the AutoModel system.
        It should be called once at application shutdown.
        """
        global _model_registry, _task_router, _cache_service

        logger.info("Shutting down AutoModel system...")

        # Shutdown ModelRegistry
        if _model_registry:
            await _model_registry.shutdown()
            _model_registry = None
            logger.info("ModelRegistry shut down")

        # Clear TaskRouter
        _task_router = None
        logger.info("TaskRouter cleared")

        # Clear CacheService
        _cache_service = None
        logger.info("CacheService cleared")

        logger.info("AutoModel system shutdown complete")

    @staticmethod
    async def process(request: ProcessRequest) -> ProcessResponse:
        """
        Process content using the AutoModel system.

        This method is the main entry point for AI processing. It handles provider
        and model selection, caching, session management, and performance tracking.

        Args:
            request: ProcessRequest object containing the processing request

        Returns:
            ProcessResponse object containing the processing result

        Raises:
            ProviderNotAvailableError: If no suitable provider is available
            ModelNotFoundError: If the specified model is not found
            ProcessingError: If processing fails
        """
        if not _model_registry or not _task_router or not _cache_service:
            raise RuntimeError("AutoModel system not initialized")

        request_id = str(uuid.uuid4())
        start_time = time.time()

        # Try to get from cache first
        cache_key = _cache_service.generate_key(
            task_type=request.task_type,
            content=request.content,
            model_id=request.model_id,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
        )
        cached_response = await _cache_service.get(cache_key)
        if cached_response:
            logger.info(f"Cache hit for request {request_id}")
            # Add metrics to cached response
            end_time = time.time()
            cached_response.metrics = PerformanceMetrics(
                request_id=request_id,
                task_type=request.task_type,
                model_id=cached_response.model_id,
                provider_type=cached_response.provider_type,
                start_time=start_time,
                end_time=end_time,
                processing_time=end_time - start_time,
                success=True,
                tokens_used=cached_response.tokens_used,
            )
            return cached_response

        logger.info(f"Processing request {request_id} for task {request.task_type}")

        try:
            # Route the task to an appropriate model
            response = await _task_router.route_task(request)

            # Cache the response
            if response.finish_reason != "error":
                await _cache_service.set(cache_key, response)

            return response

        except Exception as e:
            end_time = time.time()
            logger.error(f"Error processing request {request_id}: {str(e)}")

            # If we have a specific model ID, try to get its provider type
            provider_type = ProviderType.UNKNOWN
            if request.model_id:
                model = _model_registry.get_model(request.model_id)
                if model:
                    provider_type = model.provider

            # Create error metrics
            metrics = PerformanceMetrics(
                request_id=request_id,
                task_type=request.task_type,
                model_id=request.model_id or "unknown",
                provider_type=provider_type,
                start_time=start_time,
                end_time=end_time,
                processing_time=end_time - start_time,
                success=False,
                error=str(e),
            )

            # Re-raise the original error
            if isinstance(e, ProviderNotAvailableError) or isinstance(e, ModelNotFoundError):
                raise
            else:
                raise ProcessingError(f"Processing failed: {str(e)}") from e

    @staticmethod
    async def process_with_fallback(
        request: ProcessRequest, fallback_providers: Optional[List[ProviderType]] = None
    ) -> ProcessResponse:
        """
        Process content with fallback to other providers if the primary fails.

        Args:
            request: ProcessRequest object containing the processing request
            fallback_providers: List of provider types to try if the primary fails

        Returns:
            ProcessResponse object containing the processing result
        """
        if not fallback_providers:
            fallback_providers = [
                ProviderType.OPENAI,
                ProviderType.ANTHROPIC,
                ProviderType.MISTRAL,
                ProviderType.HUGGINGFACE,
            ]

        # Try the primary request first
        try:
            return await AutoModel.process(request)
        except (ProviderNotAvailableError, ModelNotFoundError, ProcessingError) as primary_error:
            logger.warning(f"Primary processing failed, trying fallbacks: {str(primary_error)}")

            # Try each fallback provider
            errors = [str(primary_error)]
            for provider in fallback_providers:
                if request.excluded_providers and provider in request.excluded_providers:
                    continue

                fallback_request = ProcessRequest(
                    **request.dict(exclude={"model_id", "excluded_providers"})
                )
                fallback_request.excluded_providers = {
                    p for p in fallback_providers if p != provider
                }

                try:
                    logger.info(f"Trying fallback provider: {provider}")
                    return await AutoModel.process(fallback_request)
                except Exception as e:
                    errors.append(f"{provider}: {str(e)}")
                    continue

            # If all fallbacks fail, raise an error with all the failures
            raise ProcessingError(f"All processing attempts failed: {'; '.join(errors)}")

    @staticmethod
    async def get_available_models(
        task_type: Optional[TaskType] = None,
        excluded_providers: Optional[Set[ProviderType]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get a list of available models.

        Args:
            task_type: Optional task type to filter models by
            excluded_providers: Optional set of provider types to exclude

        Returns:
            List of model information dictionaries
        """
        if not _model_registry:
            raise RuntimeError("AutoModel system not initialized")

        models = _model_registry.get_all_models()
        result = []

        for model in models:
            # Skip models from excluded providers
            if excluded_providers and model.provider in excluded_providers:
                continue

            # Skip models that don't support the task type
            if task_type and task_type not in model.supported_tasks:
                continue

            result.append(
                {
                    "id": model.id,
                    "name": model.name,
                    "provider": model.provider.value,
                    "description": model.description,
                    "max_tokens": model.max_tokens,
                    "supports_streaming": model.supports_streaming,
                    "supports_functions": model.supports_functions,
                    "supports_vision": model.supports_vision,
                    "cost_per_1k_tokens": model.cost_per_1k_tokens,
                    "supported_tasks": [task.value for task in model.supported_tasks],
                    "priority_score": model.priority_score,
                    "is_available": model.is_available,
                }
            )

        return result

    @staticmethod
    async def set_task_model_preferences(
        task_type: TaskType,
        preferred_models: List[str],
        user_id: Optional[str] = None,
    ) -> bool:
        """
        Set preferred models for a specific task type.

        Args:
            task_type: Task type to set preferences for
            preferred_models: List of model IDs in order of preference
            user_id: Optional user ID for user-specific preferences

        Returns:
            True if preferences were set successfully, False otherwise
        """
        if not _task_router:
            raise RuntimeError("AutoModel system not initialized")

        return _task_router.set_preferred_models(task_type, preferred_models, user_id)

    @staticmethod
    async def create_session(
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Create a new AI processing session.

        Args:
            metadata: Optional metadata to associate with the session

        Returns:
            Session ID
        """
        if not _cache_service:
            raise RuntimeError("AutoModel system not initialized")

        session_id = str(uuid.uuid4())
        session_data = {
            "created_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
            "metadata": metadata or {},
            "context": {},
        }

        await _cache_service.set(f"session:{session_id}", session_data)
        return session_id

    @staticmethod
    async def update_session(
        session_id: str,
        context_updates: Dict[str, Any],
    ) -> bool:
        """
        Update an existing AI processing session.

        Args:
            session_id: Session ID
            context_updates: Updates to apply to the session context

        Returns:
            True if the session was updated successfully, False otherwise
        """
        if not _cache_service:
            raise RuntimeError("AutoModel system not initialized")

        session_key = f"session:{session_id}"
        session_data = await _cache_service.get(session_key)
        if not session_data:
            return False

        # Update the session context
        session_data["context"].update(context_updates)
        session_data["last_updated"] = datetime.now().isoformat()

        await _cache_service.set(session_key, session_data)
        return True

    @staticmethod
    async def get_session(session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get an existing AI processing session.

        Args:
            session_id: Session ID

        Returns:
            Session data or None if not found
        """
        if not _cache_service:
            raise RuntimeError("AutoModel system not initialized")

        return await _cache_service.get(f"session:{session_id}")

    @staticmethod
    async def delete_session(session_id: str) -> bool:
        """
        Delete an AI processing session.

        Args:
            session_id: Session ID

        Returns:
            True if the session was deleted successfully, False otherwise
        """
        if not _cache_service:
            raise RuntimeError("AutoModel system not initialized")

        return await _cache_service.delete(f"session:{session_id}")

    @staticmethod
    async def process_media(
        task_type: TaskType,
        media_data: bytes,
        media_type: str,
        text_prompt: Optional[str] = None,
        model_id: Optional[str] = None,
        max_tokens: Optional[int] = None,
    ) -> ProcessResponse:
        """
        Process media content (images, audio, etc.) using the AutoModel system.

        Args:
            task_type: Type of task to perform (e.g., IMAGE_ANALYSIS)
            media_data: Binary media data
            media_type: MIME type of the media
            text_prompt: Optional text prompt to guide the AI
            model_id: Optional specific model to use
            max_tokens: Maximum tokens to generate in the response

        Returns:
            ProcessResponse object containing the processing result
        """
        if not _model_registry or not _task_router:
            raise RuntimeError("AutoModel system not initialized")

        # Prepare the request
        request = ProcessRequest(
            task_type=task_type,
            content={
                "media_data": media_data.hex(),  # Convert bytes to hex string
                "media_type": media_type,
                "text_prompt": text_prompt or "",
            },
            model_id=model_id,
            max_tokens=max_tokens,
            priority=ModelPriority.HIGH,  # Media processing is typically high priority
        )

        # Process the request
        return await AutoModel.process(request)

    @staticmethod
    async def _apply_template(
        conversation_content: str,
        template_id: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Apply a template to a conversation.

        Args:
            conversation_content: Raw conversation content
            template_id: ID of the template to apply
            metadata: Optional metadata to include in the template

        Returns:
            Processed conversation with the template applied
        """
        # Construct the full path to the template file
        template_path = Path(settings.TEMPLATES_DIR) / f"{template_id}.yaml"
        
        # Check if the template file exists
        if not template_path.exists():
            raise FileNotFoundError(f"Template not found: {template_path}")
        
        # Read and parse the YAML content
        with open(template_path, "r", encoding="utf-8") as f:
            template_data = yaml.safe_load(f)
        
        # Extract the system prompt and template content
        if (
            "ai_processing" not in template_data
            or "system_prompt" not in template_data["ai_processing"]
            or "template" not in template_data
            or "content" not in template_data["template"]
        ):
            raise ValueError(f"Invalid template format: {template_id}")
        
        system_prompt = template_data["ai_processing"]["system_prompt"]
        template_content = template_data["template"]["content"]
        
        # Get AI parameters from template or use defaults
        ai_params = template_data["ai_processing"].get("parameters", {})
        temperature = ai_params.get("temperature", 0.7)
        max_tokens = ai_params.get("max_tokens", 2000)
        top_p = ai_params.get("top_p", 0.95)
        
        # Prepare a prompt for the AI to generate structured data
        ai_prompt = f"""
        {system_prompt}
        
        Here is the conversation to process:
        
        {conversation_content}
        
        Return a JSON object with the extracted data that can be used to populate the template.
        Make sure the JSON is valid and contains all the necessary fields for the template.
        """
        
        # Process the prompt with AI to get structured data
        request = ProcessRequest(
            task_type=TaskType.SYSTEM,
            content=ai_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
            response_format="json_object",
            priority=ModelPriority.HIGH,
        )
        
        response = await AutoModel.process(request)
        
        # Parse the AI's JSON response
        try:
            if isinstance(response.content, str):
                template_data = json.loads(response.content)
            else:
                template_data = response.content
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse AI response as JSON: {e}")
        
        # Add metadata if provided
        if metadata:
            template_data.update(metadata)
        
        # Add current date if not present
        if "date" not in template_data:
            template_data["date"] = datetime.now().strftime("%Y-%m-%d")
        
        # Render the template using pystache
        try:
            rendered_content = pystache.render(template_content, template_data)
            return rendered_content
        except Exception as e:
            raise ValueError(f"Failed to render template: {e}")

    @staticmethod
    async def process_with_models(
        task_type: TaskType,
        content: Union[str, Dict[str, Any], List[Dict[str, Any]]],
        model_ids: List[str],
        **kwargs,
    ) -> Dict[str, ProcessResponse]:
        """
        Process content with multiple models for comparison.

        Args:
            task_type: Type of task to perform
            content: Content to process
            model_ids: List of model IDs to use
            **kwargs: Additional processing parameters

        Returns:
            Dictionary mapping model IDs to their responses
        """
        if not _model_registry:
            raise RuntimeError("AutoModel system not initialized")

        results = {}
        tasks = []

        for model_id in model_ids:
            request = ProcessRequest(
                task_type=task_type,
                content=content,
                model_id=model_id,
                **kwargs,
            )
            tasks.append(AutoModel.process(request))

        # Process all requests concurrently
        responses = await asyncio.gather(*tasks, return_exceptions=True)

        # Organize responses by model ID
        for i, response in enumerate(responses):
            model_id = model_ids[i]
            if isinstance(response, Exception):
                logger.error(f"Error processing with model {model_id}: {str(response)}")
                # Create a dummy response for failed models
                results[model_id] = ProcessResponse(
                    request_id=str(uuid.uuid4()),
                    content=f"Error: {str(response)}",
                    model_id=model_id,
                    provider_type=ProviderType.UNKNOWN,
                    metrics=PerformanceMetrics(
                        request_id=str(uuid.uuid4()),
                        task_type=task_type,
                        model_id=model_id,
                        provider_type=ProviderType.UNKNOWN,
                        start_time=time.time(),
                        end_time=time.time(),
                        processing_time=0.0,
                        success=False,
                        error=str(response),
                    ),
                )
            else:
                results[model_id] = response

        return results
