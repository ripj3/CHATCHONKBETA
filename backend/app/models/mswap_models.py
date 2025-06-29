"""
MSWAP Database Models - ModelSwapper Service Data Models

This module defines Pydantic models for the existing MSWAP database tables.
These models work with the actual database schema for AI provider configurations,
model management, performance tracking, and intelligent routing decisions.

Includes security controls and cost management features to prevent billing surprises.

Author: Rip Jonesy
"""

import uuid
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, SecretStr, HttpUrl, constr, validator


# === User Tier Enums ===
class UserTier(str, Enum):
    """User subscription tiers that determine AI model access and spending limits."""

    FREE = "free"
    LILBEAN = "lilbean"
    CLAWBACK = "clawback"
    BIGCHONK = "bigchonk"
    MEOWTRIX = "meowtrix"


class ModelPriority(str, Enum):
    """Model selection priority levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SecurityLevel(str, Enum):
    """Security levels for API access."""

    SYSTEM = "system"  # System-managed keys
    USER = "user"  # User-provided keys
    RESTRICTED = "restricted"  # Limited access

# === Supported Provider Types ===
# Keeping the list lean; extend as needed.
class SupportedProviderType(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    DEEPSEEK = "deepseek"
    QWEN = "qwen"
    MISTRAL = "mistral"


# === Database Models (matching existing MSWAP schema) ===
class Provider(BaseModel):
    """Provider configuration from the existing providers table."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = Field(..., description="Human-readable provider name")
    provider_type: str = Field(
        ..., description="Provider type (openai, anthropic, etc.)"
    )
    api_key: str = Field(..., description="API key for this provider")
    base_url: Optional[str] = Field(None, description="Custom API endpoint URL")
    organization_id: Optional[str] = Field(
        None, description="Organization ID for the provider"
    )
    enabled: bool = Field(default=True, description="Whether this provider is enabled")
    priority: int = Field(default=0, description="Priority for provider selection")
    regions: List[str] = Field(default_factory=list, description="Supported regions")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional provider metadata"
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Model(BaseModel):
    """Model definition from the existing models table."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    provider_id: str = Field(..., description="Reference to provider")
    name: str = Field(..., description="Model name/identifier")
    capabilities: List[str] = Field(..., description="Model capabilities")
    context_length: int = Field(..., description="Maximum context length")
    cost_per_1k_prompt_tokens: Decimal = Field(
        ..., description="Cost per 1K prompt tokens"
    )
    cost_per_1k_completion_tokens: Decimal = Field(
        ..., description="Cost per 1K completion tokens"
    )
    regions: List[str] = Field(default_factory=list, description="Supported regions")
    enabled: bool = Field(default=True, description="Whether this model is enabled")
    reliability: Decimal = Field(
        default=Decimal("0.99"), description="Model reliability score"
    )
    avg_latency: int = Field(default=0, description="Average latency in milliseconds")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional model metadata"
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class TaskType(BaseModel):
    """Task type definition from the existing task_types table."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = Field(..., description="Task type name")
    description: Optional[str] = Field(None, description="Task type description")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional task type metadata"
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class TaskPerformance(BaseModel):
    """Task performance tracking from the existing task_performance table."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    task_type_id: str = Field(..., description="Reference to task type")
    task_model_id: str = Field(
        ..., description="Reference to model"
    )  # Renamed from model_id
    success_rate: Decimal = Field(
        default=Decimal("0"), description="Success rate (0-1)"
    )
    avg_latency: int = Field(default=0, description="Average latency in milliseconds")
    avg_cost: Decimal = Field(
        default=Decimal("0"), description="Average cost per request"
    )
    sample_size: int = Field(default=0, description="Number of samples")
    last_success_at: Optional[datetime] = Field(
        None, description="Last successful execution"
    )
    last_failure_at: Optional[datetime] = Field(
        None, description="Last failed execution"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional performance metadata"
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class GlobalPerformance(BaseModel):
    """Global performance tracking from the existing global_performance table."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    task_type: str = Field(..., description="Task type name")
    provider_type: str = Field(..., description="Provider type")
    global_model_name: str = Field(
        ..., description="Model name"
    )  # Renamed from model_name
    success_rate: Decimal = Field(
        default=Decimal("0"), description="Success rate (0-1)"
    )
    avg_latency: int = Field(default=0, description="Average latency in milliseconds")
    avg_cost: Decimal = Field(
        default=Decimal("0"), description="Average cost per request"
    )
    sample_size: int = Field(default=0, description="Number of samples")
    installations: int = Field(
        default=1, description="Number of installations using this combination"
    )
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional global performance metadata"
    )


