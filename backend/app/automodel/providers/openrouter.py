"""
OpenRouter Provider - OpenRouter API Integration

This module provides integration with OpenRouter's API for the AutoModel system.
OpenRouter provides access to many different AI models through a unified API,
making it perfect for experimentation with various models.

Author: Rip Jonesy
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Union

import httpx
from pydantic import ValidationError

from app.automodel import TaskType, ProviderType
from .base import BaseProvider, Model, ProviderResponse

logger = logging.getLogger("chatchonk.automodel.providers.openrouter")


class OpenRouterProvider(BaseProvider):
    """OpenRouter provider implementation for the AutoModel system."""

    def __init__(self, api_key: Optional[str] = None, **kwargs):
        """
        Initialize the OpenRouter provider.

        Args:
            api_key: OpenRouter API key
            **kwargs: Additional configuration options
        """
        super().__init__(api_key, **kwargs)
        self.base_url = kwargs.get("base_url", "https://openrouter.ai/api/v1")
        self.timeout = kwargs.get("timeout", 60)
        self.app_name = kwargs.get("app_name", "ChatChonk")
        self.app_url = kwargs.get("app_url", "https://github.com/ripj3/CHATCHONKBETA")
        self._client: Optional[httpx.AsyncClient] = None

    @property
    def provider_type(self) -> ProviderType:
        """Return the provider type."""
        return ProviderType.OPENROUTER

    @property
    def name(self) -> str:
        """Return the human-readable name of the provider."""
        return "OpenRouter"

    async def initialize(self) -> None:
        """Initialize the OpenRouter provider and load available models."""
        if self._is_initialized:
            return

        if not self.api_key:
            raise ValueError("OpenRouter API key is required")

        # Initialize HTTP client
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": self.app_url,
                "X-Title": self.app_name,
            },
            timeout=self.timeout,
        )

        # Load available models from OpenRouter
        await self._load_models()

        self._is_initialized = True
        logger.info(f"OpenRouter provider initialized with {len(self._models)} models")

    async def _load_models(self) -> None:
        """Load available OpenRouter models and their capabilities."""
        try:
            # Get models from OpenRouter API
            response = await self._client.get("/models")
            response.raise_for_status()

            models_data = response.json()

            for model_data in models_data.get("data", []):
                model_id = model_data.get("id", "")
                if not model_id:
                    continue

                # Extract model information
                name = model_data.get("name", model_id)
                description = model_data.get("description", "")
                context_length = model_data.get("context_length", 4096)

                # Determine supported tasks based on model type/name
                supported_tasks = self._determine_supported_tasks(
                    model_id, name, description
                )

                # Calculate priority score based on model characteristics
                priority_score = self._calculate_priority_score(model_data)

                # Get pricing information
                pricing = model_data.get("pricing", {})
                cost_per_1k_tokens = None
                if pricing:
                    prompt_cost = pricing.get("prompt", "0")
                    completion_cost = pricing.get("completion", "0")
                    # Use average of prompt and completion costs
                    try:
                        avg_cost = (float(prompt_cost) + float(completion_cost)) / 2
                        cost_per_1k_tokens = avg_cost * 1000  # Convert to per 1k tokens
                    except (ValueError, TypeError):
                        pass

                model = Model(
                    id=model_id,
                    name=name,
                    provider=self.provider_type,
                    description=description,
                    max_tokens=context_length,
                    supports_streaming=True,  # Most OpenRouter models support streaming
                    supports_functions=self._supports_functions(model_id),
                    supports_vision=self._supports_vision(model_id),
                    cost_per_1k_tokens=cost_per_1k_tokens,
                    supported_tasks=supported_tasks,
                    priority_score=priority_score,
                    is_available=True,
                    metadata=model_data,
                )
                self._models[model.id] = model

        except Exception as e:
            logger.error(f"Failed to load OpenRouter models: {str(e)}")
            # Fall back to a basic set of known models
            await self._load_fallback_models()

    def _determine_supported_tasks(
        self, model_id: str, name: str, description: str
    ) -> set:
        """Determine which tasks a model supports based on its characteristics."""
        supported_tasks = set()

        # Convert to lowercase for easier matching
        model_lower = model_id.lower()

        # Most models support basic text generation and chat
        supported_tasks.add(TaskType.TEXT_GENERATION)
        supported_tasks.add(TaskType.CHAT)

        # Check for specific capabilities
        if any(
            term in model_lower
            for term in ["gpt", "claude", "llama", "mistral", "qwen"]
        ):
            supported_tasks.update(
                [
                    TaskType.SUMMARIZATION,
                    TaskType.TOPIC_EXTRACTION,
                    TaskType.CLASSIFICATION,
                    TaskType.TRANSLATION,
                ]
            )

        # Advanced reasoning models
        if any(term in model_lower for term in ["gpt-4", "claude-3", "opus", "sonnet"]):
            supported_tasks.update([TaskType.SENSEMAKING, TaskType.PLANNING])

        # Vision models
        if self._supports_vision(model_id):
            supported_tasks.add(TaskType.MEDIA_ANALYSIS)

        # Embedding models
        if "embed" in model_lower:
            supported_tasks = {TaskType.EMBEDDING}

        return supported_tasks

    def _supports_functions(self, model_id: str) -> bool:
        """Check if a model supports function calling."""
        function_models = ["gpt-4", "gpt-3.5-turbo", "claude-3", "mistral"]
        return any(model in model_id.lower() for model in function_models)

    def _supports_vision(self, model_id: str) -> bool:
        """Check if a model supports vision/image analysis."""
        vision_models = ["gpt-4-vision", "gpt-4o", "claude-3", "llava", "vision"]
        return any(model in model_id.lower() for model in vision_models)

    def _calculate_priority_score(self, model_data: Dict[str, Any]) -> float:
        """Calculate priority score for a model based on its characteristics."""
        base_score = 5.0

        model_id = model_data.get("id", "").lower()

        # Boost score for well-known high-quality models
        if "gpt-4o" in model_id:
            base_score = 10.0
        elif "gpt-4" in model_id:
            base_score = 9.0
        elif "claude-3.5-sonnet" in model_id:
            base_score = 9.5
        elif "claude-3-opus" in model_id:
            base_score = 9.0
        elif "claude-3" in model_id:
            base_score = 8.0
        elif "gpt-3.5" in model_id:
            base_score = 7.0
        elif "llama" in model_id:
            base_score = 6.5
        elif "mistral" in model_id:
            base_score = 7.5

        # Adjust based on context length
        context_length = model_data.get("context_length", 4096)
        if context_length >= 100000:
            base_score += 1.0
        elif context_length >= 32000:
            base_score += 0.5

        return base_score

    async def _load_fallback_models(self) -> None:
        """Load a basic set of known OpenRouter models as fallback."""
        fallback_models = [
            {
                "id": "openai/gpt-4o",
                "name": "GPT-4o",
                "description": "OpenAI's most advanced model",
                "max_tokens": 128000,
                "priority_score": 10.0,
                "cost_per_1k_tokens": 0.005,
                "supported_tasks": {
                    TaskType.TEXT_GENERATION,
                    TaskType.SUMMARIZATION,
                    TaskType.TOPIC_EXTRACTION,
                    TaskType.CLASSIFICATION,
                    TaskType.SENSEMAKING,
                    TaskType.PLANNING,
                    TaskType.MEDIA_ANALYSIS,
                    TaskType.TRANSLATION,
                    TaskType.CHAT,
                },
            },
            {
                "id": "anthropic/claude-3.5-sonnet",
                "name": "Claude 3.5 Sonnet",
                "description": "Anthropic's most intelligent model",
                "max_tokens": 200000,
                "priority_score": 9.5,
                "cost_per_1k_tokens": 0.003,
                "supported_tasks": {
                    TaskType.TEXT_GENERATION,
                    TaskType.SUMMARIZATION,
                    TaskType.TOPIC_EXTRACTION,
                    TaskType.CLASSIFICATION,
                    TaskType.SENSEMAKING,
                    TaskType.PLANNING,
                    TaskType.TRANSLATION,
                    TaskType.CHAT,
                },
            },
            {
                "id": "meta-llama/llama-3.1-70b-instruct",
                "name": "Llama 3.1 70B",
                "description": "Meta's large language model",
                "max_tokens": 131072,
                "priority_score": 8.0,
                "cost_per_1k_tokens": 0.0009,
                "supported_tasks": {
                    TaskType.TEXT_GENERATION,
                    TaskType.SUMMARIZATION,
                    TaskType.TOPIC_EXTRACTION,
                    TaskType.CLASSIFICATION,
                    TaskType.TRANSLATION,
                    TaskType.CHAT,
                },
            },
        ]

        for config in fallback_models:
            model = Model(
                id=config["id"],
                name=config["name"],
                provider=self.provider_type,
                description=config["description"],
                max_tokens=config["max_tokens"],
                supports_streaming=True,
                supports_functions=False,
                supports_vision="gpt-4o" in config["id"],
                cost_per_1k_tokens=config["cost_per_1k_tokens"],
                supported_tasks=config["supported_tasks"],
                priority_score=config["priority_score"],
                is_available=True,
            )
            self._models[model.id] = model

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
        **kwargs,
    ) -> ProviderResponse:
        """Process content using OpenRouter models."""
        if not self._is_initialized:
            await self.initialize()

        model = self.get_model(model_id)
        if not model:
            raise ValueError(f"Model {model_id} not found")

        if not self.supports_task(model_id, task_type):
            raise ValueError(f"Model {model_id} does not support task {task_type}")

        try:
            return await self._process_chat_completion(
                model_id,
                task_type,
                content,
                max_tokens,
                temperature,
                top_p,
                frequency_penalty,
                presence_penalty,
                stop_sequences,
                session_context,
                **kwargs,
            )
        except Exception as e:
            self._set_error(f"Processing failed: {str(e)}")
            raise

    async def _process_chat_completion(
        self,
        model_id: str,
        task_type: TaskType,
        content: Union[str, Dict[str, Any], List[Dict[str, Any]]],
        max_tokens: Optional[int],
        temperature: float,
        top_p: float,
        frequency_penalty: float,
        presence_penalty: float,
        stop_sequences: Optional[List[str]],
        session_context: Optional[Dict[str, Any]],
        **kwargs,
    ) -> ProviderResponse:
        """Process chat completion requests using OpenRouter's API."""
        # Convert content to messages format
        messages = self._prepare_messages(task_type, content, session_context)

        payload = {
            "model": model_id,
            "messages": messages,
            "temperature": temperature,
            "top_p": top_p,
            "frequency_penalty": frequency_penalty,
            "presence_penalty": presence_penalty,
        }

        if max_tokens:
            payload["max_tokens"] = max_tokens
        if stop_sequences:
            payload["stop"] = stop_sequences

        response = await self._client.post("/chat/completions", json=payload)
        response.raise_for_status()

        result = response.json()
        choice = result["choices"][0]
        message_content = choice["message"]["content"]
        tokens_used = result.get("usage", {}).get("total_tokens", 0)
        finish_reason = choice["finish_reason"]

        return ProviderResponse(
            content=message_content,
            model_id=model_id,
            tokens_used=tokens_used,
            finish_reason=finish_reason,
            metadata={"prompt_tokens": result.get("usage", {}).get("prompt_tokens", 0)},
        )

    def _prepare_messages(
        self,
        task_type: TaskType,
        content: Union[str, Dict[str, Any], List[Dict[str, Any]]],
        session_context: Optional[Dict[str, Any]],
    ) -> List[Dict[str, str]]:
        """Prepare messages for OpenRouter chat completion format."""
        messages = []

        # Add system message based on task type
        system_prompt = self._get_system_prompt(task_type)
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        # Add session context if available
        if session_context and "messages" in session_context:
            messages.extend(session_context["messages"])

        # Add current content
        if isinstance(content, str):
            messages.append({"role": "user", "content": content})
        elif isinstance(content, dict) and "messages" in content:
            messages.extend(content["messages"])
        elif isinstance(content, list):
            for item in content:
                if isinstance(item, dict) and "role" in item and "content" in item:
                    messages.append(item)
                else:
                    messages.append({"role": "user", "content": str(item)})
        else:
            messages.append({"role": "user", "content": str(content)})

        return messages

    def _get_system_prompt(self, task_type: TaskType) -> Optional[str]:
        """Get system prompt for specific task types."""
        prompts = {
            TaskType.SUMMARIZATION: "You are an expert at creating concise, accurate summaries. Focus on the key points and main ideas.",
            TaskType.TOPIC_EXTRACTION: "You are an expert at identifying and extracting key topics and themes from text. Provide clear, relevant topics.",
            TaskType.CLASSIFICATION: "You are an expert at text classification. Analyze the content and provide accurate classifications.",
            TaskType.SENSEMAKING: "You are an expert at analyzing complex information and making sense of patterns, relationships, and insights.",
            TaskType.PLANNING: "You are an expert at creating structured plans and organizing information logically.",
            TaskType.TRANSLATION: "You are an expert translator. Provide accurate, natural translations while preserving meaning and context.",
            TaskType.MEDIA_ANALYSIS: "You are an expert at analyzing visual content. Describe what you see in detail and provide insights.",
        }
        return prompts.get(task_type)

    async def __aenter__(self):
        """Async context manager entry."""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._client:
            await self._client.aclose()
