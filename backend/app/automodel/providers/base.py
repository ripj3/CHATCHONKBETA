"""
Base Provider - Abstract Base Class for AI Providers

This module defines the abstract base class that all AI providers must implement
to integrate with the AutoModel system. It provides a consistent interface for
AI processing across different providers.

Author: Rip Jonesy
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Union

from pydantic import BaseModel, Field

from app.automodel import TaskType, ProviderType

logger = logging.getLogger("chatchonk.automodel.providers")


class Model(BaseModel):
    """Represents an AI model with its capabilities and metadata."""
    
    id: str = Field(..., description="Unique identifier for the model")
    name: str = Field(..., description="Human-readable name of the model")
    provider: ProviderType = Field(..., description="Provider that hosts this model")
    description: Optional[str] = Field(None, description="Description of the model's capabilities")
    max_tokens: int = Field(default=4096, description="Maximum tokens the model can process")
    supports_streaming: bool = Field(default=False, description="Whether the model supports streaming responses")
    supports_functions: bool = Field(default=False, description="Whether the model supports function calling")
    supports_vision: bool = Field(default=False, description="Whether the model supports image analysis")
    cost_per_1k_tokens: Optional[float] = Field(None, description="Cost per 1000 tokens (if known)")
    supported_tasks: Set[TaskType] = Field(default_factory=set, description="Tasks this model can perform")
    priority_score: float = Field(default=1.0, description="Priority score for model selection (higher = better)")
    is_available: bool = Field(default=True, description="Whether the model is currently available")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional model metadata")


class ProviderResponse(BaseModel):
    """Response from a provider after processing a request."""
    
    content: Union[str, Dict[str, Any], List[Dict[str, Any]]] = Field(..., description="Generated content")
    model_id: str = Field(..., description="ID of the model that generated the response")
    tokens_used: Optional[int] = Field(None, description="Number of tokens used in processing")
    finish_reason: Optional[str] = Field(None, description="Reason why generation finished")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional response metadata")


class BaseProvider(ABC):
    """
    Abstract base class for all AI providers.
    
    This class defines the interface that all providers must implement to integrate
    with the AutoModel system. It handles common functionality like model management,
    error handling, and rate limiting.
    """
    
    def __init__(self, api_key: Optional[str] = None, **kwargs):
        """
        Initialize the provider.
        
        Args:
            api_key: API key for the provider
            **kwargs: Additional provider-specific configuration
        """
        self.api_key = api_key
        self.config = kwargs
        self._models: Dict[str, Model] = {}
        self._is_initialized = False
        self._last_error: Optional[str] = None
        
    @property
    @abstractmethod
    def provider_type(self) -> ProviderType:
        """Return the provider type."""
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Return the human-readable name of the provider."""
        pass
    
    @abstractmethod
    async def initialize(self) -> None:
        """
        Initialize the provider and load available models.
        
        This method should:
        1. Validate API credentials
        2. Load available models
        3. Set up any necessary connections
        """
        pass
    
    @abstractmethod
    async def process(
        self,
        task_type: TaskType,
        model_id: str,
        content: Union[str, Dict[str, Any], List[Dict[str, Any]]],
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
        top_p: float = 0.95,
        frequency_penalty: float = 0.0,
        presence_penalty: float = 0.0,
        stop_sequences: Optional[List[str]] = None,
        session_context: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> ProviderResponse:
        """
        Process content using the specified model.
        
        Args:
            task_type: Type of task to perform
            model_id: ID of the model to use
            content: Content to process
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            top_p: Nucleus sampling parameter
            frequency_penalty: Frequency penalty
            presence_penalty: Presence penalty
            stop_sequences: Sequences to stop generation
            session_context: Context from previous interactions
            **kwargs: Additional provider-specific parameters
            
        Returns:
            ProviderResponse with the generated content
        """
        pass
    
    def get_model(self, model_id: str) -> Optional[Model]:
        """
        Get a model by its ID.
        
        Args:
            model_id: ID of the model to retrieve
            
        Returns:
            Model object or None if not found
        """
        return self._models.get(model_id)
    
    def get_models(self) -> List[Model]:
        """
        Get all available models for this provider.
        
        Returns:
            List of available models
        """
        return list(self._models.values())
    
    def supports_task(self, model_id: str, task_type: TaskType) -> bool:
        """
        Check if a model supports a specific task type.
        
        Args:
            model_id: ID of the model to check
            task_type: Task type to check support for
            
        Returns:
            True if the model supports the task, False otherwise
        """
        model = self.get_model(model_id)
        if not model:
            return False
        return task_type in model.supported_tasks
    
    def get_best_model_for_task(self, task_type: TaskType) -> Optional[Model]:
        """
        Get the best model for a specific task type.
        
        Args:
            task_type: Task type to find a model for
            
        Returns:
            Best model for the task or None if no suitable model found
        """
        suitable_models = [
            model for model in self._models.values()
            if task_type in model.supported_tasks and model.is_available
        ]
        
        if not suitable_models:
            return None
            
        # Sort by priority score (higher is better)
        suitable_models.sort(key=lambda m: m.priority_score, reverse=True)
        return suitable_models[0]
    
    @property
    def is_available(self) -> bool:
        """Check if the provider is available and has working models."""
        return (
            self._is_initialized and 
            self.api_key is not None and 
            len(self._models) > 0 and
            any(model.is_available for model in self._models.values())
        )
    
    @property
    def last_error(self) -> Optional[str]:
        """Get the last error that occurred with this provider."""
        return self._last_error
    
    def _set_error(self, error: str) -> None:
        """Set the last error for this provider."""
        self._last_error = error
        logger.error(f"{self.name} error: {error}")
    
    def _clear_error(self) -> None:
        """Clear the last error for this provider."""
        self._last_error = None
    
    async def health_check(self) -> bool:
        """
        Perform a health check on the provider.
        
        Returns:
            True if the provider is healthy, False otherwise
        """
        try:
            if not self.is_available:
                return False
                
            # Try a simple request to verify the provider is working
            test_model = self.get_best_model_for_task(TaskType.TEXT_GENERATION)
            if not test_model:
                return False
                
            # Perform a minimal test request
            await self.process(
                task_type=TaskType.TEXT_GENERATION,
                model_id=test_model.id,
                content="Hello",
                max_tokens=1,
                temperature=0.0
            )
            
            self._clear_error()
            return True
            
        except Exception as e:
            self._set_error(f"Health check failed: {str(e)}")
            return False
    
    def __str__(self) -> str:
        """String representation of the provider."""
        return f"{self.name} ({len(self._models)} models)"
    
    def __repr__(self) -> str:
        """Detailed string representation of the provider."""
        return f"{self.__class__.__name__}(provider_type={self.provider_type}, models={len(self._models)})"