class UsageLog(BaseModel):
    """Usage log from the existing usage_logs table."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: Optional[str] = Field(
        None, description="User ID (nullable for anonymous usage)"
    )
    provider_id: str = Field(..., description="Reference to provider")
    usage_model_id: str = Field(
        ..., description="Reference to model"
    )  # Renamed from model_id
    prompt_tokens: int = Field(..., description="Number of prompt tokens used")
    completion_tokens: int = Field(..., description="Number of completion tokens used")
    cost: Decimal = Field(..., description="Cost of the request")
    latency: int = Field(..., description="Request latency in milliseconds")
    success: bool = Field(
        default=True, description="Whether the request was successful"
    )
    error: Optional[str] = Field(None, description="Error message if failed")
    task_type_id: Optional[str] = Field(None, description="Reference to task type")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional usage metadata"
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)


# === Security and Cost Control Models ===
class UserSpendingLimits(BaseModel):
    """User spending limits and controls."""

    user_id: str
    user_tier: UserTier

    # Daily limits
    daily_cost_limit: Decimal = Field(..., description="Maximum daily spending")
    daily_request_limit: int = Field(..., description="Maximum daily requests")
    daily_token_limit: int = Field(..., description="Maximum daily tokens")

    # Hourly limits (for burst protection)
    hourly_cost_limit: Decimal = Field(..., description="Maximum hourly spending")
    hourly_request_limit: int = Field(..., description="Maximum hourly requests")

    # Per-request limits
    max_cost_per_request: Decimal = Field(
        ..., description="Maximum cost per single request"
    )
    max_tokens_per_request: int = Field(..., description="Maximum tokens per request")

    # Current usage
    current_daily_cost: Decimal = Field(default=Decimal("0"))
    current_daily_requests: int = Field(default=0)
    current_daily_tokens: int = Field(default=0)
    current_hourly_cost: Decimal = Field(default=Decimal("0"))
    current_hourly_requests: int = Field(default=0)

    # Reset timestamps
    daily_reset_at: datetime
    hourly_reset_at: datetime

    @classmethod
    def get_tier_defaults(cls, tier: UserTier) -> Dict[str, Any]:
        """Get default spending limits for each tier."""
        limits = {
            UserTier.FREE: {
                "daily_cost_limit": Decimal("1.00"),
                "daily_request_limit": 50,
                "daily_token_limit": 10000,
                "hourly_cost_limit": Decimal("0.25"),
                "hourly_request_limit": 15,
                "max_cost_per_request": Decimal("0.10"),
                "max_tokens_per_request": 2000,
            },
            UserTier.LILBEAN: {
                "daily_cost_limit": Decimal("5.00"),
                "daily_request_limit": 200,
                "daily_token_limit": 50000,
                "hourly_cost_limit": Decimal("1.00"),
                "hourly_request_limit": 50,
                "max_cost_per_request": Decimal("0.50"),
                "max_tokens_per_request": 4000,
            },
            UserTier.CLAWBACK: {
                "daily_cost_limit": Decimal("25.00"),
                "daily_request_limit": 1000,
                "daily_token_limit": 250000,
                "hourly_cost_limit": Decimal("5.00"),
                "hourly_request_limit": 200,
                "max_cost_per_request": Decimal("2.00"),
                "max_tokens_per_request": 8000,
            },
            UserTier.BIGCHONK: {
                "daily_cost_limit": Decimal("100.00"),
                "daily_request_limit": 5000,
                "daily_token_limit": 1000000,
                "hourly_cost_limit": Decimal("20.00"),
                "hourly_request_limit": 500,
                "max_cost_per_request": Decimal("10.00"),
                "max_tokens_per_request": 16000,
            },
            UserTier.MEOWTRIX: {
                "daily_cost_limit": Decimal("500.00"),
                "daily_request_limit": 25000,
                "daily_token_limit": 5000000,
                "hourly_cost_limit": Decimal("100.00"),
                "hourly_request_limit": 2000,
                "max_cost_per_request": Decimal("50.00"),
                "max_tokens_per_request": 32000,
            },
        }
        return limits.get(tier, limits[UserTier.FREE])


class UserProviderConfig(BaseModel):
    """User-specific provider configuration with security controls."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = Field(..., description="User ID who owns this config")
    provider_id: str = Field(..., description="Reference to system provider")

    # User's API credentials (encrypted)
    api_key: SecretStr = Field(..., description="User's encrypted API key")
    organization_id: Optional[str] = Field(None, description="User's organization ID")

    # Security settings
    security_level: SecurityLevel = Field(default=SecurityLevel.USER)
    allowed_models: List[str] = Field(
        default_factory=list, description="Specific models user can access"
    )
    blocked_models: List[str] = Field(
        default_factory=list, description="Models user cannot access"
    )

    # Cost controls
    spending_limits: UserSpendingLimits

    # Status
    is_active: bool = Field(default=True)
    is_verified: bool = Field(
        default=False, description="Whether API key has been verified"
    )
    last_verified_at: Optional[datetime] = Field(None)

    # Metadata
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


