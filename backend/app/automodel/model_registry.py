"""
Model Registry - Central Registry for AI Models and Providers

This module manages all AI providers and models in the AutoModel system.
It handles provider initialization, model discovery, health monitoring,
and intelligent model selection for tasks.

Author: Rip Jonesy
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple

from app.automodel import TaskType, ProviderType, ModelPriority
from app.automodel.providers import (
    BaseProvider, Model, ProviderResponse,
    OpenAIProvider, AnthropicProvider, HuggingFaceProvider,
    MistralProvider, DeepseekProvider, QwenProvider, OpenRouterProvider
)

logger = logging.getLogger("chatchonk.automodel.registry")


class ModelRegistry:
    """
    Central registry for managing AI providers and models.
    
    This class handles:
    - Provider initialization and management
    - Model discovery and registration
    - Health monitoring and availability tracking
    - Intelligent model selection for tasks
    - Performance metrics and optimization
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the model registry.
        
        Args:
            config: Configuration dictionary with provider settings
        """
        self.config = config or {}
        self._providers: Dict[ProviderType, BaseProvider] = {}
        self._models: Dict[str, Model] = {}
        self._provider_health: Dict[ProviderType, bool] = {}
        self._last_health_check: Dict[ProviderType, datetime] = {}
        self._performance_metrics: Dict[str, Dict[str, Any]] = {}
        self._is_initialized = False
        
        # Health check interval (5 minutes)
        self.health_check_interval = timedelta(minutes=5)
    
    async def initialize(self) -> None:
        """Initialize all configured providers and load their models."""
        if self._is_initialized:
            return
        
        logger.info("Initializing ModelRegistry...")
        
        # Initialize providers based on configuration
        await self._initialize_providers()
        
        # Load models from all providers
        await self._load_all_models()
        
        # Perform initial health checks
        await self._perform_health_checks()
        
        self._is_initialized = True
        logger.info(f"ModelRegistry initialized with {len(self._providers)} providers and {len(self._models)} models")
    
    async def _initialize_providers(self) -> None:
        """Initialize all configured providers."""
        provider_configs = {
            ProviderType.OPENAI: (OpenAIProvider, self.config.get("openai", {})),
            ProviderType.ANTHROPIC: (AnthropicProvider, self.config.get("anthropic", {})),
            ProviderType.HUGGINGFACE: (HuggingFaceProvider, self.config.get("huggingface", {})),
            ProviderType.MISTRAL: (MistralProvider, self.config.get("mistral", {})),
            ProviderType.DEEPSEEK: (DeepseekProvider, self.config.get("deepseek", {})),
            ProviderType.QWEN: (QwenProvider, self.config.get("qwen", {})),
            ProviderType.OPENROUTER: (OpenRouterProvider, self.config.get("openrouter", {})),
        }
        
        for provider_type, (provider_class, provider_config) in provider_configs.items():
            try:
                # Skip if no API key provided
                if not provider_config.get("api_key"):
                    logger.warning(f"No API key provided for {provider_type}, skipping initialization")
                    continue
                
                # Initialize provider
                provider = provider_class(**provider_config)
                await provider.initialize()
                
                self._providers[provider_type] = provider
                self._provider_health[provider_type] = True
                
                logger.info(f"Initialized {provider.name} provider")
                
            except Exception as e:
                logger.error(f"Failed to initialize {provider_type} provider: {str(e)}")
                self._provider_health[provider_type] = False
    
    async def _load_all_models(self) -> None:
        """Load models from all initialized providers."""
        for provider_type, provider in self._providers.items():
            try:
                models = provider.get_models()
                for model in models:
                    self._models[model.id] = model
                    # Initialize performance metrics
                    self._performance_metrics[model.id] = {
                        "total_requests": 0,
                        "successful_requests": 0,
                        "failed_requests": 0,
                        "average_response_time": 0.0,
                        "last_used": None,
                        "error_rate": 0.0
                    }
                
                logger.info(f"Loaded {len(models)} models from {provider.name}")
                
            except Exception as e:
                logger.error(f"Failed to load models from {provider_type}: {str(e)}")
    
    async def _perform_health_checks(self) -> None:
        """Perform health checks on all providers."""
        for provider_type, provider in self._providers.items():
            try:
                is_healthy = await provider.health_check()
                self._provider_health[provider_type] = is_healthy
                self._last_health_check[provider_type] = datetime.now()
                
                if not is_healthy:
                    logger.warning(f"Health check failed for {provider.name}: {provider.last_error}")
                
            except Exception as e:
                logger.error(f"Health check error for {provider_type}: {str(e)}")
                self._provider_health[provider_type] = False
    
    def get_model(self, model_id: str) -> Optional[Model]:
        """
        Get a model by its ID.
        
        Args:
            model_id: ID of the model to retrieve
            
        Returns:
            Model object or None if not found
        """
        return self._models.get(model_id)
    
    def get_models_for_task(self, task_type: TaskType) -> List[Model]:
        """
        Get all models that support a specific task type.
        
        Args:
            task_type: Task type to find models for
            
        Returns:
            List of models that support the task
        """
        suitable_models = []
        
        for model in self._models.values():
            if (task_type in model.supported_tasks and 
                model.is_available and 
                self._provider_health.get(model.provider, False)):
                suitable_models.append(model)
        
        return suitable_models
    
    def get_best_model_for_task(
        self, 
        task_type: TaskType, 
        priority: ModelPriority = ModelPriority.MEDIUM,
        exclude_providers: Optional[Set[ProviderType]] = None
    ) -> Optional[Model]:
        """
        Get the best model for a specific task type.
        
        Args:
            task_type: Task type to find a model for
            priority: Priority level for model selection
            exclude_providers: Providers to exclude from selection
            
        Returns:
            Best model for the task or None if no suitable model found
        """
        exclude_providers = exclude_providers or set()
        suitable_models = []
        
        for model in self._models.values():
            if (task_type in model.supported_tasks and 
                model.is_available and 
                model.provider not in exclude_providers and
                self._provider_health.get(model.provider, False)):
                suitable_models.append(model)
        
        if not suitable_models:
            return None
        
        # Sort models by multiple criteria
        def model_score(model: Model) -> float:
            base_score = model.priority_score
            
            # Adjust score based on performance metrics
            metrics = self._performance_metrics.get(model.id, {})
            error_rate = metrics.get("error_rate", 0.0)
            avg_response_time = metrics.get("average_response_time", 0.0)
            
            # Penalize high error rates
            if error_rate > 0.1:  # More than 10% error rate
                base_score *= (1.0 - error_rate)
            
            # Slightly favor faster models
            if avg_response_time > 0:
                time_penalty = min(avg_response_time / 10.0, 0.2)  # Max 20% penalty
                base_score *= (1.0 - time_penalty)
            
            # Adjust based on priority requirements
            if priority == ModelPriority.HIGH and model.priority_score < 8.0:
                base_score *= 0.8
            elif priority == ModelPriority.CRITICAL and model.priority_score < 9.0:
                base_score *= 0.7
            
            return base_score
        
        # Sort by calculated score (higher is better)
        suitable_models.sort(key=model_score, reverse=True)
        return suitable_models[0]
    
    def get_provider(self, provider_type: ProviderType) -> Optional[BaseProvider]:
        """
        Get a provider by its type.
        
        Args:
            provider_type: Type of provider to retrieve
            
        Returns:
            Provider instance or None if not found
        """
        return self._providers.get(provider_type)
    
    def get_available_providers(self) -> List[ProviderType]:
        """
        Get list of available (healthy) providers.
        
        Returns:
            List of available provider types
        """
        return [
            provider_type for provider_type, is_healthy in self._provider_health.items()
            if is_healthy
        ]
    
    def update_model_metrics(
        self, 
        model_id: str, 
        success: bool, 
        response_time: float,
        error: Optional[str] = None
    ) -> None:
        """
        Update performance metrics for a model.
        
        Args:
            model_id: ID of the model
            success: Whether the request was successful
            response_time: Response time in seconds
            error: Error message if request failed
        """
        if model_id not in self._performance_metrics:
            return
        
        metrics = self._performance_metrics[model_id]
        metrics["total_requests"] += 1
        metrics["last_used"] = datetime.now()
        
        if success:
            metrics["successful_requests"] += 1
            # Update average response time
            current_avg = metrics["average_response_time"]
            total_successful = metrics["successful_requests"]
            metrics["average_response_time"] = (
                (current_avg * (total_successful - 1) + response_time) / total_successful
            )
        else:
            metrics["failed_requests"] += 1
            if error:
                logger.warning(f"Model {model_id} error: {error}")
        
        # Update error rate
        total_requests = metrics["total_requests"]
        failed_requests = metrics["failed_requests"]
        metrics["error_rate"] = failed_requests / total_requests if total_requests > 0 else 0.0
    
    async def health_check_if_needed(self) -> None:
        """Perform health checks if enough time has passed since the last check."""
        now = datetime.now()
        
        for provider_type, provider in self._providers.items():
            last_check = self._last_health_check.get(provider_type)
            
            if (not last_check or 
                now - last_check > self.health_check_interval):
                
                try:
                    is_healthy = await provider.health_check()
                    self._provider_health[provider_type] = is_healthy
                    self._last_health_check[provider_type] = now
                    
                    if not is_healthy:
                        logger.warning(f"Health check failed for {provider.name}")
                        
                except Exception as e:
                    logger.error(f"Health check error for {provider_type}: {str(e)}")
                    self._provider_health[provider_type] = False
    
    def get_registry_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the registry.
        
        Returns:
            Dictionary with registry statistics
        """
        total_models = len(self._models)
        available_models = sum(
            1 for model in self._models.values()
            if model.is_available and self._provider_health.get(model.provider, False)
        )
        
        provider_stats = {}
        for provider_type, provider in self._providers.items():
            models = [m for m in self._models.values() if m.provider == provider_type]
            provider_stats[provider_type.value] = {
                "name": provider.name,
                "healthy": self._provider_health.get(provider_type, False),
                "models": len(models),
                "last_health_check": self._last_health_check.get(provider_type)
            }
        
        return {
            "total_providers": len(self._providers),
            "healthy_providers": sum(self._provider_health.values()),
            "total_models": total_models,
            "available_models": available_models,
            "providers": provider_stats,
            "initialized": self._is_initialized
        }
    
    async def shutdown(self) -> None:
        """Shutdown all providers and clean up resources."""
        logger.info("Shutting down ModelRegistry...")
        
        for provider in self._providers.values():
            try:
                if hasattr(provider, '__aexit__'):
                    await provider.__aexit__(None, None, None)
            except Exception as e:
                logger.error(f"Error shutting down provider: {str(e)}")
        
        self._providers.clear()
        self._models.clear()
        self._provider_health.clear()
        self._performance_metrics.clear()
        self._is_initialized = False
