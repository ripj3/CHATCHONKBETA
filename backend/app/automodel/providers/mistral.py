"""
Mistral Provider - Mistral AI API Integration

This module provides integration with Mistral AI's API for the AutoModel system.
Mistral models are efficient and perform well on various language tasks.

Author: Rip Jonesy
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Union

import httpx
from pydantic import ValidationError

from app.automodel import TaskType, ProviderType
from .base import BaseProvider, Model, ProviderResponse

logger = logging.getLogger("chatchonk.automodel.providers.mistral")


class MistralProvider(BaseProvider):
    """Mistral AI provider implementation for the AutoModel system."""
    
    def __init__(self, api_key: Optional[str] = None, **kwargs):
        """
        Initialize the Mistral provider.
        
        Args:
            api_key: Mistral API key
            **kwargs: Additional configuration options
        """
        super().__init__(api_key, **kwargs)
        self.base_url = kwargs.get("base_url", "https://api.mistral.ai/v1")
        self.timeout = kwargs.get("timeout", 60)
        self._client: Optional[httpx.AsyncClient] = None
    
    @property
    def provider_type(self) -> ProviderType:
        """Return the provider type."""
        return ProviderType.MISTRAL
    
    @property
    def name(self) -> str:
        """Return the human-readable name of the provider."""
        return "Mistral AI"
    
    async def initialize(self) -> None:
        """Initialize the Mistral provider and load available models."""
        if self._is_initialized:
            return
            
        if not self.api_key:
            raise ValueError("Mistral API key is required")
        
        # Initialize HTTP client
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            timeout=self.timeout
        )
        
        # Load available models
        await self._load_models()
        
        self._is_initialized = True
        logger.info(f"Mistral provider initialized with {len(self._models)} models")
    
    async def _load_models(self) -> None:
        """Load available Mistral models and their capabilities."""
        # Define Mistral models with their capabilities
        model_configs = [
            {
                "id": "mistral-large-latest",
                "name": "Mistral Large",
                "description": "Most capable Mistral model for complex reasoning",
                "max_tokens": 32768,
                "supports_functions": True,
                "cost_per_1k_tokens": 0.008,
                "priority_score": 8.5,
                "supported_tasks": {
                    TaskType.TEXT_GENERATION, TaskType.SUMMARIZATION, TaskType.TOPIC_EXTRACTION,
                    TaskType.CLASSIFICATION, TaskType.SENSEMAKING, TaskType.PLANNING,
                    TaskType.TRANSLATION, TaskType.CHAT
                }
            },
            {
                "id": "mistral-medium-latest",
                "name": "Mistral Medium",
                "description": "Balanced model for most tasks",
                "max_tokens": 32768,
                "cost_per_1k_tokens": 0.0027,
                "priority_score": 7.5,
                "supported_tasks": {
                    TaskType.TEXT_GENERATION, TaskType.SUMMARIZATION, TaskType.TOPIC_EXTRACTION,
                    TaskType.CLASSIFICATION, TaskType.TRANSLATION, TaskType.CHAT
                }
            },
            {
                "id": "mistral-small-latest",
                "name": "Mistral Small",
                "description": "Fast and efficient model for simple tasks",
                "max_tokens": 32768,
                "cost_per_1k_tokens": 0.002,
                "priority_score": 6.5,
                "supported_tasks": {
                    TaskType.TEXT_GENERATION, TaskType.SUMMARIZATION, TaskType.CLASSIFICATION,
                    TaskType.TRANSLATION, TaskType.CHAT
                }
            }
        ]
        
        for config in model_configs:
            model = Model(
                id=config["id"],
                name=config["name"],
                provider=self.provider_type,
                description=config["description"],
                max_tokens=config["max_tokens"],
                supports_streaming=True,
                supports_functions=config.get("supports_functions", False),
                supports_vision=False,
                cost_per_1k_tokens=config["cost_per_1k_tokens"],
                supported_tasks=config["supported_tasks"],
                priority_score=config["priority_score"],
                is_available=True
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
        **kwargs
    ) -> ProviderResponse:
        """Process content using Mistral models."""
        if not self._is_initialized:
            await self.initialize()
        
        model = self.get_model(model_id)
        if not model:
            raise ValueError(f"Model {model_id} not found")
        
        if not self.supports_task(model_id, task_type):
            raise ValueError(f"Model {model_id} does not support task {task_type}")
        
        try:
            return await self._process_chat_completion(
                model_id, task_type, content, max_tokens, temperature,
                top_p, stop_sequences, session_context, **kwargs
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
        stop_sequences: Optional[List[str]],
        session_context: Optional[Dict[str, Any]],
        **kwargs
    ) -> ProviderResponse:
        """Process chat completion requests."""
        # Convert content to messages format
        messages = self._prepare_messages(task_type, content, session_context)
        
        payload = {
            "model": model_id,
            "messages": messages,
            "temperature": temperature,
            "top_p": top_p,
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
        tokens_used = result["usage"]["total_tokens"]
        finish_reason = choice["finish_reason"]
        
        return ProviderResponse(
            content=message_content,
            model_id=model_id,
            tokens_used=tokens_used,
            finish_reason=finish_reason,
            metadata={"prompt_tokens": result["usage"]["prompt_tokens"]}
        )
    
    def _prepare_messages(
        self,
        task_type: TaskType,
        content: Union[str, Dict[str, Any], List[Dict[str, Any]]],
        session_context: Optional[Dict[str, Any]]
    ) -> List[Dict[str, str]]:
        """Prepare messages for Mistral chat completion format."""
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