# === Request/Response Models ===
class ModelSelectionRequest(BaseModel):
    """Request for intelligent model selection with security and cost controls."""

    task_type: str = Field(..., description="Task type name")
    user_id: str = Field(..., description="User ID for security and billing")
    user_tier: UserTier = Field(..., description="User subscription tier")

    # Content details
    estimated_tokens: int = Field(
        ..., description="Estimated token count for cost calculation"
    )
    priority: ModelPriority = Field(default=ModelPriority.MEDIUM)

    # Cost controls
    max_cost: Optional[Decimal] = Field(
        None, description="Maximum acceptable cost override"
    )

    # Model preferences
    preferred_providers: List[str] = Field(
        default_factory=list, description="Preferred provider types"
    )
    excluded_providers: List[str] = Field(
        default_factory=list, description="Excluded provider types"
    )

    # Requirements
    min_context_length: Optional[int] = Field(
        None, description="Minimum context length required"
    )
    required_capabilities: List[str] = Field(
        default_factory=list, description="Required model capabilities"
    )

    # Security context
    use_user_keys: bool = Field(
        default=False, description="Use user's own API keys if available"
    )


class ModelSelectionResponse(BaseModel):
    """Response with selected model and security/cost information."""

    # Selected model
    selected_model_id: str = Field(
        ..., description="Selected model ID"
    )  # Renamed from model_id
    provider_id: str = Field(..., description="Provider ID")
    selected_model_name: str = Field(
        ..., description="Human-readable model name"
    )  # Renamed from model_name
    provider_type: str = Field(..., description="Provider type")

    # Cost information
    estimated_cost: Decimal = Field(..., description="Estimated cost for the request")
    cost_breakdown: Dict[str, Decimal] = Field(
        ..., description="Detailed cost breakdown"
    )

    # Security information
    using_user_keys: bool = Field(..., description="Whether using user's API keys")
    security_level: SecurityLevel = Field(..., description="Security level being used")

    # Selection reasoning
    reasoning: str = Field(..., description="Why this model was selected")
    fallback_models: List[str] = Field(
        default_factory=list, description="Alternative models if primary fails"
    )

    # Usage tracking
    request_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique request ID for tracking",
    )

    # Warnings
    cost_warning: Optional[str] = Field(None, description="Cost-related warnings")
    security_warning: Optional[str] = Field(
        None, description="Security-related warnings"
    )


