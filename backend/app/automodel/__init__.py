"""
AutoModel - AI Model Abstraction Layer for ChatChonk

This module provides a unified interface for interacting with multiple AI providers
through a consistent API. It handles model selection, task routing, and provider
management to make AI integration seamless throughout the application.

Usage:
    from app.automodel import AutoModel, TaskType
    
    # Basic usage with default settings
    result = await AutoModel.process(
        task_type=TaskType.SUMMARIZATION,
        content="Your long text to summarize...",
    )
    
    # Advanced usage with specific model and parameters
    result = await AutoModel.process(
        task_type=TaskType.TOPIC_EXTRACTION,
        content="Your chat log content...",
        provider="anthropic",
        model_id="claude-3-opus-20240229",
        max_tokens=2000,
        temperature=0.7,
    )

Author: Rip Jonesy
"""

from enum import Enum, auto
from typing import Any, Dict, List, Optional, Union

# Forward imports from submodules
from .model_registry import ModelRegistry
from .task_router import TaskRouter
from .providers.base import BaseProvider
from .providers.huggingface import HuggingFaceProvider
from .providers.openai import OpenAIProvider
from .providers.anthropic import AnthropicProvider
from .providers.mistral import MistralProvider
from .providers.deepseek import DeepseekProvider
from .providers.qwen import QwenProvider
from .providers.openrouter import OpenRouterProvider
from .automodel import AutoModel

# === Task Types ===
class TaskType(str, Enum):
    """Types of AI tasks supported by the AutoModel system."""
    
    TEXT_GENERATION = "text_generation"
    SUMMARIZATION = "summarization"
    TOPIC_EXTRACTION = "topic_extraction"
    CLASSIFICATION = "classification"
    EMBEDDING = "embedding"
    SENSEMAKING = "sensemaking"  # Complex analysis
    PLANNING = "planning"  # Structured planning
    MEDIA_ANALYSIS = "media_analysis"  # Image/audio analysis
    TRANSLATION = "translation"
    CHAT = "chat"  # Multi-turn conversation


class ProviderType(str, Enum):
    """Supported AI model providers."""

    HUGGINGFACE = "huggingface"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    MISTRAL = "mistral"
    DEEPSEEK = "deepseek"
    QWEN = "qwen"
    OPENROUTER = "openrouter"
    CUSTOM = "custom"


class ModelPriority(int, Enum):
    """Priority levels for model selection."""
    
    LOW = 0
    MEDIUM = 1
    HIGH = 2
    CRITICAL = 3


# === Exceptions ===
class AutoModelError(Exception):
    """Base exception for all AutoModel errors."""
    pass


class ProviderNotAvailableError(AutoModelError):
    """Raised when a requested provider is not available."""
    pass


class ModelNotFoundError(AutoModelError):
    """Raised when a requested model is not found."""
    pass


class TaskNotSupportedError(AutoModelError):
    """Raised when a task is not supported by the selected model."""
    pass


class ProviderApiError(AutoModelError):
    """Raised when there's an error from the provider's API."""
    pass


class ProcessingError(AutoModelError):
    """Raised when there's an error during processing."""
    pass

# Export public API
__all__ = [
    # Main classes
    "AutoModel",
    "ModelRegistry",
    "TaskRouter",
    "BaseProvider",
    
    # Provider implementations
    "HuggingFaceProvider",
    "OpenAIProvider",
    "AnthropicProvider",
    "MistralProvider",
    "DeepseekProvider",
    "QwenProvider",
    "OpenRouterProvider",
    
    # Enums
    "TaskType",
    "ProviderType",
    "ModelPriority",
    
    # Exceptions
    "AutoModelError",
    "ProviderNotAvailableError",
    "ModelNotFoundError",
    "TaskNotSupportedError",
    "ProviderApiError",
    "ProcessingError",
]

# Version
__version__ = "0.1.0"
