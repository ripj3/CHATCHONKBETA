"""
ModelSwapper API Routes - User-Level AI Model Configuration

This module provides API endpoints for high-tier users to configure their own
AI provider API keys, manage model preferences, and monitor usage.

Key Features:
- User-specific API key management
- Model selection and routing preferences
- Usage tracking and analytics
- Rate limiting and cost monitoring

Author: Rip Jonesy
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel, ValidationError
from app.core.security import get_current_user
from app.core.rate_limiter import rate_limiter

from app.models.mswap_models import (
    UserProviderConfig,
    UserTier,
    CreateProviderConfigRequest,
    UpdateProviderConfigRequest,
    ModelSelectionRequest,
    ModelSelectionResponse,
    # Removed: ModelDefinition, ModelPerformance, TaskRoutingPreference, UserApiUsage
)
from app.services.modelswapper_service import ModelSwapperService
from app.automodel import TaskType

logger = logging.getLogger("chatchonk.api.modelswapper")

# Initialize router and dependencies
router = APIRouter(prefix="/modelswapper", tags=["ModelSwapper"])
modelswapper_service = ModelSwapperService()


async def require_tier(min_tier: UserTier):
    """Dependency to require minimum user tier."""

    def _check_tier(user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
        user_tier = UserTier(user.get("tier", UserTier.FREE))

        # Define tier hierarchy
        tier_levels = {
            UserTier.FREE: 0,
            UserTier.LILBEAN: 1,
            UserTier.CLAWBACK: 2,
            UserTier.BIGCHONK: 3,
            UserTier.MEOWTRIX: 4,
        }

        if tier_levels.get(user_tier, 0) < tier_levels.get(min_tier, 0):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"This feature requires {min_tier.value} tier or higher",
            )

        return user

    return _check_tier


async def apply_rate_limit(request: Request, user: Dict[str, Any] = Depends(get_current_user)):
    """Apply rate limiting based on user tier."""
    user_id = user["user_id"]
    user_tier = UserTier(user.get("tier", UserTier.FREE))
    
    # Define rate limits based on user tier
    tier_limits = {
        UserTier.FREE: {"limit": 50, "window": 60},  # 50 requests per minute
        UserTier.LILBEAN: {"limit": 100, "window": 60},  # 100 requests per minute
        UserTier.CLAWBACK: {"limit": 200, "window": 60},  # 200 requests per minute
        UserTier.BIGCHONK: {"limit": 500, "window": 60},  # 500 requests per minute
        UserTier.MEOWTRIX: {"limit": 1000, "window": 60},  # 1000 requests per minute
    }
    
    limits = tier_limits.get(user_tier, tier_limits[UserTier.FREE])
    
    # Apply rate limiting
    await rate_limiter(request, user_id, limits["limit"], limits["window"])
    return user


# === Response Models ===
class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    timestamp: str
    details: Dict[str, Any]


class UsageStatsResponse(BaseModel):
    """User usage statistics response."""

    user_id: str
    current_tier: UserTier
    usage_today: Dict[str, int]
    usage_this_month: Dict[str, int]
    cost_today: float
    cost_this_month: float
    rate_limits: Dict[str, Any]


# === Health & Status Endpoints ===
@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Get ModelSwapper service health status."""
    try:
        health_data = await modelswapper_service.health_check()
        return HealthResponse(
            status="healthy", timestamp=health_data["timestamp"], details=health_data
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="ModelSwapper service is unhealthy: " + str(e),
        )


