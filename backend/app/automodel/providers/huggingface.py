"""
HuggingFace Provider - HuggingFace Inference API Integration

This module provides integration with HuggingFace's Inference API for the AutoModel system.
HuggingFace excels at specialized models for embeddings, classification, and domain-specific tasks.

Author: Rip Jonesy
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Union

import httpx
from pydantic import ValidationError

from app.automodel import TaskType, ProviderType
from .base import BaseProvider, Model, ProviderResponse

logger = logging.getLogger("chatchonk.automodel.providers.huggingface")


class HuggingFaceProvider(BaseProvider):
    """HuggingFace provider implementation for the AutoModel system."""
    
    def __init__(self, api_key: Optional[str] = None, **kwargs):
        """
        Initialize the HuggingFace provider.
        
        Args:
            api_key: HuggingFace API token
            **kwargs: Additional configuration options
        """
        super().__init__(api_key, **kwargs)
        self.base_url = kwargs.get("base_url", "https://api-inference.huggingface.co")
        self.timeout = kwargs.get("timeout", 60)
        self._client: Optional[httpx.AsyncClient] = None
    
    @property
    def provider_type(self) -> ProviderType:
        """Return the provider type."""
        return ProviderType.HUGGINGFACE
    
    @property
    def name(self) -> str:
        """Return the human-readable name of the provider."""
        return "HuggingFace"
    
    async def initialize(self) -> None:
        """Initialize the HuggingFace provider and load available models."""
        if self._is_initialized:
            return
            
        if not self.api_key:
            raise ValueError("HuggingFace API token is required")
        
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
        logger.info(f"HuggingFace provider initialized with {len(self._models)} models")
    
    async def _load_models(self) -> None:
        """Load available HuggingFace models and their capabilities."""
        # Define HuggingFace models with their capabilities
        model_configs = [
            # Text Generation Models
            {
                "id": "microsoft/DialoGPT-large",
                "name": "DialoGPT Large",
                "description": "Conversational AI model for chat applications",
                "max_tokens": 1024,
                "cost_per_1k_tokens": 0.0,  # Free tier
                "priority_score": 6.0,
                "supported_tasks": {TaskType.TEXT_GENERATION, TaskType.CHAT}
            },
            {
                "id": "google/flan-t5-large",
                "name": "FLAN-T5 Large",
                "description": "Instruction-tuned model for various text tasks",
                "max_tokens": 512,
                "cost_per_1k_tokens": 0.0,
                "priority_score": 7.0,
                "supported_tasks": {
                    TaskType.TEXT_GENERATION, TaskType.SUMMARIZATION, 
                    TaskType.TRANSLATION, TaskType.CLASSIFICATION
                }
            },
            
            # Embedding Models
            {
                "id": "sentence-transformers/all-MiniLM-L6-v2",
                "name": "All-MiniLM-L6-v2",
                "description": "High-quality sentence embeddings",
                "max_tokens": 256,
                "cost_per_1k_tokens": 0.0,
                "priority_score": 8.0,
                "supported_tasks": {TaskType.EMBEDDING}
            },
            {
                "id": "sentence-transformers/all-mpnet-base-v2",
                "name": "All-MPNet-Base-v2",
                "description": "High-performance sentence embeddings",
                "max_tokens": 384,
                "cost_per_1k_tokens": 0.0,
                "priority_score": 8.5,
                "supported_tasks": {TaskType.EMBEDDING}
            },
            
            # Classification Models
            {
                "id": "cardiffnlp/twitter-roberta-base-sentiment-latest",
                "name": "Twitter RoBERTa Sentiment",
                "description": "Sentiment analysis for social media text",
                "max_tokens": 512,
                "cost_per_1k_tokens": 0.0,
                "priority_score": 7.5,
                "supported_tasks": {TaskType.CLASSIFICATION}
            },
            {
                "id": "facebook/bart-large-mnli",
                "name": "BART Large MNLI",
                "description": "Zero-shot text classification",
                "max_tokens": 1024,
                "cost_per_1k_tokens": 0.0,
                "priority_score": 8.0,
                "supported_tasks": {TaskType.CLASSIFICATION, TaskType.TOPIC_EXTRACTION}
            },
            
            # Summarization Models
            {
                "id": "facebook/bart-large-cnn",
                "name": "BART Large CNN",
                "description": "News article summarization",
                "max_tokens": 1024,
                "cost_per_1k_tokens": 0.0,
                "priority_score": 7.5,
                "supported_tasks": {TaskType.SUMMARIZATION}
            },
            {
                "id": "google/pegasus-xsum",
                "name": "Pegasus XSum",
                "description": "Abstractive summarization",
                "max_tokens": 512,
                "cost_per_1k_tokens": 0.0,
                "priority_score": 7.0,
                "supported_tasks": {TaskType.SUMMARIZATION}
            }
        ]
        
        for config in model_configs:
            model = Model(
                id=config["id"],
                name=config["name"],
                provider=self.provider_type,
                description=config["description"],
                max_tokens=config["max_tokens"],
                supports_streaming=False,  # HF Inference API doesn't support streaming
                supports_functions=False,
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
        """Process content using HuggingFace models."""
        if not self._is_initialized:
            await self.initialize()
        
        model = self.get_model(model_id)
        if not model:
            raise ValueError(f"Model {model_id} not found")
        
        if not self.supports_task(model_id, task_type):
            raise ValueError(f"Model {model_id} does not support task {task_type}")
        
        try:
            if task_type == TaskType.EMBEDDING:
                return await self._process_embedding(model_id, content)
            elif task_type == TaskType.CLASSIFICATION:
                return await self._process_classification(model_id, content, **kwargs)
            elif task_type == TaskType.SUMMARIZATION:
                return await self._process_summarization(model_id, content, max_tokens)
            elif task_type in [TaskType.TEXT_GENERATION, TaskType.CHAT]:
                return await self._process_text_generation(model_id, content, max_tokens, temperature)
            else:
                # Default to text generation for other tasks
                return await self._process_text_generation(model_id, content, max_tokens, temperature)
        except Exception as e:
            self._set_error(f"Processing failed: {str(e)}")
            raise
    
    async def _process_embedding(self, model_id: str, content: Union[str, List[str]]) -> ProviderResponse:
        """Process embedding requests."""
        if isinstance(content, str):
            inputs = [content]
        elif isinstance(content, list):
            inputs = [str(item) for item in content]
        else:
            inputs = [str(content)]
        
        payload = {"inputs": inputs}
        
        response = await self._client.post(f"/models/{model_id}", json=payload)
        response.raise_for_status()
        
        result = response.json()
        
        # HuggingFace returns embeddings as nested arrays
        if isinstance(result, list) and len(result) > 0:
            embedding = result[0] if isinstance(result[0], list) else result
        else:
            embedding = result
        
        return ProviderResponse(
            content=embedding,
            model_id=model_id,
            tokens_used=None,  # HF doesn't provide token counts
            finish_reason="completed",
            metadata={"embedding_dimension": len(embedding) if isinstance(embedding, list) else None}
        )
    
    async def _process_classification(self, model_id: str, content: str, **kwargs) -> ProviderResponse:
        """Process classification requests."""
        candidate_labels = kwargs.get("candidate_labels", ["positive", "negative", "neutral"])
        
        if "mnli" in model_id.lower():
            # Zero-shot classification
            payload = {
                "inputs": content,
                "parameters": {"candidate_labels": candidate_labels}
            }
        else:
            # Regular classification
            payload = {"inputs": content}
        
        response = await self._client.post(f"/models/{model_id}", json=payload)
        response.raise_for_status()
        
        result = response.json()
        
        return ProviderResponse(
            content=result,
            model_id=model_id,
            tokens_used=None,
            finish_reason="completed",
            metadata={"classification_type": "zero_shot" if "mnli" in model_id.lower() else "standard"}
        )
    
    async def _process_summarization(self, model_id: str, content: str, max_tokens: Optional[int]) -> ProviderResponse:
        """Process summarization requests."""
        payload = {
            "inputs": content,
            "parameters": {}
        }
        
        if max_tokens:
            payload["parameters"]["max_length"] = max_tokens
        
        response = await self._client.post(f"/models/{model_id}", json=payload)
        response.raise_for_status()
        
        result = response.json()
        
        # Extract summary text
        if isinstance(result, list) and len(result) > 0:
            summary = result[0].get("summary_text", str(result[0]))
        else:
            summary = str(result)
        
        return ProviderResponse(
            content=summary,
            model_id=model_id,
            tokens_used=None,
            finish_reason="completed",
            metadata={"task": "summarization"}
        )
    
    async def _process_text_generation(
        self, 
        model_id: str, 
        content: str, 
        max_tokens: Optional[int], 
        temperature: float
    ) -> ProviderResponse:
        """Process text generation requests."""
        payload = {
            "inputs": content,
            "parameters": {
                "temperature": temperature,
                "return_full_text": False
            }
        }
        
        if max_tokens:
            payload["parameters"]["max_new_tokens"] = max_tokens
        
        response = await self._client.post(f"/models/{model_id}", json=payload)
        response.raise_for_status()
        
        result = response.json()
        
        # Extract generated text
        if isinstance(result, list) and len(result) > 0:
            generated_text = result[0].get("generated_text", str(result[0]))
        else:
            generated_text = str(result)
        
        return ProviderResponse(
            content=generated_text,
            model_id=model_id,
            tokens_used=None,
            finish_reason="completed",
            metadata={"task": "text_generation"}
        )
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._client:
            await self._client.aclose()