class CreateProviderRequest(BaseModel):
    """Request to create a new provider configuration."""

    name: str = Field(..., description="Human-readable provider name")
    provider_type: str = Field(..., description="Provider type")
    api_key: SecretStr = Field(..., description="API key for the provider")
    base_url: Optional[str] = Field(None, description="Custom API endpoint URL")
    organization_id: Optional[str] = Field(None, description="Organization ID")
    regions: List[str] = Field(default_factory=list, description="Supported regions")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )


class UpdateProviderRequest(BaseModel):
    """Request to update an existing provider configuration."""

    name: Optional[str] = Field(None, description="Human-readable provider name")
    api_key: Optional[SecretStr] = Field(None, description="API key for the provider")
    base_url: Optional[str] = Field(None, description="Custom API endpoint URL")
    organization_id: Optional[str] = Field(None, description="Organization ID")
    enabled: Optional[bool] = Field(None, description="Whether the provider is enabled")
    priority: Optional[int] = Field(None, description="Provider priority")
    regions: Optional[List[str]] = Field(None, description="Supported regions")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class UsageStatsResponse(BaseModel):
    """User usage statistics response."""

    user_id: str = Field(..., description="User ID")
    current_tier: UserTier = Field(..., description="Current subscription tier")
    total_requests: int = Field(..., description="Total requests made")
    total_tokens: int = Field(..., description="Total tokens used")
    total_cost: Decimal = Field(..., description="Total cost incurred")
    requests_today: int = Field(..., description="Requests made today")
    tokens_today: int = Field(..., description="Tokens used today")
    cost_today: Decimal = Field(..., description="Cost incurred today")
    top_models: List[Dict[str, Any]] = Field(
        default_factory=list, description="Most used models"
    )
    performance_summary: Dict[str, Any] = Field(
        default_factory=dict, description="Performance summary"
    )


# -----------------------------------------------------------
# New – Validated Provider-Config request payloads (used by API)
# -----------------------------------------------------------
_NameStr = constr(min_length=3, max_length=50)
# 20+ url-safe chars (basic sanity check – adjust if stricter format desired)
_ApiKeyStr = constr(regex=r"^[A-Za-z0-9_\-]{20,}$")


class CreateProviderConfigRequest(BaseModel):
    """Validated payload for creating a user provider configuration."""

    name: _NameStr = Field(..., description="Human-readable provider name")
    provider_type: SupportedProviderType = Field(..., description="Provider type")
    api_key: SecretStr = Field(..., description="API key for the provider")
    base_url: Optional[HttpUrl] = Field(
        None, description="Custom API endpoint URL"
    )
    organization_id: Optional[str] = Field(None, description="Organization ID")
    regions: List[str] = Field(default_factory=list, description="Supported regions")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )

    # Extra defensive validation for api_key pattern
    @validator("api_key")
    def _validate_api_key(cls, v: SecretStr) -> SecretStr:  # noqa: N805
        if not _ApiKeyStr.regex.match(v.get_secret_value()):
            raise ValueError("api_key appears to be in an invalid format")
        return v


class UpdateProviderConfigRequest(BaseModel):
    """Validated payload for updating an existing provider configuration."""

    name: Optional[_NameStr] = Field(
        None, description="Human-readable provider name"
    )
    api_key: Optional[SecretStr] = Field(None, description="API key for the provider")
    base_url: Optional[HttpUrl] = Field(
        None, description="Custom API endpoint URL"
    )
    organization_id: Optional[str] = Field(None, description="Organization ID")
    enabled: Optional[bool] = Field(None, description="Whether the provider is enabled")
    priority: Optional[int] = Field(None, description="Provider priority")
    regions: Optional[List[str]] = Field(None, description="Supported regions")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")

    @validator("api_key")
    def _validate_api_key_optional(cls, v: Optional[SecretStr]) -> Optional[SecretStr]:  # noqa: N805
        if v is None:
            return v
        if not _ApiKeyStr.regex.match(v.get_secret_value()):
            raise ValueError("api_key appears to be in an invalid format")
        return v