# === Model Selection Endpoints ===
@router.post("/select-model", response_model=ModelSelectionResponse)
async def select_model(
    request: ModelSelectionRequest, 
    user: Dict[str, Any] = Depends(apply_rate_limit)
):
    """
    Select the best AI model for a given task.

    This endpoint uses intelligent routing to select the optimal model based on:
    - Task type and requirements
    - User tier and preferences
    - Model performance history
    - Cost considerations
    - Current availability
    """
    try:
        # Set user context in request
        request.user_id = user["user_id"]
        request.user_tier = UserTier(user.get("tier", UserTier.FREE))

        response = await modelswapper_service.select_best_model(request)

        logger.info(
            f"Selected model {response.selected_model_name} for user {user['user_id']}"
        )
        return response

    except ValueError as e:
        logger.warning(f"Invalid request parameters: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except ValidationError as e:
        logger.warning(f"Request validation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid request data: {str(e)}"
        )
    except ConnectionError as e:
        logger.error(f"Connection error during model selection: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service temporarily unavailable. Please try again later."
        )
    except Exception as e:
        logger.error(f"Model selection failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to select model: An unexpected error occurred"
        )


# === Provider Configuration Endpoints (High-Tier Users) ===
@router.get(
    "/provider-configs", response_model=List[UserProviderConfig]
)  # Changed to UserProviderConfig
async def get_provider_configs(
    request: Request,
    user: Dict[str, Any] = Depends(require_tier(UserTier.CLAWBACK)),
):
    """Get user's provider configurations (Clawback tier and above)."""
    try:
        # Apply rate limiting
        await rate_limiter(request, user["user_id"], 30, 60)  # 30 requests per minute
        
        configs = await modelswapper_service.get_user_provider_configs(user["user_id"])
        return configs
    except HTTPException:
        raise
    except ConnectionError as e:
        logger.error(f"Database connection error: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database service temporarily unavailable"
        )
    except Exception as e:
        logger.error(f"Failed to get provider configs: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve provider configurations: " + str(e)
        )


@router.post(
    "/provider-configs", response_model=UserProviderConfig
)  # Changed to UserProviderConfig
async def create_provider_config(
    request: Request,
    config_request: CreateProviderConfigRequest,
    user: Dict[str, Any] = Depends(require_tier(UserTier.CLAWBACK)),
):
    """Create a new provider configuration with user's API key."""
    try:
        # Apply rate limiting - stricter for creation operations
        await rate_limiter(request, user["user_id"], 10, 60)  # 10 requests per minute
        
        config = await modelswapper_service.create_user_provider_config(
            user["user_id"], config_request
        )

        logger.info(
            f"Created provider config for {config_request.provider_type} by user "
            f"{user['user_id']}"
        )
        return config

    except ValueError as e:
        logger.warning(f"Invalid provider config parameters: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except ValidationError as e:
        logger.warning(f"Provider config validation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid configuration data: {str(e)}"
        )
    except ConnectionError as e:
        logger.error(f"Database connection error: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database service temporarily unavailable"
        )
    except Exception as e:
        logger.error(
            f"Failed to create provider config: {e}", exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create provider configuration: " + str(e)
        )


@router.put(
    "/provider-configs/{config_id}", response_model=UserProviderConfig
)  # Changed to UserProviderConfig
async def update_provider_config(
    config_id: str,
    request: Request,
    update_request: UpdateProviderConfigRequest,
    user: Dict[str, Any] = Depends(require_tier(UserTier.CLAWBACK)),
):
    """Update an existing provider configuration."""
    try:
        # Apply rate limiting
        await rate_limiter(request, user["user_id"], 20, 60)  # 20 requests per minute
        
        config = await modelswapper_service.update_user_provider_config(
            user["user_id"], config_id, update_request
        )

        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Provider configuration with ID {config_id} not found"
            )

        logger.info(f"Updated provider config {config_id} by user {user['user_id']}")
        return config

    except ValueError as e:
        logger.warning(f"Invalid provider config update parameters: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except ValidationError as e:
        logger.warning(f"Provider config update validation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid update data: {str(e)}"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update provider config: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update provider configuration {config_id}: {str(e)}"
        )


@router.delete("/provider-configs/{config_id}")
async def delete_provider_config(
    config_id: str, 
    request: Request,
    user: Dict[str, Any] = Depends(require_tier(UserTier.CLAWBACK))
):
    """Delete a provider configuration."""
    try:
        # Apply rate limiting - stricter for deletion operations
        await rate_limiter(request, user["user_id"], 10, 60)  # 10 requests per minute
        
        # Check if the config exists and belongs to the user
        config = await modelswapper_service.get_user_provider_config(
            user["user_id"], config_id
        )
        
        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Provider configuration with ID {config_id} not found"
            )
            
        success = await modelswapper_service.delete_user_provider_config(
            user["user_id"], config_id
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete provider configuration"
            )

        logger.info(f"Deleted provider config {config_id} by user {user['user_id']}")
        return {"message": "Provider configuration deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete provider config: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete provider configuration {config_id}: {str(e)}"
        )


# === Usage & Analytics Endpoints ===
@router.get("/usage", response_model=UsageStatsResponse)
async def get_usage_stats(
    request: Request,
    user: Dict[str, Any] = Depends(apply_rate_limit)
):
    """Get user's API usage statistics and rate limits."""
    try:
        # TODO: Implement usage statistics retrieval
        # This would query UserApiUsage table and aggregate data

        # Mock response for now
        return UsageStatsResponse(
            user_id=user["user_id"],
            current_tier=UserTier(user.get("tier", UserTier.FREE)),
            usage_today={"requests": 45, "tokens": 12500},
            usage_this_month={"requests": 1250, "tokens": 450000},
            cost_today=2.35,
            cost_this_month=67.80,
            rate_limits={
                "requests_per_hour": 100,
                "tokens_per_day": 50000,
                "remaining_today": 37500,
            },
        )

    except ConnectionError as e:
        logger.error(f"Database connection error: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Usage statistics service temporarily unavailable"
        )
    except Exception as e:
        logger.error(f"Failed to get usage stats: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve usage statistics: {str(e)}"
        )


# === Model Performance Endpoints ===
@router.get("/models/performance")
async def get_model_performance(
    request: Request,
    task_type: Optional[TaskType] = None,
    user: Dict[str, Any] = Depends(apply_rate_limit),
):
    """Get model performance statistics for the user."""
    try:
        # TODO: Implement performance data retrieval
        # Query ModelPerformance table for user's models

        # Mock response
        return {
            "user_id": user["user_id"],
            "performance_data": [
                {
                    "model_name": "GPT-4o",
                    "task_type": "summarization",
                    "success_rate": 98.5,
                    "avg_response_time": 2.3,
                    "total_requests": 156,
                    "avg_quality_score": 4.7,
                },
                {
                    "model_name": "Claude 3.5 Sonnet",
                    "task_type": "topic_extraction",
                    "success_rate": 99.2,
                    "avg_response_time": 1.8,
                    "total_requests": 89,
                    "avg_quality_score": 4.8,
                },
            ],
        }

    except ValueError as e:
        if task_type is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid task type: {task_type}"
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to get model performance: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve model performance data: {str(e)}"
        )
