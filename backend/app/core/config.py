"""
ChatChonk Configuration Module - adjusted for pipeline error

This module defines all configuration settings for the ChatChonk application.
It uses Pydantic's BaseSettings for automatic environment variable loading and validation.

Environment variables are loaded from .env file if present.

Author: Rip Jonesy
"""

import logging
import secrets
from enum import Enum
from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic import (
    AnyHttpUrl,
    EmailStr,
    Field,
    SecretStr,
)

try:
    from pydantic_settings import BaseSettings
except ImportError:
    raise ImportError(
        "pydantic-settings is not installed. Please run: pip install pydantic-settings"
    )


class LogLevel(str, Enum):
    """Log levels for application logging."""

    CRITICAL = "CRITICAL"
    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"
    DEBUG = "DEBUG"


class Environment(str, Enum):
    """Application environment types."""

    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    PRODUCTION_BETA = "production_beta"
    TEST = "test"

    @classmethod
    def _missing_(cls, value: object):
        if isinstance(value, str):
            # Handle 'production-beta' as 'production_beta'
            if value == "production-beta":
                return cls.PRODUCTION_BETA
        return super()._missing_(value)


class AiProvider(str, Enum):
    """Supported AI model providers."""

    HUGGINGFACE = "huggingface"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    MISTRAL = "mistral"
    DEEPSEEK = "deepseek"
    QWEN = "qwen"
    CUSTOM = "custom"  # For potential self-hosted or other models


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    This class defines all configuration parameters for ChatChonk.
    """

    # ======================================================================
    # APPLICATION CORE SETTINGS
    # ======================================================================
    PROJECT_NAME: str = Field(
        default="ChatChonk", description="The name of the project."
    )
    APP_NAME: str = Field(
        default="ChatChonk",
        description="The name of the application (can be same as PROJECT_NAME).",
    )
    APP_VERSION: str = Field(default="0.1.0", description="Application version.")
    ENVIRONMENT: Environment = Field(
        default=Environment.DEVELOPMENT,
        description="Application environment (development, staging, production).",
    )
    DEBUG: bool = Field(
        default=False,
        description="Enable debug mode. Overrides LOG_LEVEL to DEBUG if True.",
    )

    # ======================================================================
    # SERVER SETTINGS (FastAPI Backend)
    # ======================================================================
    API_V1_STR: str = Field(default="/api", description="API version prefix.")
    HOST: str = Field(default="0.0.0.0", description="Server host to bind to.")
    PORT: int = Field(
        default=8000, description="Server port to listen on."
    )  # Match Dockerfile default
    ROOT_PATH: str = Field(
        default="",
        description="API root path prefix if running behind a reverse proxy with path stripping.",
    )
    RELOAD: bool = Field(
        default=False,
        description="Enable hot reloading for Uvicorn (development only).",
    )
    API_HOST: str = Field(
        default="127.0.0.1",
        description="Host for constructing API URLs, typically localhost for dev.",
    )
    API_URL: AnyHttpUrl = Field(
        default="http://127.0.0.1:8080/api",
        description="Full base URL for the API in development.",
    )
    PRODUCTION_API_URL: Optional[AnyHttpUrl] = Field(
        default=None,
        description="Full base URL for the API in production (e.g., https://api.chatchonk.com).",
    )

    # ======================================================================
    # DOMAIN & FRONTEND CONFIGURATION
    # ======================================================================
    DOMAIN: str = Field(
        default="chatchonk.com", description="Main domain for the application."
    )
    FRONTEND_URL: AnyHttpUrl = Field(
        default="https://chatchonk.com",
        description="Base URL for the frontend application.",
    )
    API_DOMAIN: Optional[str] = Field(
        default="api.chatchonk.com", description="Subdomain for the API in production."
    )

    # ======================================================================
    # SECURITY SETTINGS
    # ======================================================================
    SECRET_KEY: SecretStr = Field(
        default_factory=lambda: SecretStr(secrets.token_urlsafe(32)),
        alias="CHONK_SECRET_KEY",  # Alias to match .env.example
        description="Secret key for signing tokens, cookies, etc. CRITICAL for production.",
    )
    ALLOWED_ORIGINS: str = Field(
        default="",
        description="Comma-separated list of allowed CORS origins.",
    )
    ALLOWED_HOSTS: str = Field(
        default="",
        description="Comma-separated list of allowed host headers.",
    )
    API_KEY: Optional[SecretStr] = Field(
        default=None,
        description="Generic API key for securing internal or specific endpoints (development only or specific use cases).",
    )
    REQUIRE_API_KEY: bool = Field(
        default=False, description="Whether a general API key is required for access."
    )
    API_KEY_EXPIRY_DAYS: int = Field(
        default=90, description="Default expiry for generated API keys."
    )
    MAX_API_KEYS_PER_USER: int = Field(
        default=5, description="Maximum API keys a user can generate."
    )

    # ======================================================================
    # SUPABASE CONFIGURATION (CHCH3 - Main Database)
    # ======================================================================
    SUPABASE_URL: Optional[AnyHttpUrl] = Field(
        default=None, description="Supabase project URL."
    )
    SUPABASE_KEY: Optional[SecretStr] = Field(
        default=None,
        alias="SUPABASE_ANON_KEY",
        description="Supabase anonymous key (public).",
    )  # Alias for common naming
    SUPABASE_SERVICE_ROLE_KEY: Optional[SecretStr] = Field(
        default=None,
        description="Supabase service role key (secret, for backend admin operations).",
    )
    SUPABASE_PERSONAL_ACCESS_TOKEN: Optional[SecretStr] = Field(
        default=None,
        description="Supabase Personal Access Token for management API calls.",
    )

    # Optional direct DB passwords if self-hosting or specific needs
    SUPABASE_DB_PASSWORD: Optional[SecretStr] = Field(
        default=None,
        description="Password for the main Supabase PostgreSQL database user.",
    )

    # ======================================================================
    # MSWAP SUPABASE CONFIGURATION (ModelSwapper Database)
    # ======================================================================
    MSWAP_SUPABASE_URL: Optional[AnyHttpUrl] = Field(
        default=None, description="MSWAP Supabase project URL."
    )
    MSWAP_SUPABASE_KEY: Optional[SecretStr] = Field(
        default=None,
        alias="MSWAP_SUPABASE_ANON_KEY",
        description="MSWAP Supabase anonymous key (public).",
    )
    MSWAP_SUPABASE_SERVICE_ROLE_KEY: Optional[SecretStr] = Field(
        default=None,
        description="MSWAP Supabase service role key (secret, for backend admin operations).",
    )
    SUPABASE_DB_PASSWORD_MSWAP: Optional[SecretStr] = Field(
        default=None,
        description="Specific DB password for ModelSwapper service if it uses a different user/role.",
    )

    # ======================================================================
    # SUPABASE STORAGE / S3 COMPATIBLE CONFIGURATION
    # ======================================================================
    SUPABASE_STORAGE_URL: Optional[AnyHttpUrl] = Field(
        default=None,
        description="Base URL for Supabase Storage (e.g., SUPABASE_URL/storage/v1).",
    )
    SUPABASE_S3_ACCESS_KEY_ID: Optional[SecretStr] = Field(
        default=None, description="S3 compatible access key for Supabase Storage."
    )
    SUPABASE_S3_SECRET_ACCESS_KEY: Optional[SecretStr] = Field(
        default=None, description="S3 compatible secret key for Supabase Storage."
    )
    SUPABASE_S3_BUCKET: str = Field(
        default="files", description="Default S3 bucket name for Supabase Storage."
    )
    SUPABASE_STORAGE_BUCKET: str = Field(
        default="files",
        description="Default bucket name for Supabase Storage (can be same as S3_BUCKET).",
    )

    # ======================================================================
    # FILE PROCESSING & LOCAL STORAGE SETTINGS
    # ======================================================================
    UPLOAD_DIR: Optional[Path] = Field(
        default=None,
        description="Directory for initial file uploads (will be None if using cloud storage).",
    )
    TEMP_DIR: Optional[Path] = Field(
        default=None, description="Directory for temporary files during processing."
    )
    EXPORT_DIR: Optional[Path] = Field(
        default=None,
        description="Directory for storing generated export files locally (will be None if directly streamed or sent to cloud).",
    )
    STORAGE_PATH: Optional[Path] = Field(
        default=None,
        description="General local storage path (will be None if using cloud exclusively).",
    )
    EPHEMERAL_STORAGE_PATH: Optional[Path] = Field(
        default=None,
        description="Path for temporary storage of files that need quick cleanup.",
    )
    EPHEMERAL_MAX_AGE_SECONDS: int = Field(
        default=7200, description="Max age for files in ephemeral storage (2 hours)."
    )
    EPHEMERAL_CLEANUP_INTERVAL: int = Field(
        default=600,
        description="Interval for cleaning up ephemeral storage (10 minutes).",
    )
    EPHEMERAL_ENCRYPTION_ENABLED: bool = Field(
        default=True, description="Enable encryption for files in ephemeral storage."
    )

    MAX_UPLOAD_SIZE: int = Field(
        default=2_147_483_648, description="Maximum upload size in bytes (2GB)."
    )  # 2GB
    CHUNK_SIZE: int = Field(
        default=1_048_576,
        description="Chunk size for streaming file uploads in bytes (1MB).",
    )
    CLEANUP_INTERVAL: int = Field(
        default=3600,
        description="General interval for temporary file cleanup tasks (1 hour).",
    )
    FILE_RETENTION_PERIOD: int = Field(
        default=86400,
        description="Time to keep processed files locally before potential deletion (24 hours).",
    )
    ALLOWED_FILE_TYPES: str = Field(
        default="zip,json,txt,md,csv",  # Comma-separated string for environment variable parsing
        description="Comma-separated list of allowed file extensions for direct uploads (archives might contain more types internally).",
    )

    # ======================================================================
    # AI PROVIDER SETTINGS (AutoModel)
    # ======================================================================
    DEFAULT_AI_PROVIDER: AiProvider = Field(
        default=AiProvider.HUGGINGFACE,
        description="Default AI provider for processing if not specified.",
    )

    HUGGINGFACE_API_KEY: Optional[SecretStr] = Field(
        default=None, description="API key for Hugging Face Hub and Inference API."
    )
    HUGGINGFACE_DEFAULT_MODEL: str = Field(
        default="mistralai/Mistral-7B-Instruct-v0.2",
        description="Default Hugging Face model for general tasks.",
    )
    HUGGINGFACE_SPACE: Optional[str] = Field(
        default=None,
        description="Identifier for a specific Hugging Face Space if used.",
    )
    HUGGINGFACE_STREAMLIT_URL: Optional[AnyHttpUrl] = Field(
        default=None, description="URL for a Hugging Face Streamlit app if integrated."
    )

    OPENAI_API_KEY: Optional[SecretStr] = Field(
        default=None, description="API key for OpenAI."
    )
    OPENAI_DEFAULT_MODEL: str = Field(
        default="gpt-4o", description="Default OpenAI model."
    )

    ANTHROPIC_API_KEY: Optional[SecretStr] = Field(
        default=None, description="API key for Anthropic (Claude)."
    )
    ANTHROPIC_DEFAULT_MODEL: str = Field(
        default="claude-3-opus-20240229", description="Default Anthropic model."
    )

    MISTRAL_API_KEY: Optional[SecretStr] = Field(
        default=None, description="API key for Mistral AI."
    )
    MISTRAL_DEFAULT_MODEL: str = Field(
        default="mistral-large-latest", description="Default Mistral model."
    )

    DEEPSEEK_API_KEY: Optional[SecretStr] = Field(
        default=None, description="API key for DeepSeek."
    )
    DEEPSEEK_DEFAULT_MODEL: str = Field(
        default="deepseek-coder", description="Default DeepSeek model."
    )

    QWEN_API_KEY: Optional[SecretStr] = Field(
        default=None, description="API key for Qwen (Alibaba)."
    )
    QWEN_DEFAULT_MODEL: str = Field(
        default="qwen-max", description="Default Qwen model."
    )

    # ======================================================================
    # TEMPLATE SETTINGS
    # ======================================================================
    TEMPLATES_DIR: Path = Field(
        default=Path("./templates"),
        description="Directory where ChatChonk processing templates (YAML files) are stored.",
    )
    DEFAULT_TEMPLATE: str = Field(
        default="adhd-idea-harvest",
        description="Default template ID to use if none is specified by the user.",
    )

    # ======================================================================
    # LOGGING CONFIGURATION
    # ======================================================================
    LOG_LEVEL: LogLevel = Field(
        default=LogLevel.INFO, description="Logging level for the application."
    )
    LOG_FILE: Optional[Path] = Field(
        default=None,
        description="Path to the log file. Set to None for stdout, or a path for file logging.",
    )
    LOG_FORMAT: str = Field(
        default="%(levelname)s:	%(asctime)s %(name)s - %(message)s",
        description="Log output format string.",
    )

    # ======================================================================
    # EMAIL SETTINGS (Optional, for future use like notifications, MFA)
    # ======================================================================
    SMTP_HOST: Optional[str] = Field(
        default=None, description="SMTP server host for sending emails."
    )
    SMTP_PORT: Optional[int] = Field(default=587, description="SMTP server port.")
    SMTP_USER: Optional[str] = Field(default=None, description="SMTP username.")
    SMTP_PASSWORD: Optional[SecretStr] = Field(
        default=None, description="SMTP password."
    )
    EMAILS_FROM_EMAIL: Optional[EmailStr] = Field(
        default=None, description="Default sender email address for application emails."
    )
    EMAILS_FROM_NAME: Optional[str] = Field(
        default=None, description="Default sender name for application emails."
    )

    # ======================================================================
    # GITHUB CONFIGURATION (Optional, if app interacts with GitHub)
    # ======================================================================
    GITHUB_PERSONAL_ACCESS_TOKEN: Optional[SecretStr] = Field(
        default=None, description="GitHub Personal Access Token for API interactions."
    )

    # ======================================================================
    # STRIPE BILLING CONFIGURATION (Optional, for paid tiers)
    # ======================================================================
    STRIPE_PUBLISHABLE_KEY: Optional[SecretStr] = Field(
        default=None, description="Stripe publishable API key (pk_...)."
    )
    STRIPE_SECRET_KEY: Optional[SecretStr] = Field(
        default=None,
        alias="STRIPE_RESTRICTED_KEY",
        description="Stripe secret API key (sk_live_... or rk_live_...).",
    )  # Renamed for clarity
    STRIPE_SECRET_TEST_KEY: Optional[SecretStr] = Field(
        default=None,
        alias="STRIPE_RESTRICTED_TEST_KEY",
        description="Stripe secret test API key (sk_test_... or rk_test_...).",
    )
    STRIPE_WEBHOOK_SECRET: Optional[SecretStr] = Field(
        default=None, description="Stripe webhook signing secret (whsec_...)."
    )

    STRIPE_PRICE_LILBEAN: Optional[str] = Field(
        default=None, description="Stripe Price ID for 'LilBean' tier."
    )
    STRIPE_PRICE_CLAWBACK: Optional[str] = Field(
        default=None, description="Stripe Price ID for 'Clawback' tier."
    )
    STRIPE_PRICE_BIGCHONK: Optional[str] = Field(
        default=None, description="Stripe Price ID for 'BigChonk' tier."
    )
    STRIPE_PRICE_MEOWTRIX: Optional[str] = Field(
        default=None, description="Stripe Price ID for 'Meowtrix' tier."
    )
    STRIPE_PRICE_CLAWBACK_YEARLY: Optional[str] = Field(
        default=None, description="Stripe Price ID for 'Clawback Yearly' tier."
    )
    STRIPE_PRICE_BIGCHONK_YEARLY: Optional[str] = Field(
        default=None, description="Stripe Price ID for 'BigChonk Yearly' tier."
    )
    STRIPE_PRICE_MEOWTRIX_YEARLY: Optional[str] = Field(
        default=None, description="Stripe Price ID for 'Meowtrix Yearly' tier."
    )
    USE_STRIPE_PLANS: bool = Field(
        default=True,
        description="Flag to enable/disable Stripe plan integration logic.",
    )
    STRIPE_PROMO_CODE: Optional[str] = Field(
        default=None, description="Default monthly promo code for Stripe."
    )
    STRIPE_PROMO_CODE_YEARLY: Optional[str] = Field(
        default=None, description="Default yearly promo code for Stripe."
    )

    # ======================================================================
    # DISCORD INTEGRATION CONFIGURATION
    # ======================================================================
    DISCORD_BOT_TOKEN: Optional[SecretStr] = Field(
        default=None, description="Discord bot token for ChatChonk support bot."
    )
    DISCORD_GUILD_ID: Optional[int] = Field(
        default=None, description="Discord server (guild) ID for ChatChonk support."
    )

    # Channel IDs
    DISCORD_GENERAL_CHANNEL_ID: Optional[int] = Field(
        default=None, description="General chat channel ID."
    )
    DISCORD_SUPPORT_CHANNEL_ID: Optional[int] = Field(
        default=None, description="Support channel ID."
    )
    DISCORD_ANNOUNCEMENTS_CHANNEL_ID: Optional[int] = Field(
        default=None, description="Announcements channel ID."
    )
    DISCORD_FEEDBACK_CHANNEL_ID: Optional[int] = Field(
        default=None, description="Feedback channel ID."
    )

    # User tier role IDs
    DISCORD_FREE_ROLE_ID: Optional[int] = Field(
        default=None, description="Free tier role ID."
    )
    DISCORD_LILBEAN_ROLE_ID: Optional[int] = Field(
        default=None, description="LilBean tier role ID."
    )
    DISCORD_CLAWBACK_ROLE_ID: Optional[int] = Field(
        default=None, description="Clawback tier role ID."
    )
    DISCORD_BIGCHONK_ROLE_ID: Optional[int] = Field(
        default=None, description="BigChonk tier role ID."
    )
    DISCORD_MEOWTRIX_ROLE_ID: Optional[int] = Field(
        default=None, description="Meowtrix tier role ID."
    )

    # Staff role IDs
    DISCORD_ADMIN_ROLE_ID: Optional[int] = Field(
        default=None, description="Admin role ID."
    )
    DISCORD_MODERATOR_ROLE_ID: Optional[int] = Field(
        default=None, description="Moderator role ID."
    )
    DISCORD_SUPPORT_ROLE_ID: Optional[int] = Field(
        default=None, description="Support role ID."
    )

    # ======================================================================
    # CLOUDFLARE KV CACHING (RECOMMENDED – Free 1GB tier)
    # ======================================================================
    CLOUDFLARE_API_TOKEN: Optional[SecretStr] = Field(
        default=None, description="Cloudflare API Token for KV access."
    )
    CLOUDFLARE_ACCOUNT_ID: Optional[str] = Field(
        default=None, description="Cloudflare Account ID."
    )
    CLOUDFLARE_KV_NAMESPACE_ID: Optional[str] = Field(
        default=None, description="Cloudflare KV Namespace ID for caching."
    )

    # ======================================================================
    # REDIS CACHING (OPTIONAL – Deprecated in favor of Cloudflare KV)
    # ======================================================================
    REDIS_HOST: str = Field(default="localhost", description="Redis host.")
    REDIS_PORT: int = Field(default=6379, description="Redis port.")
    REDIS_PASSWORD: Optional[SecretStr] = Field(
        default=None, description="Redis password."
    )
    REDIS_ENABLED: bool = Field(
        default=False, description="Enable or disable Redis caching."
    )

    # ======================================================================
    # MONITORING & OBSERVABILITY
    # ======================================================================
    SENTRY_DSN: Optional[SecretStr] = Field(
        default=None, description="Sentry DSN for error tracking."
    )
    ENABLE_AUDIT_LOGGING: bool = Field(
        default=True, description="Enable detailed audit logging."
    )
    LOG_ROTATION_DAYS: int = Field(
        default=90, description="Number of days to retain log files before rotation."
    )

    # ======================================================================
    # SECURITY & VALIDATION SETTINGS (Backend)
    # ======================================================================
    ENABLE_INPUT_VALIDATION: bool = Field(
        default=True, description="Enable validation for API request payloads."
    )
    ENABLE_CONTENT_VALIDATION: bool = Field(
        default=True, description="Enable content validation (e.g., PII checks) for uploaded files."
    )
    ENABLE_REQUEST_SIGNING: bool = Field(
        default=True, description="Enable request signing for inter-service communication."
    )
    REQUEST_SIGNATURE_EXPIRY_SECONDS: int = Field(
        default=300, description="Expiry time for request signatures in seconds."
    )
    ENABLE_IP_FILTERING: bool = Field(
        default=False, description="Enable IP filtering for API access."
    )
    ALLOWED_IPS: str = Field(
        default="", description="Comma-separated list of allowed IP addresses or CIDR blocks if IP filtering is enabled."
    )

    @property
    def allowed_origins_list(self) -> list[str]:
        return [item.strip() for item in self.ALLOWED_ORIGINS.split(",") if item.strip()]

    @property
    def allowed_hosts_list(self) -> list[str]:
        return [item.strip() for item in self.ALLOWED_HOSTS.split(",") if item.strip()]

    @property
    def allowed_ips_list(self) -> list[str]:
        return [item.strip() for item in self.ALLOWED_IPS.split(",") if item.strip()]

    # ======================================================================
    # RATE LIMITING CONFIGURATION (Backend)
    # ======================================================================
    RATE_LIMIT_ENABLED: bool = Field(
        default=False, description="Enable global API rate limiting."
    )
    RATE_LIMIT_REQUESTS: int = Field(
        default=100, description="Default number of requests allowed within the rate limit window."
    )
    RATE_LIMIT_WINDOW_MINUTES: int = Field(
        default=60, description="Default rate limit window in minutes."
    )
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = Field(
        default=1000, description="Requests per minute for general rate limiting."
    )

    # ======================================================================
    # PROMPT & OUTPUT SAFETY FILTERS (Backend - AutoModel)
    # ======================================================================
    ENABLE_PROMPT_FILTERING: bool = Field(
        default=True, description="Enable safety filtering for user prompts."
    )
    PROMPT_FILTER_LEVEL: str = Field(
        default="medium", description="Level of prompt filtering (low, medium, high)."
    )
    ENABLE_OUTPUT_FILTERING: bool = Field(
        default=True, description="Enable safety filtering for model outputs."
    )
    OUTPUT_FILTER_LEVEL: str = Field(
        default="medium", description="Level of output filtering (low, medium, high)."
    )

    # ======================================================================
    # API ACCESS CONTROL (Backend)
    # ======================================================================
    # REQUIRE_API_KEY is defined under SECURITY SETTINGS
    # API_KEY_EXPIRY_DAYS is defined under SECURITY SETTINGS
    # MAX_API_KEYS_PER_USER is defined under SECURITY SETTINGS

    # ======================================================================
    # TESTING / MOCK TOGGLES (Mainly for local development and testing)
    # ======================================================================
    ENABLE_MOCK_AUTH: bool = Field(
        default=False, description="If true, bypasses real authentication for testing."
    )
    ENABLE_MOCK_SUPABASE: bool = Field(
        default=False, description="If true, uses mock Supabase client for testing."
    )

    # ======================================================================
    # FRONTEND SPECIFIC (Next.js - these are prefixed with NEXT_PUBLIC_)
    # These are built into the frontend bundle and are publicly accessible.
    # ======================================================================
    NEXT_PUBLIC_APP_NAME: str = Field(
        default="ChatChonk", description="Public application name for frontend."
    )
    NEXT_PUBLIC_API_URL: AnyHttpUrl = Field(
        default="http://localhost:8080/api",
        description="Public API URL for frontend to connect to.",
    )
    NEXT_PUBLIC_SUPABASE_URL: Optional[AnyHttpUrl] = Field(
        default=None, description="Public Supabase URL for frontend."
    )
    NEXT_PUBLIC_SUPABASE_ANON_KEY: Optional[SecretStr] = Field(
        default=None, description="Public Supabase anonymous key for frontend."
    )

    class Config:
        """Pydantic configuration for Settings."""

        env_file = ".env.local"  # Load from .env.local for local development
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"  # Ignore extra environment variables not defined in Settings
        populate_by_name = True  # Allow fields to be populated by their alias
        protected_namespaces = ("model_")  # Protect pydantic's internal model_ prefix


# Move get_settings outside the class
@lru_cache()
def get_settings() -> "Settings":
    """
    Get application settings.
    Uses lru_cache to ensure settings are loaded only once.
    """
    settings = Settings()
    return settings


# Initialize settings
settings = get_settings()

# Configure logging based on settings

# Apply debug mode override for logging
logging.getLogger(__name__).setLevel(logging.DEBUG)
logging.getLogger("uvicorn").setLevel(logging.DEBUG)
logging.getLogger("uvicorn.access").setLevel(logging.DEBUG)
logging.getLogger("uvicorn.error").setLevel(logging.DEBUG)
logging.getLogger("fastapi").setLevel(logging.DEBUG)
logging.getLogger("httpx").setLevel(logging.DEBUG)
logging.getLogger("httpcore").setLevel(logging.DEBUG)
logging.getLogger("supabase").setLevel(logging.DEBUG)
logging.getLogger("postgrest").setLevel(logging.DEBUG)
logging.getLogger("pydantic_settings").setLevel(logging.DEBUG)
logging.getLogger("app").setLevel(logging.DEBUG)

# Ensure local directories exist if specified
if settings.UPLOAD_DIR:
    settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
if settings.TEMP_DIR:
    settings.TEMP_DIR.mkdir(parents=True, exist_ok=True)
if settings.EXPORT_DIR:
    settings.EXPORT_DIR.mkdir(parents=True, exist_ok=True)
if settings.STORAGE_PATH:
    settings.STORAGE_PATH.mkdir(parents=True, exist_ok=True)
if settings.EPHEMERAL_STORAGE_PATH:
    settings.EPHEMERAL_STORAGE_PATH.mkdir(parents=True, exist_ok=True)

# Ensure templates directory exists
settings.TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)

# Log key settings (excluding sensitive ones)
logging.info(f"Project Name: {settings.PROJECT_NAME}")
logging.info(f"Environment: {settings.ENVIRONMENT.value}")
logging.info(f"Debug Mode: {settings.DEBUG}")
logging.info(f"API URL: {settings.API_URL}")
logging.info(f"Frontend URL: {settings.FRONTEND_URL}")
logging.info(f"Allowed Origins: {settings.ALLOWED_ORIGINS}")
logging.info(f"Log Level: {settings.LOG_LEVEL.value}")
logging.info(f"Templates Directory: {settings.TEMPLATES_DIR.resolve()}")

# Conditional logging for Supabase
if settings.SUPABASE_URL:
    logging.info(f"Supabase URL: {settings.SUPABASE_URL}")
else:
    logging.warning("Supabase URL is not set. Database features may be limited.")

# Conditional logging for MSWAP Supabase
if settings.MSWAP_SUPABASE_URL:
    logging.info(f"MSWAP Supabase URL: {settings.MSWAP_SUPABASE_URL}")
else:
    logging.warning(
        "MSWAP Supabase URL is not set. ModelSwapper features may be limited."
    )

# Conditional logging for Cloudflare KV
if settings.CLOUDFLARE_API_TOKEN and settings.CLOUDFLARE_ACCOUNT_ID:
    logging.info("Cloudflare KV caching is configured.")
else:
    logging.warning("Cloudflare KV caching is not fully configured.")

# Conditional logging for AI Providers
if settings.HUGGINGFACE_API_KEY:
    logging.info("Hugging Face API key is set.")
if settings.OPENAI_API_KEY:
    logging.info("OpenAI API key is set.")
if settings.ANTHROPIC_API_KEY:
    logging.info("Anthropic API key is set.")
if settings.MISTRAL_API_KEY:
    logging.info("Mistral AI API key is set.")
if settings.DEEPSEEK_API_KEY:
    logging.info("DeepSeek API key is set.")
if settings.QWEN_API_KEY:
    logging.info("Qwen API key is set.")

# Conditional logging for Discord
if settings.DISCORD_BOT_TOKEN:
    logging.info("Discord integration is configured.")
else:
    logging.warning("Discord integration is not configured.")

# Conditional logging for Stripe
if settings.USE_STRIPE_PLANS:
    logging.info("Stripe billing is enabled.")
    if not settings.STRIPE_PUBLISHABLE_KEY or not settings.STRIPE_SECRET_KEY:
        logging.warning("Stripe keys are not fully configured for billing.")
else:
    logging.info("Stripe billing is disabled.")

# Conditional logging for IP filtering
if settings.ENABLE_IP_FILTERING:
    logging.info(f"IP Filtering Enabled. Allowed IPs: {settings.ALLOWED_IPS}")
else:
    logging.info("IP Filtering Disabled.")

# Conditional logging for Rate Limiting
if settings.RATE_LIMIT_ENABLED:
    logging.info(
        f"Rate Limiting Enabled: {settings.RATE_LIMIT_REQUESTS_PER_MINUTE} req/min."
    )
else:
    logging.info("Rate Limiting Disabled.")

# Conditional logging for Mock Toggles
if settings.ENABLE_MOCK_AUTH:
    logging.warning("Mock Authentication is ENABLED.")
if settings.ENABLE_MOCK_SUPABASE:
    logging.warning("Mock Supabase is ENABLED.")

# Ensure pydantic and pydantic-settings are installed in your environment:
# pip install pydantic pydantic-settings



