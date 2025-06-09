"""
Anthropic Provider - Anthropic Claude API Integration

This module provides integration with Anthropic's Claude API for the AutoModel system.
Claude excels at reasoning, analysis, and complex text processing tasks.

Author: Rip Jonesy
"""

import logging
from typing import Any, Dict, List, Optional, Union

import httpx

from app.automodel import TaskType, ProviderType
from .base import BaseProvider, Model, ProviderResponse

logger = logging.getLogger("chatchonk.automodel.providers.anthropic")


class AnthropicProvider(BaseProvider):
    """Anthropic Claude provider implementation for the AutoModel system."""

    def __init__(self, api_key: Optional[str] = None, **kwargs):
        """
        Initialize the Anthropic provider.

        Args:
            api_key: Anthropic API key
            **kwargs: Additional configuration options
        """
        super().__init__(api_key, **kwargs)
        self.base_url = kwargs.get("base_url", "https://api.anthropic.com")
        self.timeout = kwargs.get("timeout", 60)
        self.anthropic_version = kwargs.get("anthropic_version", "2023-06-01")
        self._client: Optional[httpx.AsyncClient] = None

    @property
    def provider_type(self) -> ProviderType:
        """Return the provider type."""
        return ProviderType.ANTHROPIC

    @property
    def name(self) -> str:
        """Return the human-readable name of the provider."""
        return "Anthropic Claude"

    async def initialize(self) -> None:
        """Initialize the Anthropic provider and load available models."""
        if self._is_initialized:
            return

        if not self.api_key:
            raise ValueError("Anthropic API key is required")

        # Initialize HTTP client
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={
                "x-api-key": self.api_key,
                "Content-Type": "application/json",
                "anthropic-version": self.anthropic_version,
            },
            timeout=self.timeout,
        )

        # Load available models
        await self._load_models()

        self._is_initialized = True
        logger.info(f"Anthropic provider initialized with {len(self._models)} models")

    async def _load_models(self) -> None:
        """Load available Anthropic models and their capabilities."""
        # Define Anthropic models with their capabilities
        model_configs = [
            {
                "id": "claude-3-5-sonnet-20241022",
                "name": "Claude 3.5 Sonnet",
                "description": "Most intelligent model with vision capabilities",
                "max_tokens": 200000,
                "supports_vision": True,
                "cost_per_1k_tokens": 0.003,
                "priority_score": 10.0,
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
                "id": "claude-3-opus-20240229",
                "name": "Claude 3 Opus",
                "description": "Most powerful model for complex reasoning",
                "max_tokens": 200000,
                "cost_per_1k_tokens": 0.015,
                "priority_score": 9.5,
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
                "id": "claude-3-sonnet-20240229",
                "name": "Claude 3 Sonnet",
                "description": "Balanced model for most tasks",
                "max_tokens": 200000,
                "cost_per_1k_tokens": 0.003,
                "priority_score": 8.5,
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
                "id": "claude-3-haiku-20240307",
                "name": "Claude 3 Haiku",
                "description": "Fast and efficient model for simple tasks",
                "max_tokens": 200000,
                "cost_per_1k_tokens": 0.00025,
                "priority_score": 7.0,
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

        for config in model_configs:
            model = Model(
                id=config["id"],
                name=config["name"],
                provider=self.provider_type,
                description=config["description"],
                max_tokens=config["max_tokens"],
                supports_streaming=True,
                supports_functions=False,  # Claude doesn't support function calling yet
                supports_vision=config.get("supports_vision", False),
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
        """Process content using Anthropic Claude models."""
        if not self._is_initialized:
            await self.initialize()

        model = self.get_model(model_id)
        if not model:
            raise ValueError(f"Model {model_id} not found")

        if not self.supports_task(model_id, task_type):
            raise ValueError(f"Model {model_id} does not support task {task_type}")

        try:
            return await self._process_message(
                model_id,
                task_type,
                content,
                max_tokens,
                temperature,
                top_p,
                stop_sequences,
                session_context,
                **kwargs,
            )
        except Exception as e:
            self._set_error(f"Processing failed: {str(e)}")
            raise

    async def _process_message(
        self,
        model_id: str,
        task_type: TaskType,
        content: Union[str, Dict[str, Any], List[Dict[str, Any]]],
        max_tokens: Optional[int],
        temperature: float,
        top_p: float,
        stop_sequences: Optional[List[str]],
        session_context: Optional[Dict[str, Any]],
        **kwargs,
    ) -> ProviderResponse:
        """Process message requests using Claude's messages API."""
        # Prepare messages and system prompt
        messages, system_prompt = self._prepare_messages(
            task_type, content, session_context
        )

        payload = {
            "model": model_id,
            "messages": messages,
            "max_tokens": max_tokens or 4096,
            "temperature": temperature,
            "top_p": top_p,
        }

        if system_prompt:
            payload["system"] = system_prompt
        if stop_sequences:
            payload["stop_sequences"] = stop_sequences

        response = await self._client.post("/v1/messages", json=payload)
        response.raise_for_status()

        result = response.json()

        # Extract content from Claude's response format
        content_blocks = result.get("content", [])
        if content_blocks and len(content_blocks) > 0:
            message_content = content_blocks[0].get("text", "")
        else:
            message_content = ""

        tokens_used = result.get("usage", {}).get("output_tokens", 0) + result.get(
            "usage", {}
        ).get("input_tokens", 0)
        finish_reason = result.get("stop_reason", "completed")

        return ProviderResponse(
            content=message_content,
            model_id=model_id,
            tokens_used=tokens_used,
            finish_reason=finish_reason,
            metadata={
                "input_tokens": result.get("usage", {}).get("input_tokens", 0),
                "output_tokens": result.get("usage", {}).get("output_tokens", 0),
            },
        )

    def _prepare_messages(
        self,
        task_type: TaskType,
        content: Union[str, Dict[str, Any], List[Dict[str, Any]]],
        session_context: Optional[Dict[str, Any]],
    ) -> tuple[List[Dict[str, Any]], Optional[str]]:
        """Prepare messages for Claude's message format."""
        messages = []
        system_prompt = self._get_system_prompt(task_type)

        # Add session context if available
        if session_context and "messages" in session_context:
            # Filter out system messages as they go in the system parameter
            for msg in session_context["messages"]:
                if msg.get("role") != "system":
                    messages.append(msg)

        # Add current content
        if isinstance(content, str):
            messages.append({"role": "user", "content": content})
        elif isinstance(content, dict) and "messages" in content:
            for msg in content["messages"]:
                if msg.get("role") != "system":
                    messages.append(msg)
        elif isinstance(content, list):
            for item in content:
                if isinstance(item, dict) and "role" in item and "content" in item:
                    if item.get("role") != "system":
                        messages.append(item)
                else:
                    messages.append({"role": "user", "content": str(item)})
        else:
            messages.append({"role": "user", "content": str(content)})

        # Ensure messages alternate between user and assistant
        cleaned_messages = []
        last_role = None

        for msg in messages:
            role = msg.get("role")
            if role == last_role:
                # Merge consecutive messages from the same role
                if cleaned_messages:
                    cleaned_messages[-1]["content"] += "\n\n" + msg["content"]
                else:
                    cleaned_messages.append(msg)
            else:
                cleaned_messages.append(msg)
                last_role = role

        # Ensure the conversation starts with a user message
        if cleaned_messages and cleaned_messages[0].get("role") != "user":
            cleaned_messages.insert(
                0, {"role": "user", "content": "Please help me with the following:"}
            )

        return cleaned_messages, system_prompt

    def _get_system_prompt(self, task_type: TaskType) -> Optional[str]:
        """Get system prompt for specific task types."""
        prompts = {
            TaskType.SUMMARIZATION: "You are an expert at creating concise, accurate summaries. Focus on the key points and main ideas while preserving important context.",
            TaskType.TOPIC_EXTRACTION: "You are an expert at identifying and extracting key topics and themes from text. Provide clear, relevant topics with brief explanations.",
            TaskType.CLASSIFICATION: "You are an expert at text classification. Analyze the content carefully and provide accurate, well-reasoned classifications.",
            TaskType.SENSEMAKING: "You are an expert at analyzing complex information and making sense of patterns, relationships, and insights. Think deeply about connections and implications.",
            TaskType.PLANNING: "You are an expert at creating structured plans and organizing information logically. Break down complex tasks into manageable steps.",
            TaskType.TRANSLATION: "You are an expert translator. Provide accurate, natural translations while preserving meaning, context, and cultural nuances.",
            TaskType.MEDIA_ANALYSIS: "You are an expert at analyzing visual content. Describe what you see in detail and provide insights about the content.",
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
