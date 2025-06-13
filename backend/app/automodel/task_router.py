"""
Task Router - Intelligent Task Routing for AutoModel System

This module handles intelligent routing of tasks to the most appropriate
AI models based on task type, model capabilities, performance metrics,
and availability. It implements the core "AutoSwap" logic.

Author: Rip Jonesy
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from app.automodel import TaskType, ProviderType, ModelPriority
from app.automodel.providers import Model, ProviderResponse
from app.automodel.model_registry import ModelRegistry

logger = logging.getLogger("chatchonk.automodel.router")


class TaskRouter:
    """
    Intelligent task router for the AutoModel system.

    This class implements the core "AutoSwap" functionality by:
    - Analyzing task requirements and selecting optimal models
    - Implementing fallback strategies when primary models fail
    - Load balancing across available providers
    - Learning from performance metrics to improve routing decisions
    """

    def __init__(self, model_registry: ModelRegistry):
        """
        Initialize the task router.

        Args:
            model_registry: ModelRegistry instance for accessing models and providers
        """
        self.model_registry = model_registry
        self._routing_cache: Dict[str, Tuple[str, datetime]] = {}
        self._fallback_chains: Dict[TaskType, List[ProviderType]] = {}
        self._load_balancing: Dict[ProviderType, int] = {}

        # Initialize fallback chains for different task types
        self._initialize_fallback_chains()

    def _initialize_fallback_chains(self) -> None:
        """Initialize fallback chains for different task types."""
        # Define preferred provider order for each task type
        self._fallback_chains = {
            TaskType.TEXT_GENERATION: [
                ProviderType.OPENAI,
                ProviderType.ANTHROPIC,
                ProviderType.MISTRAL,
                ProviderType.DEEPSEEK,
                ProviderType.QWEN,
                ProviderType.HUGGINGFACE,
            ],
            TaskType.SUMMARIZATION: [
                ProviderType.ANTHROPIC,
                ProviderType.OPENAI,
                ProviderType.MISTRAL,
                ProviderType.QWEN,
                ProviderType.HUGGINGFACE,
            ],
            TaskType.TOPIC_EXTRACTION: [
                ProviderType.ANTHROPIC,
                ProviderType.OPENAI,
                ProviderType.HUGGINGFACE,
                ProviderType.MISTRAL,
                ProviderType.QWEN,
            ],
            TaskType.CLASSIFICATION: [
                ProviderType.HUGGINGFACE,
                ProviderType.OPENAI,
                ProviderType.ANTHROPIC,
                ProviderType.MISTRAL,
                ProviderType.QWEN,
            ],
            TaskType.EMBEDDING: [ProviderType.OPENAI, ProviderType.HUGGINGFACE],
            TaskType.SENSEMAKING: [
                ProviderType.ANTHROPIC,
                ProviderType.OPENAI,
                ProviderType.DEEPSEEK,
                ProviderType.MISTRAL,
                ProviderType.QWEN,
            ],
            TaskType.PLANNING: [
                ProviderType.ANTHROPIC,
                ProviderType.OPENAI,
                ProviderType.DEEPSEEK,
                ProviderType.MISTRAL,
                ProviderType.QWEN,
            ],
            TaskType.MEDIA_ANALYSIS: [ProviderType.OPENAI, ProviderType.ANTHROPIC],
            TaskType.TRANSLATION: [
                ProviderType.QWEN,
                ProviderType.OPENAI,
                ProviderType.ANTHROPIC,
                ProviderType.MISTRAL,
                ProviderType.HUGGINGFACE,
            ],
            TaskType.CHAT: [
                ProviderType.OPENAI,
                ProviderType.ANTHROPIC,
                ProviderType.MISTRAL,
                ProviderType.DEEPSEEK,
                ProviderType.QWEN,
                ProviderType.HUGGINGFACE,
            ],
        }

    async def route_task(
        self,
        task_type: TaskType,
        content: Union[str, Dict[str, Any], List[Dict[str, Any]]],
        priority: ModelPriority = ModelPriority.MEDIUM,
        preferred_providers: Optional[List[ProviderType]] = None,
        excluded_providers: Optional[Set[ProviderType]] = None,
        model_requirements: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> ProviderResponse:
        """
        Route a task to the most appropriate model and execute it.

        Args:
            task_type: Type of task to perform
            content: Content to process
            priority: Priority level for model selection
            preferred_providers: Preferred providers to use (in order)
            excluded_providers: Providers to exclude from selection
            model_requirements: Specific model requirements (e.g., max_tokens, supports_vision)
            **kwargs: Additional parameters for model processing

        Returns:
            ProviderResponse from the selected model

        Raises:
            ValueError: If no suitable model is found
            Exception: If all attempts fail
        """
        # Ensure registry is up to date
        await self.model_registry.health_check_if_needed()

        # Get candidate models
        candidate_models = self._get_candidate_models(
            task_type,
            priority,
            preferred_providers,
            excluded_providers,
            model_requirements,
        )

        if not candidate_models:
            raise ValueError(f"No suitable models found for task {task_type}")

        # Try models in order until one succeeds
        last_error = None
        for model in candidate_models:
            try:
                provider = self.model_registry.get_provider(model.provider)
                if not provider:
                    continue

                # Record attempt start time
                start_time = datetime.now()

                # Execute the task
                response = await provider.process(
                    task_type=task_type, model_id=model.id, content=content, **kwargs
                )

                # Record success metrics
                response_time = (datetime.now() - start_time).total_seconds()
                self.model_registry.update_model_metrics(
                    model.id, success=True, response_time=response_time
                )

                # Update load balancing
                self._load_balancing[model.provider] = (
                    self._load_balancing.get(model.provider, 0) + 1
                )

                logger.info(
                    f"Task {task_type} completed successfully using {model.name}"
                )
                return response

            except Exception as e:
                # Record failure metrics
                response_time = (datetime.now() - start_time).total_seconds()
                self.model_registry.update_model_metrics(
                    model.id, success=False, response_time=response_time, error=str(e)
                )

                last_error = e
                logger.warning(f"Task failed with {model.name}: {str(e)}")
                continue

        # If we get here, all models failed
        raise Exception(
            f"All models failed for task {task_type}. Last error: {str(last_error)}"
        )

    def _get_candidate_models(
        self,
        task_type: TaskType,
        priority: ModelPriority,
        preferred_providers: Optional[List[ProviderType]],
        excluded_providers: Optional[Set[ProviderType]],
        model_requirements: Optional[Dict[str, Any]],
    ) -> List[Model]:
        """Get candidate models for a task, ordered by preference."""
        excluded_providers = excluded_providers or set()
        model_requirements = model_requirements or {}

        # Get all models that support the task
        suitable_models = self.model_registry.get_models_for_task(task_type)

        # Filter by requirements
        filtered_models = []
        for model in suitable_models:
            if model.provider in excluded_providers:
                continue

            # Check model requirements
            if not self._meets_requirements(model, model_requirements):
                continue

            filtered_models.append(model)

        if not filtered_models:
            return []

        # Sort models by preference
        return self._sort_models_by_preference(
            filtered_models, task_type, priority, preferred_providers
        )

    def _meets_requirements(self, model: Model, requirements: Dict[str, Any]) -> bool:
        """Check if a model meets the specified requirements."""
        for req_key, req_value in requirements.items():
            if req_key == "min_max_tokens" and model.max_tokens < req_value:
                return False
            elif (
                req_key == "supports_vision" and req_value and not model.supports_vision
            ):
                return False
            elif (
                req_key == "supports_functions"
                and req_value
                and not model.supports_functions
            ):
                return False
            elif (
                req_key == "max_cost_per_1k_tokens"
                and model.cost_per_1k_tokens
                and model.cost_per_1k_tokens > req_value
            ):
                return False

        return True

    def _sort_models_by_preference(
        self,
        models: List[Model],
        task_type: TaskType,
        priority: ModelPriority,
        preferred_providers: Optional[List[ProviderType]],
    ) -> List[Model]:
        """Sort models by preference for the given task."""

        def model_preference_score(model: Model) -> Tuple[int, float, float]:
            # Primary sort: preferred providers (if specified)
            if preferred_providers:
                try:
                    provider_preference = preferred_providers.index(model.provider)
                except ValueError:
                    provider_preference = len(preferred_providers)
            else:
                # Use fallback chain preference
                fallback_chain = self._fallback_chains.get(task_type, [])
                try:
                    provider_preference = fallback_chain.index(model.provider)
                except ValueError:
                    provider_preference = len(fallback_chain)

            # Secondary sort: model priority score (higher is better, so negate)
            priority_score = -model.priority_score

            # Tertiary sort: load balancing (prefer less used providers)
            load_balance_score = self._load_balancing.get(model.provider, 0)

            return (provider_preference, priority_score, load_balance_score)

        # Sort by preference (lower scores are better)
        models.sort(key=model_preference_score)
        return models

    async def get_model_recommendation(
        self,
        task_type: TaskType,
        priority: ModelPriority = ModelPriority.MEDIUM,
        model_requirements: Optional[Dict[str, Any]] = None,
    ) -> Optional[Model]:
        """
        Get a model recommendation for a task without executing it.

        Args:
            task_type: Type of task
            priority: Priority level
            model_requirements: Model requirements

        Returns:
            Recommended model or None if no suitable model found
        """
        await self.model_registry.health_check_if_needed()

        candidate_models = self._get_candidate_models(
            task_type, priority, None, None, model_requirements
        )

        return candidate_models[0] if candidate_models else None

    def get_task_capabilities(self, task_type: TaskType) -> Dict[str, Any]:
        """
        Get information about available capabilities for a task type.

        Args:
            task_type: Task type to analyze

        Returns:
            Dictionary with capability information
        """
        models = self.model_registry.get_models_for_task(task_type)

        if not models:
            return {
                "available": False,
                "model_count": 0,
                "providers": [],
                "capabilities": {},
            }

        providers = list(set(model.provider for model in models))

        # Aggregate capabilities
        capabilities = {
            "supports_vision": any(model.supports_vision for model in models),
            "supports_functions": any(model.supports_functions for model in models),
            "supports_streaming": any(model.supports_streaming for model in models),
            "max_tokens": max(model.max_tokens for model in models),
            "min_cost_per_1k_tokens": (
                min(
                    model.cost_per_1k_tokens
                    for model in models
                    if model.cost_per_1k_tokens is not None
                )
                if any(model.cost_per_1k_tokens is not None for model in models)
                else None
            ),
        }

        return {
            "available": True,
            "model_count": len(models),
            "providers": [p.value for p in providers],
            "capabilities": capabilities,
            "best_model": models[0].name if models else None,
        }

    def get_routing_stats(self) -> Dict[str, Any]:
        """
        Get statistics about task routing.

        Returns:
            Dictionary with routing statistics
        """
        total_requests = sum(self._load_balancing.values())

        provider_distribution = {}
        for provider_type, count in self._load_balancing.items():
            percentage = (count / total_requests * 100) if total_requests > 0 else 0
            provider_distribution[provider_type.value] = {
                "requests": count,
                "percentage": round(percentage, 2),
            }

        return {
            "total_requests": total_requests,
            "provider_distribution": provider_distribution,
            "fallback_chains": {
                task_type.value: [p.value for p in providers]
                for task_type, providers in self._fallback_chains.items()
            },
        }
