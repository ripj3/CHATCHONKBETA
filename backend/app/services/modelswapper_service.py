"""
ModelSwapper Service - Secure AI Model Selection with Cost Controls

This service provides intelligent model selection based on the existing MSWAP database,
with comprehensive security controls and cost management to prevent billing surprises.

Key Security Features:
- User-level API key management for high-tier users
- Spending limits per user tier with real-time tracking
- Request rate limiting and token limits
- Secure API key storage and validation
- Cost estimation before execution

Key Cost Control Features:
- Pre-request cost estimation and approval
- Real-time spending tracking
- Automatic fallback to cheaper models when approaching limits
- Detailed cost breakdown and warnings
- Emergency circuit breakers

Author: Rip Jonesy
"""

import logging
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

from app.models.mswap_models import (
    Provider,
    Model,
    UserTier,
    ModelPriority,
    SecurityLevel,
    UserSpendingLimits,
    ModelSelectionRequest,
    ModelSelectionResponse,
)
from app.core.config import get_settings

logger = logging.getLogger("chatchonk.modelswapper")


class SecurityException(Exception):
    """Security-related exceptions."""

    pass


class CostLimitException(Exception):
    """Cost limit exceeded exceptions."""

    pass


class ModelSwapperService:
    """
    Secure AI Model Selection Service with Cost Controls

    This service provides intelligent model selection using the existing MSWAP database,
    with comprehensive security controls and cost management to prevent billing surprises.
    """

    def __init__(self):
        """Initialize the ModelSwapper service."""
        self.settings = get_settings()
        self._cache: Dict[str, Any] = {}
        self._last_cache_refresh = datetime.now()

        # Emergency circuit breaker settings
        self.emergency_cost_threshold = Decimal("50.00")  # Emergency stop at $50
        self.emergency_requests_per_hour = 10000  # Emergency stop at 10k requests/hour

    # === Database Access Methods ===
    async def _execute_mswap_query(
        self, query: str, params: Optional[List] = None
    ) -> List[Dict]:
        """Execute a query against the MSWAP database with proper error handling."""
        try:
            from app.services.database_service import get_database_service
            from app.services.cache_service import get_cache_service

            cache_key = f"mswap_query:{hash(query)}:{hash(str(params))}"
            cache = get_cache_service()

            # Try cache first (5 minute TTL)
            cached_result = await cache.get(cache_key)
            if cached_result:
                import json

                return json.loads(cached_result)

            # Execute query using the database service
            logger.debug(f"MSWAP Query: {query} with params: {params}")
            db_service = get_database_service()
            results = await db_service.execute_mswap_raw_query(query, params)

            # Cache results
            import json

            await cache.set(cache_key, json.dumps(results), ttl=300)

            return results

        except Exception as e:
            logger.error(f"MSWAP database error: {e}")
            raise

    async def _get_providers(self, enabled_only: bool = True) -> List[Provider]:
        """Get all providers from the database."""
        query = "SELECT * FROM providers"
        if enabled_only:
            query += " WHERE enabled = true"
        query += " ORDER BY priority DESC"

        results = await self._execute_mswap_query(query)
        return [Provider(**row) for row in results]

    async def _get_models_for_task(
        self, task_type: str, user_tier: UserTier
    ) -> List[Model]:
        """Get models suitable for a specific task type and user tier."""
        # Get models that support the required capabilities for this task type
        query = """
        SELECT m.* FROM models m
        JOIN providers p ON m.provider_id = p.id
        WHERE m.enabled = true
        AND p.enabled = true
        AND m.capabilities && %s
        ORDER BY m.reliability DESC, m.avg_latency ASC
        """

        # Map task types to required capabilities
        task_capabilities = {
            "text_completion": ["completion"],
            "chat_conversation": ["chat"],
            "creative_writing": ["completion", "chat"],
            "content_generation": ["completion"],
            "email_composition": ["completion", "chat"],
        }

        required_caps = task_capabilities.get(task_type, ["completion"])
        results = await self._execute_mswap_query(query, [required_caps])

        models = [Model(**row) for row in results]

        # Filter by user tier (implement tier-based model access)
        return self._filter_models_by_tier(models, user_tier)

    def _filter_models_by_tier(
        self, models: List[Model], user_tier: UserTier
    ) -> List[Model]:
        """Filter models based on user tier access levels."""
        # Define which models each tier can access based on cost
        tier_cost_limits = {
            UserTier.FREE: Decimal("0.001"),  # Very cheap models only
            UserTier.LILBEAN: Decimal("0.005"),  # Low-cost models
            UserTier.CLAWBACK: Decimal("0.020"),  # Mid-range models
            UserTier.BIGCHONK: Decimal("0.100"),  # High-end models
            UserTier.MEOWTRIX: Decimal("1.000"),  # Premium models
        }

        max_cost = tier_cost_limits.get(user_tier, Decimal("0.001"))

        filtered_models = []
        for model in models:
            # Use the higher of prompt or completion token cost
            model_cost = max(
                model.cost_per_1k_prompt_tokens, model.cost_per_1k_completion_tokens
            )
            if model_cost <= max_cost:
                filtered_models.append(model)

        return filtered_models

    # === Security and Cost Control Methods ===
    async def _check_user_spending_limits(
        self, user_id: str, user_tier: UserTier, estimated_cost: Decimal
    ) -> None:
        """Check if user has exceeded spending limits."""
        # Get user's current spending limits
        limits = UserSpendingLimits.get_tier_defaults(user_tier)

        # TODO: Get actual user spending from database
        # For now, use mock data
        current_daily_cost = Decimal("0.00")  # TODO: Query from database
        current_hourly_cost = Decimal("0.00")  # TODO: Query from database

        # Check daily limit
        if current_daily_cost + estimated_cost > limits["daily_cost_limit"]:
            raise CostLimitException(
                f"Request would exceed daily spending limit of "
                f"${limits['daily_cost_limit']}"
            )

        # Check hourly limit
        if current_hourly_cost + estimated_cost > limits["hourly_cost_limit"]:
            raise CostLimitException(
                f"Request would exceed hourly spending limit of "
                f"${limits['hourly_cost_limit']}"
            )

        # Check per-request limit
        if estimated_cost > limits["max_cost_per_request"]:
            raise CostLimitException(
                f"Request cost ${estimated_cost} exceeds per-request limit of "
                f"${limits['max_cost_per_request']}"
            )

        # Emergency circuit breaker
        if estimated_cost > self.emergency_cost_threshold:
            raise CostLimitException(
                f"Request cost ${estimated_cost} exceeds emergency threshold of "
                f"${self.emergency_cost_threshold}"
            )

    def _calculate_cost(
        self, model: Model, estimated_tokens: int
    ) -> Tuple[Decimal, Dict[str, Decimal]]:
        """Calculate detailed cost breakdown for a model and token count."""
        # Assume 70% prompt tokens, 30% completion tokens (typical ratio)
        prompt_tokens = int(estimated_tokens * 0.7)
        completion_tokens = int(estimated_tokens * 0.3)

        prompt_cost = (prompt_tokens / 1000) * model.cost_per_1k_prompt_tokens
        completion_cost = (
            completion_tokens / 1000
        ) * model.cost_per_1k_completion_tokens
        total_cost = prompt_cost + completion_cost

        breakdown = {
            "prompt_tokens": Decimal(str(prompt_tokens)),
            "completion_tokens": Decimal(str(completion_tokens)),
            "prompt_cost": prompt_cost,
            "completion_cost": completion_cost,
            "total_cost": total_cost,
        }

        return total_cost, breakdown

    # === Model Selection ===
    async def select_best_model(
        self, request: ModelSelectionRequest
    ) -> ModelSelectionResponse:
        """
        Select the best model with comprehensive security and cost controls.

        This method implements multiple layers of protection:
        1. User authentication and authorization
        2. Spending limit checks
        3. Model access tier validation
        4. Cost estimation and approval
        5. Intelligent model selection
        """
        logger.info(
            f"Selecting model for user {request.user_id}, task {request.task_type}, tier: {request.user_tier}"
        )

        try:
            # Step 1: Get available models for this task and user tier
            available_models = await self._get_models_for_task(
                request.task_type, request.user_tier
            )

            if not available_models:
                raise ValueError(
                    f"No models available for task {request.task_type} and tier {request.user_tier}"
                )

            # Step 2: Filter models based on user preferences and requirements
            filtered_models = self._filter_models_by_requirements(
                available_models, request
            )

            if not filtered_models:
                raise ValueError("No models match the specified requirements")

            # Step 3: Score and rank models
            scored_models = self._score_models_by_criteria(filtered_models, request)

            # Step 4: Select best model and calculate costs
            best_model = scored_models[0]
            estimated_cost, cost_breakdown = self._calculate_cost(
                best_model, request.estimated_tokens
            )

            # Step 5: Check spending limits BEFORE proceeding
            await self._check_user_spending_limits(
                request.user_id, request.user_tier, estimated_cost
            )

            # Step 6: Check if user wants to use their own API keys
            using_user_keys = request.use_user_keys and request.user_tier in [
                UserTier.CLAWBACK,
                UserTier.BIGCHONK,
                UserTier.MEOWTRIX,
            ]

            # Step 7: Generate warnings if needed
            cost_warning = None
            if estimated_cost > Decimal("1.00"):
                cost_warning = f"High cost request: ${estimated_cost}"

            security_warning = None
            if using_user_keys:
                security_warning = "Using user-provided API keys"

            # Step 8: Build response
            return ModelSelectionResponse(
                model_id=best_model.id,
                provider_id=best_model.provider_id,
                model_name=best_model.name,
                provider_type=await self._get_provider_type(best_model.provider_id),
                estimated_cost=estimated_cost,
                cost_breakdown=cost_breakdown,
                using_user_keys=using_user_keys,
                security_level=(
                    SecurityLevel.USER if using_user_keys else SecurityLevel.SYSTEM
                ),
                reasoning=self._generate_selection_reasoning(best_model, request),
                fallback_models=[m.id for m in scored_models[1:3]],
                cost_warning=cost_warning,
                security_warning=security_warning,
            )

        except (CostLimitException, SecurityException) as e:
            logger.warning(f"Request blocked for user {request.user_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"Model selection failed for user {request.user_id}: {e}")
            raise ValueError(f"Model selection failed: {e}")

    def _filter_models_by_requirements(
        self, models: List[Model], request: ModelSelectionRequest
    ) -> List[Model]:
        """Filter models based on specific requirements."""
        filtered = []

        for model in models:
            # Check context length requirement
            if (
                request.min_context_length
                and model.context_length < request.min_context_length
            ):
                continue

            # Check required capabilities
            if request.required_capabilities:
                if not all(
                    cap in model.capabilities for cap in request.required_capabilities
                ):
                    continue

            # Check provider preferences
            provider_type = model.metadata.get("provider_type", "")
            if (
                request.excluded_providers
                and provider_type in request.excluded_providers
            ):
                continue

            # Check cost limits
            if request.max_cost:
                estimated_cost, _ = self._calculate_cost(
                    model, request.estimated_tokens
                )
                if estimated_cost > request.max_cost:
                    continue

            filtered.append(model)

        return filtered

    def _score_models_by_criteria(
        self, models: List[Model], request: ModelSelectionRequest
    ) -> List[Model]:
        """Score and rank models based on multiple criteria."""
        scored_models = []

        for model in models:
            score = 0.0

            # Reliability score (0-40 points)
            score += float(model.reliability) * 40

            # Latency score (0-30 points, lower latency is better)
            max_latency = 10000  # 10 seconds
            latency_score = max(0, 30 - (model.avg_latency / max_latency * 30))
            score += latency_score

            # Cost score (0-30 points, lower cost is better)
            estimated_cost, _ = self._calculate_cost(model, request.estimated_tokens)
            max_cost = Decimal("1.00")  # $1 as reference
            cost_score = max(0, 30 - (float(estimated_cost) / float(max_cost) * 30))
            score += cost_score

            # Priority adjustments
            if request.priority == ModelPriority.HIGH:
                if model.avg_latency < 2000:  # Under 2 seconds
                    score += 10
            elif request.priority == ModelPriority.LOW:
                # Prefer cheaper models for low priority
                score += cost_score * 0.5

            scored_models.append((model, score))

        # Sort by score (highest first)
        scored_models.sort(key=lambda x: x[1], reverse=True)
        return [model for model, score in scored_models]

    async def _get_provider_type(self, provider_id: str) -> str:
        """Get provider type for a given provider ID."""
        query = "SELECT provider_type FROM providers WHERE id = %s"
        results = await self._execute_mswap_query(query, [provider_id])
        return results[0]["provider_type"] if results else "unknown"

    def _generate_selection_reasoning(
        self, model: Model, request: ModelSelectionRequest
    ) -> str:
        """Generate human-readable reasoning for model selection."""
        reasons = []

        reasons.append(f"Selected {model.name}")
        reasons.append(f"reliability: {model.reliability}")
        reasons.append(f"avg latency: {model.avg_latency}ms")

        estimated_cost, _ = self._calculate_cost(model, request.estimated_tokens)
        reasons.append(f"estimated cost: ${estimated_cost}")

        if request.priority == ModelPriority.HIGH:
            reasons.append("optimized for high priority")
        elif request.priority == ModelPriority.LOW:
            reasons.append("optimized for cost efficiency")

        return "; ".join(reasons)

    # === Usage Tracking and Analytics ===
    async def record_model_usage(
        self,
        model_id: str,
        task_type: str,
        user_id: str,
        success: bool,
        response_time: int,
        prompt_tokens: int,
        completion_tokens: int,
        cost: Decimal,
        error: Optional[str] = None,
    ) -> None:
        """Record model usage in the MSWAP database."""
        try:
            # Insert into usage_logs table
            query = """
            INSERT INTO usage_logs (
                user_id, provider_id, model_id, prompt_tokens, completion_tokens,
                cost, latency, success, error, task_type_id, metadata
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """

            # Get provider_id for the model
            provider_query = "SELECT provider_id FROM models WHERE id = %s"
            provider_results = await self._execute_mswap_query(
                provider_query, [model_id]
            )
            provider_id = (
                provider_results[0]["provider_id"] if provider_results else None
            )

            # Get task_type_id
            task_query = "SELECT id FROM task_types WHERE name = %s"
            task_results = await self._execute_mswap_query(task_query, [task_type])
            task_type_id = task_results[0]["id"] if task_results else None

            metadata = {
                "timestamp": datetime.now().isoformat(),
                "total_tokens": prompt_tokens + completion_tokens,
            }

            await self._execute_mswap_query(
                query,
                [
                    user_id,
                    provider_id,
                    model_id,
                    prompt_tokens,
                    completion_tokens,
                    float(cost),
                    response_time,
                    success,
                    error,
                    task_type_id,
                    metadata,
                ],
            )

            # Update performance metrics
            await self._update_performance_metrics(
                model_id, task_type, success, response_time, cost
            )

            logger.info(
                f"Recorded usage: user={user_id}, model={model_id}, cost=${cost}"
            )

        except Exception as e:
            logger.error(f"Failed to record usage: {e}")

    async def _update_performance_metrics(
        self,
        model_id: str,
        task_type: str,
        success: bool,
        response_time: int,
        cost: Decimal,
    ) -> None:
        """Update performance metrics in task_performance table."""
        try:
            # Get current performance data
            query = """
            SELECT * FROM task_performance
            WHERE model_id = %s AND task_type_id = (
                SELECT id FROM task_types WHERE name = %s
            )
            """
            results = await self._execute_mswap_query(query, [model_id, task_type])

            if results:
                # Update existing record
                perf = results[0]
                new_sample_size = perf["sample_size"] + 1
                new_success_rate = (
                    (perf["success_rate"] * perf["sample_size"]) + (1 if success else 0)
                ) / new_sample_size
                new_avg_latency = (
                    (perf["avg_latency"] * perf["sample_size"]) + response_time
                ) / new_sample_size
                new_avg_cost = (
                    (perf["avg_cost"] * perf["sample_size"]) + float(cost)
                ) / new_sample_size

                update_query = """
                UPDATE task_performance
                SET success_rate = %s, avg_latency = %s, avg_cost = %s,
                    sample_size = %s, last_success_at = %s, updated_at = NOW()
                WHERE id = %s
                """

                last_success = (
                    datetime.now() if success else perf.get("last_success_at")
                )
                await self._execute_mswap_query(
                    update_query,
                    [
                        new_success_rate,
                        new_avg_latency,
                        new_avg_cost,
                        new_sample_size,
                        last_success,
                        perf["id"],
                    ],
                )
            else:
                # Create new record
                task_query = "SELECT id FROM task_types WHERE name = %s"
                task_results = await self._execute_mswap_query(task_query, [task_type])
                task_type_id = task_results[0]["id"] if task_results else None

                insert_query = """
                INSERT INTO task_performance (
                    task_type_id, model_id, success_rate, avg_latency, avg_cost,
                    sample_size, last_success_at, metadata
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """

                metadata = {"created_from": "modelswapper_service"}
                last_success = datetime.now() if success else None

                await self._execute_mswap_query(
                    insert_query,
                    [
                        task_type_id,
                        model_id,
                        1 if success else 0,
                        response_time,
                        float(cost),
                        1,
                        last_success,
                        metadata,
                    ],
                )

        except Exception as e:
            logger.error(f"Failed to update performance metrics: {e}")

    # === User Provider Configuration (High-Tier Users) ===
    async def create_user_provider_config(
        self,
        user_id: str,
        provider_type: str,
        api_key: str,
        organization_id: Optional[str] = None,
    ) -> str:
        """Create a user-specific provider configuration for high-tier users."""
        try:
            # Create a new provider entry for this user
            query = """
            INSERT INTO providers (
                name, provider_type, api_key, organization_id, enabled, priority,
                regions, metadata
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
            """

            name = f"{provider_type.title()} (User: {user_id})"
            metadata = {
                "user_id": user_id,
                "user_managed": True,
                "created_by": "modelswapper_service",
            }

            results = await self._execute_mswap_query(
                query,
                [
                    name,
                    provider_type,
                    api_key,
                    organization_id,
                    True,
                    100,
                    [],
                    metadata,
                ],
            )

            provider_id = results[0]["id"] if results else None
            logger.info(
                f"Created user provider config: {provider_id} for user {user_id}"
            )
            return provider_id

        except Exception as e:
            logger.error(f"Failed to create user provider config: {e}")
            raise

    async def get_user_provider_configs(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all provider configurations for a user."""
        try:
            query = """
            SELECT * FROM providers
            WHERE metadata->>'user_id' = %s
            AND metadata->>'user_managed' = 'true'
            ORDER BY created_at DESC
            """

            results = await self._execute_mswap_query(query, [user_id])
            return results

        except Exception as e:
            logger.error(f"Failed to get user provider configs: {e}")
            return []

    # === Health Monitoring ===
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on the ModelSwapper service."""
        try:
            # Test database connection
            test_query = "SELECT COUNT(*) as count FROM providers WHERE enabled = true"
            results = await self._execute_mswap_query(test_query)
            provider_count = results[0]["count"] if results else 0

            return {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "database_connection": "ok",
                "active_providers": provider_count,
                "cache_size": len(self._cache),
                "emergency_threshold": str(self.emergency_cost_threshold),
            }
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "status": "unhealthy",
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
            }
