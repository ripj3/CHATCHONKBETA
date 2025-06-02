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

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

from app.models.mswap_models import (
    ProviderConfig, ModelDefinition, ModelPerformance, TaskRoutingPreference,
    UserApiUsage, UserTier, CreateProviderConfigRequest, UpdateProviderConfigRequest,
    ModelSelectionRequest, ModelSelectionResponse
)
from app.services.modelswapper_service import ModelSwapperService
from app.automodel import TaskType, ProviderType

logger = logging.getLogger("chatchonk.api.modelswapper")

# Initialize router and dependencies
router = APIRouter(prefix="/modelswapper", tags=["ModelSwapper"])
security = HTTPBearer()
modelswapper_service = ModelSwapperService()


# === Authentication & Authorization ===
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """
    Extract user information from JWT token.
    
    TODO: Implement proper JWT validation with Supabase
    For now, returns mock user data.
    """
    # TODO: Validate JWT token with Supabase
    # TODO: Extract user_id, tier, and other claims
    
    # Mock user data for development
    return {
        "user_id": "mock-user-123",
        "email": "user@example.com",
        "tier": UserTier.BIGCHONK,
        "is_active": True
    }


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
            UserTier.MEOWTRIX: 4
        }
        
        if tier_levels.get(user_tier, 0) < tier_levels.get(min_tier, 0):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"This feature requires {min_tier.value} tier or higher"
            )
        
        return user
    
    return _check_tier


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
            status="healthy",
            timestamp=health_data["timestamp"],
            details=health_data
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="ModelSwapper service is unhealthy"
        )


# === Model Selection Endpoints ===
@router.post("/select-model", response_model=ModelSelectionResponse)
async def select_model(
    request: ModelSelectionRequest,
    user: Dict[str, Any] = Depends(get_current_user)
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
        
        logger.info(f"Selected model {response.model_name} for user {user['user_id']}")
        return response
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Model selection failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to select model"
        )


# === Provider Configuration Endpoints (High-Tier Users) ===
@router.get("/provider-configs", response_model=List[ProviderConfig])
async def get_provider_configs(
    user: Dict[str, Any] = Depends(require_tier(UserTier.CLAWBACK))
):
    """Get user's provider configurations (Clawback tier and above)."""
    try:
        configs = await modelswapper_service.get_user_provider_configs(user["user_id"])
        return configs
    except Exception as e:
        logger.error(f"Failed to get provider configs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve provider configurations"
        )


@router.post("/provider-configs", response_model=ProviderConfig)
async def create_provider_config(
    request: CreateProviderConfigRequest,
    user: Dict[str, Any] = Depends(require_tier(UserTier.CLAWBACK))
):
    """Create a new provider configuration with user's API key."""
    try:
        config = await modelswapper_service.create_user_provider_config(
            user["user_id"], request
        )
        
        logger.info(f"Created provider config for {request.provider_type} by user {user['user_id']}")
        return config
        
    except Exception as e:
        logger.error(f"Failed to create provider config: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create provider configuration"
        )


@router.put("/provider-configs/{config_id}", response_model=ProviderConfig)
async def update_provider_config(
    config_id: str,
    request: UpdateProviderConfigRequest,
    user: Dict[str, Any] = Depends(require_tier(UserTier.CLAWBACK))
):
    """Update an existing provider configuration."""
    try:
        config = await modelswapper_service.update_user_provider_config(
            user["user_id"], config_id, request
        )
        
        logger.info(f"Updated provider config {config_id} by user {user['user_id']}")
        return config
        
    except Exception as e:
        logger.error(f"Failed to update provider config: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update provider configuration"
        )


@router.delete("/provider-configs/{config_id}")
async def delete_provider_config(
    config_id: str,
    user: Dict[str, Any] = Depends(require_tier(UserTier.CLAWBACK))
):
    """Delete a provider configuration."""
    try:
        success = await modelswapper_service.delete_user_provider_config(
            user["user_id"], config_id
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Provider configuration not found"
            )
        
        logger.info(f"Deleted provider config {config_id} by user {user['user_id']}")
        return {"message": "Provider configuration deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete provider config: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete provider configuration"
        )


# === Usage & Analytics Endpoints ===
@router.get("/usage", response_model=UsageStatsResponse)
async def get_usage_stats(
    user: Dict[str, Any] = Depends(get_current_user)
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
                "remaining_today": 37500
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to get usage stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve usage statistics"
        )


# === Model Performance Endpoints ===
@router.get("/models/performance")
async def get_model_performance(
    task_type: Optional[TaskType] = None,
    user: Dict[str, Any] = Depends(get_current_user)
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
                    "avg_quality_score": 4.7
                },
                {
                    "model_name": "Claude 3.5 Sonnet",
                    "task_type": "topic_extraction",
                    "success_rate": 99.2,
                    "avg_response_time": 1.8,
                    "total_requests": 89,
                    "avg_quality_score": 4.8
                }
            ]
        }
        
    except Exception as e:
        logger.error(f"Failed to get model performance: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve model performance data"
        )
