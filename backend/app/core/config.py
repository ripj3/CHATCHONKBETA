"""
ChatChonk Configuration Module

This module defines all configuration settings for the ChatChonk application.
It uses Pydantic's BaseSettings for automatic environment variable loading and validation.

Environment variables are loaded from .env file if present.

Author: Rip Jonesy
"""

import ast # Added for literal_eval
import logging
import os
import secrets
from enum import Enum
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Union

from pydantic import (
    AnyHttpUrl,
    EmailStr,
    Field,
    PostgresDsn, # Not directly used but good for reference if direct DB DSN needed
    SecretStr,
    validator,
)
from pydantic_settings import BaseSettings


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
    CUSTOM = "custom" # For potential self-hosted or other models


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    This class defines all configuration parameters for ChatChonk.
    """

    # ======================================================================
    # APPLICATION CORE SETTINGS
    # ======================================================================
    PROJECT_NAME: str = Field(default="ChatChonk", description="The name of the project.")
    APP_NAME: str = Field(default="ChatChonk", description="The name of the application (can be same as PROJECT_NAME).")
    APP_VERSION: str = Field(default="0.1.0", description="Application version.")
    ENVIRONMENT: Environment = Field(default=Environment.DEVELOPMENT, description="Application environment (development, staging, production).")
    DEBUG: bool = Field(default=False, description="Enable debug mode. Overrides LOG_LEVEL to DEBUG if True.")

    # ======================================================================
    # SERVER SETTINGS (FastAPI Backend)
    # ======================================================================
    API_V1_STR: str = Field(default="/api", description="API version prefix.")
    HOST: str = Field(default="0.0.0.0", description="Server host to bind to.")
    PORT: int = Field(default=8000, description="Server port to listen on.") # Match Dockerfile default
    ROOT_PATH: str = Field(default="", description="API root path prefix if running behind a reverse proxy with path stripping.")
    RELOAD: bool = Field(default=False, description="Enable hot reloading for Uvicorn (development only).")
    API_HOST: str = Field(default="127.0.0.1", description="Host for constructing API URLs, typically localhost for dev.")
    API_URL: AnyHttpUrl = Field(default="http://127.0.0.1:8080/api", description="Full base URL for the API in development.")
    PRODUCTION_API_URL: Optional[AnyHttpUrl] = Field(default=None, description="Full base URL for the API in production (e.g., https://api.chatchonk.com).")

    # ======================================================================
    # DOMAIN & FRONTEND CONFIGURATION
    # ======================================================================
    DOMAIN: str = Field(default="chatchonk.com", description="Main domain for the application.")
    FRONTEND_URL: AnyHttpUrl = Field(default="https://chatchonk.com", description="Base URL for the frontend application.")
    API_DOMAIN: Optional[str] = Field(default="api.chatchonk.com", description="Subdomain for the API in production.")

    # ======================================================================
    # SECURITY SETTINGS
    # ======================================================================
    SECRET_KEY: SecretStr = Field(
        default_factory=lambda: SecretStr(secrets.token_urlsafe(32)),
        alias="CHONK_SECRET_KEY", # Alias to match .env.example
        description="Secret key for signing tokens, cookies, etc. CRITICAL for production.",
    )
    ALLOWED_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://127.0.0.1:3000"], # Default for local Next.js dev
        description="Comma-separated list of allowed CORS origins.",
    )
    ALLOWED_HOSTS: List[str] = Field(
        default=["localhost", "127.0.0.1"],
        description="Comma-separated list of allowed host headers.",
    )
    API_KEY: Optional[SecretStr] = Field(default=None, description="Generic API key for securing internal or specific endpoints (development only or specific use cases).")
    REQUIRE_API_KEY: bool = Field(default=False, description="Whether a general API key is required for access.")
    API_KEY_EXPIRY_DAYS: int = Field(default=90, description="Default expiry for generated API keys.")
    MAX_API_KEYS_PER_USER: int = Field(default=5, description="Maximum API keys a user can generate.")

    # ======================================================================
    # SUPABASE CONFIGURATION (CHCH3 - Main Database)
    # ======================================================================
    SUPABASE_URL: Optional[AnyHttpUrl] = Field(default=None, description="Supabase project URL.")
    SUPABASE_KEY: Optional[SecretStr] = Field(default=None, alias="SUPABASE_ANON_KEY", description="Supabase anonymous key (public).") # Alias for common naming
    SUPABASE_SERVICE_ROLE_KEY: Optional[SecretStr] = Field(default=None, description="Supabase service role key (secret, for backend admin operations).")
    SUPABASE_PERSONAL_ACCESS_TOKEN: Optional[SecretStr] = Field(default=None, description="Supabase Personal Access Token for management API calls.")

    # Optional direct DB passwords if self-hosting or specific needs
    SUPABASE_DB_PASSWORD: Optional[SecretStr] = Field(default=None, description="Password for the main Supabase PostgreSQL database user.")

    # ======================================================================
    # MSWAP SUPABASE CONFIGURATION (ModelSwapper Database)
    # ======================================================================
    MSWAP_SUPABASE_URL: Optional[AnyHttpUrl] = Field(default=None, description="MSWAP Supabase project URL.")
    MSWAP_SUPABASE_KEY: Optional[SecretStr] = Field(default=None, alias="MSWAP_SUPABASE_ANON_KEY", description="MSWAP Supabase anonymous key (public).")
    MSWAP_SUPABASE_SERVICE_ROLE_KEY: Optional[SecretStr] = Field(default=None, description="MSWAP Supabase service role key (secret, for backend admin operations).")
    SUPABASE_DB_PASSWORD_MSWAP: Optional[SecretStr] = Field(default=None, description="Specific DB password for ModelSwapper service if it uses a different user/role.")

    # ======================================================================
    # SUPABASE STORAGE / S3 COMPATIBLE CONFIGURATION
    # ======================================================================
    SUPABASE_STORAGE_URL: Optional[AnyHttpUrl] = Field(default=None, description="Base URL for Supabase Storage (e.g., SUPABASE_URL/storage/v1).")
    SUPABASE_S3_ACCESS_KEY_ID: Optional[SecretStr] = Field(default=None, description="S3 compatible access key for Supabase Storage.")
    SUPABASE_S3_SECRET_ACCESS_KEY: Optional[SecretStr] = Field(default=None, description="S3 compatible secret key for Supabase Storage.")
    SUPABASE_S3_BUCKET: str = Field(default="files", description="Default S3 bucket name for Supabase Storage.")
    SUPABASE_STORAGE_BUCKET: str = Field(default="files", description="Default bucket name for Supabase Storage (can be same as S3_BUCKET).")

    # ======================================================================
    # FILE PROCESSING & LOCAL STORAGE SETTINGS
    # ======================================================================
    UPLOAD_DIR: Optional[Path] = Field(default=None, description="Directory for initial file uploads (will be None if using cloud storage).")
    TEMP_DIR: Optional[Path] = Field(default=None, description="Directory for temporary files during processing.")
    EXPORT_DIR: Optional[Path] = Field(default=None, description="Directory for storing generated export files locally (will be None if directly streamed or sent to cloud).")
    STORAGE_PATH: Optional[Path] = Field(default=None, description="General local storage path (will be None if using cloud exclusively).")
    EPHEMERAL_STORAGE_PATH: Optional[Path] = Field(default=None, description="Path for temporary storage of files that need quick cleanup.")
    EPHEMERAL_MAX_AGE_SECONDS: int = Field(default=7200, description="Max age for files in ephemeral storage (2 hours).")
    EPHEMERAL_CLEANUP_INTERVAL: int = Field(default=600, description="Interval for cleaning up ephemeral storage (10 minutes).")
    EPHEMERAL_ENCRYPTION_ENABLED: bool = Field(default=True, description="Enable encryption for files in ephemeral storage.")

    MAX_UPLOAD_SIZE: int = Field(default=2_147_483_648, description="Maximum upload size in bytes (2GB).") # 2GB
    CHUNK_SIZE: int = Field(default=1_048_576, description="Chunk size for streaming file uploads in bytes (1MB).")
    CLEANUP_INTERVAL: int = Field(default=3600, description="General interval for temporary file cleanup tasks (1 hour).")
    FILE_RETENTION_PERIOD: int = Field(default=86400, description="Time to keep processed files locally before potential deletion (24 hours).")
    ALLOWED_FILE_TYPES: str = Field(
        default="zip,json,txt,md,csv", # Comma-separated string for environment variable parsing
        description="Comma-separated list of allowed file extensions for direct uploads (archives might contain more types internally).",
    )

    # ======================================================================
    # AI PROVIDER SETTINGS (AutoModel)
    # ======================================================================
    DEFAULT_AI_PROVIDER: AiProvider = Field(default=AiProvider.HUGGINGFACE, description="Default AI provider for processing if not specified.")

    HUGGINGFACE_API_KEY: Optional[SecretStr] = Field(default=None, description="API key for Hugging Face Hub and Inference API.")
    HUGGINGFACE_DEFAULT_MODEL: str = Field(default="mistralai/Mistral-7B-Instruct-v0.2", description="Default Hugging Face model for general tasks.")
    HUGGINGFACE_SPACE: Optional[str] = Field(default=None, description="Identifier for a specific Hugging Face Space if used.")
    HUGGINGFACE_STREAMLIT_URL: Optional[AnyHttpUrl] = Field(default=None, description="URL for a Hugging Face Streamlit app if integrated.")

    OPENAI_API_KEY: Optional[SecretStr] = Field(default=None, description="API key for OpenAI.")
    OPENAI_DEFAULT_MODEL: str = Field(default="gpt-4o", description="Default OpenAI model.")

    ANTHROPIC_API_KEY: Optional[SecretStr] = Field(default=None, description="API key for Anthropic (Claude).")
    ANTHROPIC_DEFAULT_MODEL: str = Field(default="claude-3-opus-20240229", description="Default Anthropic model.")

    MISTRAL_API_KEY: Optional[SecretStr] = Field(default=None, description="API key for Mistral AI.")
    MISTRAL_DEFAULT_MODEL: str = Field(default="mistral-large-latest", description="Default Mistral model.")

    DEEPSEEK_API_KEY: Optional[SecretStr] = Field(default=None, description="API key for DeepSeek.")
    DEEPSEEK_DEFAULT_MODEL: str = Field(default="deepseek-coder", description="Default DeepSeek model.")

    QWEN_API_KEY: Optional[SecretStr] = Field(default=None, description="API key for Qwen (Alibaba).")
    QWEN_DEFAULT_MODEL: str = Field(default="qwen-max", description="Default Qwen model.")

    # ======================================================================
    # TEMPLATE SETTINGS
    # ======================================================================
    TEMPLATES_DIR: Path = Field(default=Path("./templates"), description="Directory where ChatChonk processing templates (YAML files) are stored.")
    DEFAULT_TEMPLATE: str = Field(default="adhd-idea-harvest", description="Default template ID to use if none is specified by the user.")

    # ======================================================================
    # LOGGING CONFIGURATION
    # ======================================================================
    LOG_LEVEL: LogLevel = Field(default=LogLevel.INFO, description="Logging level for the application.")
    LOG_FILE: Optional[Path] = Field(default=None, description="Path to the log file. Set to None for stdout, or a path for file logging.")
    LOG_FORMAT: str = Field(default="%(levelname)s:	%(asctime)s %(name)s - %(message)s", description="Log output format string.")

    # ======================================================================
    # EMAIL SETTINGS (Optional, for future use like notifications, MFA)
    # ======================================================================
    SMTP_HOST: Optional[str] = Field(default=None, description="SMTP server host for sending emails.")
    SMTP_PORT: Optional[int] = Field(default=587, description="SMTP server port.")
    SMTP_USER: Optional[str] = Field(default=None, description="SMTP username.")
    SMTP_PASSWORD: Optional[SecretStr] = Field(default=None, description="SMTP password.")
    EMAILS_FROM_EMAIL: Optional[EmailStr] = Field(default=None, description="Default sender email address for application emails.")
    EMAILS_FROM_NAME: Optional[str] = Field(default=None, description="Default sender name for application emails.")

    # ======================================================================
    # GITHUB CONFIGURATION (Optional, if app interacts with GitHub)
    # ======================================================================
    GITHUB_PERSONAL_ACCESS_TOKEN: Optional[SecretStr] = Field(default=None, description="GitHub Personal Access Token for API interactions.")

    # ======================================================================
    # STRIPE BILLING CONFIGURATION (Optional, for paid tiers)
    # ======================================================================
    STRIPE_PUBLISHABLE_KEY: Optional[SecretStr] = Field(default=None, description="Stripe publishable API key (pk_...).")
    STRIPE_SECRET_KEY: Optional[SecretStr] = Field(default=None, alias="STRIPE_RESTRICTED_KEY", description="Stripe secret API key (sk_live_... or rk_live_...).") # Renamed for clarity
    STRIPE_SECRET_TEST_KEY: Optional[SecretStr] = Field(default=None, alias="STRIPE_RESTRICTED_TEST_KEY", description="Stripe secret test API key (sk_test_... or rk_test_...).")
    STRIPE_WEBHOOK_SECRET: Optional[SecretStr] = Field(default=None, description="Stripe webhook signing secret (whsec_...).")

    STRIPE_PRICE_LILBEAN: Optional[str] = Field(default=None, description="Stripe Price ID for 'LilBean' tier.")
    STRIPE_PRICE_CLAWBACK: Optional[str] = Field(default=None, description="Stripe Price ID for 'Clawback' tier.")
    STRIPE_PRICE_BIGCHONK: Optional[str] = Field(default=None, description="Stripe Price ID for 'BigChonk' tier.")
    STRIPE_PRICE_MEOWTRIX: Optional[str] = Field(default=None, description="Stripe Price ID for 'Meowtrix' tier.")
    STRIPE_PRICE_CLAWBACK_YEARLY: Optional[str] = Field(default=None, description="Stripe Price ID for 'Clawback Yearly' tier.")
    STRIPE_PRICE_BIGCHONK_YEARLY: Optional[str] = Field(default=None, description="Stripe Price ID for 'BigChonk Yearly' tier.")
    STRIPE_PRICE_MEOWTRIX_YEARLY: Optional[str] = Field(default=None, description="Stripe Price ID for 'Meowtrix Yearly' tier.")
    USE_STRIPE_PLANS: bool = Field(default=True, description="Flag to enable/disable Stripe plan integration logic.")
    STRIPE_PROMO_CODE: Optional[str] = Field(default=None, description="Default monthly promo code for Stripe.")
    STRIPE_PROMO_CODE_YEARLY: Optional[str] = Field(default=None, description="Default yearly promo code for Stripe.")

    # ======================================================================
    # DISCORD INTEGRATION CONFIGURATION
    # ======================================================================
    DISCORD_BOT_TOKEN: Optional[SecretStr] = Field(default=None, description="Discord bot token for ChatChonk support bot.")
    DISCORD_GUILD_ID: Optional[int] = Field(default=None, description="Discord server (guild) ID for ChatChonk support.")

    # Channel IDs
    DISCORD_GENERAL_CHANNEL_ID: Optional[int] = Field(default=None, description="General chat channel ID.")
    DISCORD_SUPPORT_CHANNEL_ID: Optional[int] = Field(default=None, description="Support channel ID.")
    DISCORD_ANNOUNCEMENTS_CHANNEL_ID: Optional[int] = Field(default=None, description="Announcements channel ID.")
    DISCORD_FEEDBACK_CHANNEL_ID: Optional[int] = Field(default=None, description="Feedback channel ID.")

    # User tier role IDs
    DISCORD_FREE_ROLE_ID: Optional[int] = Field(default=None, description="Free tier role ID.")
    DISCORD_LILBEAN_ROLE_ID: Optional[int] = Field(default=None, description="LilBean tier role ID.")
    DISCORD_CLAWBACK_ROLE_ID: Optional[int] = Field(default=None, description="Clawback tier role ID.")
    DISCORD_BIGCHONK_ROLE_ID: Optional[int] = Field(default=None, description="BigChonk tier role ID.")
    DISCORD_MEOWTRIX_ROLE_ID: Optional[int] = Field(default=None, description="Meowtrix tier role ID.")

    # Staff role IDs
    DISCORD_ADMIN_ROLE_ID: Optional[int] = Field(default=None, description="Admin role ID.")
    DISCORD_MODERATOR_ROLE_ID: Optional[int] = Field(default=None, description="Moderator role ID.")
    DISCORD_SUPPORT_ROLE_ID: Optional[int] = Field(default=None, description="Support team role ID.")

    # ======================================================================
    # CLOUDFLARE KV CACHING (Recommended)
    # ======================================================================
    CLOUDFLARE_API_TOKEN: Optional[SecretStr] = Field(default=None, description="Cloudflare API token for KV access.")
    CLOUDFLARE_ACCOUNT_ID: Optional[str] = Field(default=None, description="Cloudflare account ID.")
    CLOUDFLARE_KV_NAMESPACE_ID: Optional[str] = Field(default=None, description="Cloudflare KV namespace ID for caching.")

    # ======================================================================
    # REDIS CACHING (Optional - Deprecated in favor of Cloudflare KV)
    # ======================================================================
    REDIS_HOST: str = Field(default="localhost", description="Redis server host.")
    REDIS_PORT: int = Field(default=6379, description="Redis server port.")
    REDIS_PASSWORD: Optional[SecretStr] = Field(default=None, description="Redis password (if any).")
    REDIS_ENABLED: bool = Field(default=False, description="Enable Redis for caching and other tasks.") # Added to control usage

    # ======================================================================
    # ADVANCED SECURITY & VALIDATION
    # ======================================================================
    RATE_LIMIT_ENABLED: bool = Field(default=False, description="Enable rate limiting for API endpoints.")
    RATE_LIMIT_REQUESTS: int = Field(default=100, description="Default rate limit requests count.") # Renamed from user list for clarity
    RATE_LIMIT_WINDOW_MINUTES: int = Field(default=60, description="Default rate limit window in minutes.") # Renamed
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = Field(default=1000, description="Alternative rate limit: requests per minute (used if RATE_LIMIT_WINDOW_MINUTES is not primary).")

    ENABLE_INPUT_VALIDATION: bool = Field(default=True, description="Enable strict input validation for API requests.")
    ENABLE_CONTENT_VALIDATION: bool = Field(default=True, description="Enable validation of content within uploaded files.")
    ENABLE_REQUEST_SIGNING: bool = Field(default=False, description="Enable request signing for specific sensitive operations (advanced).")
    REQUEST_SIGNATURE_EXPIRY_SECONDS: int = Field(default=300, description="Expiry time for request signatures (5 minutes).")
    ENABLE_IP_FILTERING: bool = Field(default=False, description="Enable IP address filtering for API access.")
    ALLOWED_IPS: List[str] = Field(default=[], description="Comma-separated list of allowed IP addresses or CIDR blocks if IP filtering is enabled.")

    # ======================================================================
    # PROMPT & OUTPUT SAFETY (Content Filtering)
    # ======================================================================
    ENABLE_PROMPT_FILTERING: bool = Field(default=True, description="Enable filtering of prompts sent to AI models for safety.")
    PROMPT_FILTER_LEVEL: str = Field(default="medium", description="Severity level for prompt filtering (e.g., low, medium, high).")
    ENABLE_OUTPUT_FILTERING: bool = Field(default=True, description="Enable filtering of outputs received from AI models for safety.")
    OUTPUT_FILTER_LEVEL: str = Field(default="medium", description="Severity level for output filtering.")

    # ======================================================================
    # TESTING & MOCKING (Development/Test environments only)
    # ======================================================================
    ENABLE_MOCK_AUTH: bool = Field(default=False, description="Enable mock authentication for testing purposes.")
    ENABLE_MOCK_SUPABASE: bool = Field(default=False, description="Enable mock Supabase client for testing purposes.")


    # === Post-initialization for environment-specific paths ===
    def model_post_init(self, __context: Any) -> None:
        """Set environment-specific default paths and create directories if needed."""
        # UPLOAD_DIR, EXPORT_DIR, STORAGE_PATH are expected to be None if using cloud storage.

        if self.ENVIRONMENT in {Environment.DEVELOPMENT, Environment.TEST}:
            # Local development paths for temporary files and logs
            self.TEMP_DIR = self.TEMP_DIR or Path("./tmp") # Default to ./tmp if not set by env
            self.EPHEMERAL_STORAGE_PATH = self.EPHEMERAL_STORAGE_PATH or Path("./ephemeral_storage") # Default if not set

            # LOG_FILE defaults to None (from Field definition).
            # Only set a local file path if it's not already defined (e.g., by an env var)
            # and we are in a dev/test environment.
            if self.LOG_FILE is None:
                self.LOG_FILE = Path("chatchonk.log")

            # Create local directories if they are configured
            if self.TEMP_DIR:
                self.TEMP_DIR.mkdir(parents=True, exist_ok=True)
            if self.EPHEMERAL_STORAGE_PATH:
                self.EPHEMERAL_STORAGE_PATH.mkdir(parents=True, exist_ok=True)
            if self.LOG_FILE: # If LOG_FILE is now set (e.g., to "chatchonk.log")
                # Ensure parent directory for the log file exists for local file logging
                self.LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

        elif self.ENVIRONMENT in {Environment.STAGING, Environment.PRODUCTION, Environment.PRODUCTION_BETA}:
            # For cloud environments, TEMP_DIR and EPHEMERAL_STORAGE_PATH might use /tmp
            self.TEMP_DIR = self.TEMP_DIR or Path("/tmp") # /tmp should exist
            self.EPHEMERAL_STORAGE_PATH = self.EPHEMERAL_STORAGE_PATH or Path("/tmp/ephemeral_storage")

            # For production, LOG_FILE is already None by default (directing logs to stdout).
            # If LOG_FILE is explicitly set via an environment variable to a path (e.g., /var/log/app.log),
            # it's assumed that path is managed by the Docker image/environment, so no directory creation here.
            pass # No specific LOG_FILE path assignment needed here, relies on default=None or env var.

    # === Validators ===
    @validator("ALLOWED_ORIGINS", "ALLOWED_HOSTS", "ALLOWED_IPS", pre=True, allow_reuse=True)
    def _parse_comma_separated_list(cls, v: Union[str, List[str]]) -> List[str]:
        """Parse comma-separated string into a list of strings."""
        if isinstance(v, str):
            return [item.strip() for item in v.split(",") if item.strip()]
        return v

    @validator("ALLOWED_FILE_TYPES", pre=True, allow_reuse=True)
    def _parse_allowed_file_types(cls, v: Union[str, List[str]]) -> str:
        """
        Ensure ALLOWED_FILE_TYPES is a comma-separated string.
        If a list or set is provided, convert it to a comma-separated string.
        """
        if isinstance(v, (list, set)):
            # Convert list/set to comma-separated string
            return ",".join([item.strip().lower().lstrip('.') for item in v if isinstance(item, str) and item.strip()])
        elif isinstance(v, str):
            # Ensure it's a clean comma-separated string without extra spaces or leading dots
            return ",".join([item.strip().lower().lstrip('.') for item in v.split(",") if item.strip()])
        raise ValueError("ALLOWED_FILE_TYPES must be a comma-separated string, list, or set.")

    @validator("DEBUG", allow_reuse=True)
    def _debug_implies_log_level_debug(cls, v: bool, values: Dict[str, Any]) -> bool:
        """If DEBUG is True, set LOG_LEVEL to DEBUG unless already more verbose."""
        if v and values.get("LOG_LEVEL") not in [LogLevel.DEBUG]:
            values["LOG_LEVEL"] = LogLevel.DEBUG
            logging.warning("DEBUG mode enabled: Overriding LOG_LEVEL to DEBUG.")
        return v

    @validator("DEFAULT_AI_PROVIDER", allow_reuse=True)
    def _validate_default_ai_provider_key(cls, v: AiProvider, values: Dict[str, Any]) -> AiProvider:
        """Validate that the API key for the default AI provider is set, or fall back."""
        key_name_map = {
            AiProvider.HUGGINGFACE: "HUGGINGFACE_API_KEY",
            AiProvider.OPENAI: "OPENAI_API_KEY",
            AiProvider.ANTHROPIC: "ANTHROPIC_API_KEY",
            AiProvider.MISTRAL: "MISTRAL_API_KEY",
            AiProvider.DEEPSEEK: "DEEPSEEK_API_KEY",
            AiProvider.QWEN: "QWEN_API_KEY",
        }

        default_provider_key_env_var = key_name_map.get(v)

        if default_provider_key_env_var and not values.get(default_provider_key_env_var):
            logging.warning(
                f"API key for default provider '{v.value}' ({default_provider_key_env_var}) is not set. "
                "Attempting to find an alternative provider with a set API key."
            )
            # Try to find any available provider with a key
            for provider_enum, key_env_var in key_name_map.items():
                if values.get(key_env_var):
                    logging.warning(f"Falling back to '{provider_enum.value}' as it has an API key.")
                    return provider_enum

            logging.error(
                f"No API key found for the default provider '{v.value}' or any alternative providers. "
                "AI processing will likely fail. Please set at least one AI provider API key."
            )
        return v

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False # Typically env vars are case-insensitive, but can be True if needed
        validate_assignment = True # Ensure type hints are respected on assignment

        # Custom section for ChatChonk-specific metadata (not loaded from env)
        chatchonk_settings = {
            "app_tagline": "Tame the Chatter. Find the Signal.",
            "app_audience": "Second-brain builders and neurodivergent thinkers",
            "app_creator": "Rip Jonesy",
            "app_creation_date": "May 2025",
        }

@lru_cache()
def get_settings() -> Settings:
    """
    Get cached application settings.
    This function ensures that settings are loaded only once.
    """
    logging.info("Loading application settings...")
    settings = Settings()
    if settings.DEBUG: # Re-check after full load
        logging.getLogger().setLevel(logging.DEBUG)
        for handler in logging.getLogger().handlers:
            handler.setLevel(logging.DEBUG)
        logging.debug("Debug mode is ON. Logging level set to DEBUG.")
    else:
        logging.getLogger().setLevel(settings.LOG_LEVEL.value)
        for handler in logging.getLogger().handlers:
            handler.setLevel(settings.LOG_LEVEL.value)


    # Ensure Supabase keys are present if URL is set
    if settings.SUPABASE_URL and (not settings.SUPABASE_KEY or not settings.SUPABASE_SERVICE_ROLE_KEY):
        logging.warning(
            "SUPABASE_URL is set, but SUPABASE_ANON_KEY or SUPABASE_SERVICE_ROLE_KEY is missing. "
            "Supabase integration may not function correctly."
        )

    return settings

# For easy access to settings throughout the application
settings = get_settings()

if __name__ == "__main__":
    # Example of how to access settings
    print(f"ChatChonk Settings Loaded for Environment: {settings.ENVIRONMENT.value}")
    print(f"  Project Name: {settings.PROJECT_NAME}")
    print(f"  API URL (Dev): {settings.API_URL}")
    print(f"  Production API URL: {settings.PRODUCTION_API_URL or 'Not Set'}")
    print(f"  Debug Mode: {settings.DEBUG}")
    print(f"  Log Level: {settings.LOG_LEVEL.value}")
    print(f"  Default AI Provider: {settings.DEFAULT_AI_PROVIDER.value}")
    if settings.HUGGINGFACE_API_KEY:
        print(f"  HuggingFace API Key: Set (value redacted)")
    else:
        print(f"  HuggingFace API Key: Not Set")

    # Debugging: Print raw environment variable to confirm it's seen by the process
    import os
    hf_key_raw = os.getenv("HUGGINGFACE_API_KEY")
    print(f"  Raw HUGGINGFACE_API_KEY from os.getenv: {'Set' if hf_key_raw else 'Not Set'}")
    print(f"  Supabase URL: {settings.SUPABASE_URL or 'Not Set'}")
    print(f"  Allowed Origins: {settings.ALLOWED_ORIGINS}")
    # Ensure LOG_FILE is handled correctly, it might be None
    log_file_path = "stdout"
    if settings.LOG_FILE:
        try:
            log_file_path = str(settings.LOG_FILE.resolve())
        except Exception: # Handle cases where resolve might fail (e.g. not a file path)
            log_file_path = str(settings.LOG_FILE)
    elif settings.LOG_FILE is None:
        log_file_path = "None (stdout)"


    print(f"  Log File: {log_file_path}")

    # Check UPLOAD_DIR, TEMP_DIR etc. safely as they can be None
    upload_dir_path = "Not Set (Cloud Storage)"
    if settings.UPLOAD_DIR:
        try:
            upload_dir_path = str(settings.UPLOAD_DIR.resolve())
        except Exception:
            upload_dir_path = str(settings.UPLOAD_DIR)
    print(f"  Upload Directory: {upload_dir_path}")

    templates_dir_path = "Not Set"
    if settings.TEMPLATES_DIR:
        try:
            templates_dir_path = str(settings.TEMPLATES_DIR.resolve())
        except Exception:
            templates_dir_path = str(settings.TEMPLATES_DIR)
    print(f"  Templates Directory: {templates_dir_path}")

    print(f"  Custom Tagline: {settings.Config.chatchonk_settings['app_tagline']}")

    if settings.REDIS_ENABLED:
        print(f"  Redis Enabled: Host={settings.REDIS_HOST}, Port={settings.REDIS_PORT}")
    else:
        print(f"  Redis Enabled: False")

# Update the main section to correctly print LOG_FILE path
if __name__ == "__main__":
    # ... (previous print statements) ...

    # Correctly print LOG_FILE path, handling None
    log_file_display = "None (stdout)"
    if settings.LOG_FILE:
        try:
            # Attempt to resolve if it's a Path object and not None
            log_file_display = str(settings.LOG_FILE.resolve())
        except AttributeError:
            # Fallback if LOG_FILE is not a Path object (e.g. already a string, or if resolve fails)
            log_file_display = str(settings.LOG_FILE)
    print(f"  Log File: {log_file_display}")

    # ... (other print statements like UPLOAD_DIR, TEMPLATES_DIR, etc.) ...
    # Ensure UPLOAD_DIR is handled correctly if it's None
    upload_dir_display = "None (Cloud Storage)"
    if settings.UPLOAD_DIR:
        try:
            upload_dir_display = str(settings.UPLOAD_DIR.resolve())
        except AttributeError:
            upload_dir_display = str(settings.UPLOAD_DIR)
    print(f"  Upload Directory: {upload_dir_display}")

    # Ensure TEMPLATES_DIR is handled correctly
    templates_dir_display = "Not Set"
    if settings.TEMPLATES_DIR:
        try:
            templates_dir_display = str(settings.TEMPLATES_DIR.resolve())
        except AttributeError:
            templates_dir_display = str(settings.TEMPLATES_DIR)
    print(f"  Templates Directory: {templates_dir_display}")
    # ...
    # (The rest of the __main__ block)
    # ...
    print(f"  Custom Tagline: {settings.Config.chatchonk_settings['app_tagline']}")

    if settings.REDIS_ENABLED:
        print(f"  Redis Enabled: Host={settings.REDIS_HOST}, Port={settings.REDIS_PORT}")
    else:
        print(f"  Redis Enabled: False")

# Final __main__ block for clarity, ensuring only one is active.
# Remove previous __main__ if this is the intended one.
if __name__ == "__main__":
    # Example of how to access settings
    print(f"ChatChonk Settings Loaded for Environment: {settings.ENVIRONMENT.value}")
    print(f"  Project Name: {settings.PROJECT_NAME}")
    print(f"  API URL (Dev): {settings.API_URL}")
    print(f"  Production API URL: {settings.PRODUCTION_API_URL or 'Not Set'}")
    print(f"  Debug Mode: {settings.DEBUG}")
    print(f"  Log Level: {settings.LOG_LEVEL.value}")

    # Display LOG_FILE path
    log_file_display = "None (stdout)"
    if settings.LOG_FILE:
        # Check if it's a Path object before calling resolve
        if isinstance(settings.LOG_FILE, Path):
            try:
                log_file_display = str(settings.LOG_FILE.resolve())
            except Exception as e: # Catch potential errors if path is invalid
                log_file_display = f"Invalid Path ({settings.LOG_FILE}): {e}"
        else: # If it's not a Path object (e.g. already a string)
            log_file_display = str(settings.LOG_FILE)
    print(f"  Log File: {log_file_display}")

    print(f"  Default AI Provider: {settings.DEFAULT_AI_PROVIDER.value}")
    if settings.HUGGINGFACE_API_KEY:
        print(f"  HuggingFace API Key: Set (value redacted)")
    else:
        print(f"  HuggingFace API Key: Not Set")

    # Debugging: Print raw environment variable
    hf_key_raw = os.getenv("HUGGINGFACE_API_KEY")
    print(f"  Raw HUGGINGFACE_API_KEY from os.getenv: {'Set' if hf_key_raw else 'Not Set'}")

    print(f"  Supabase URL: {settings.SUPABASE_URL or 'Not Set'}")
    print(f"  Allowed Origins: {settings.ALLOWED_ORIGINS}")

    # Display UPLOAD_DIR path
    upload_dir_display = "None (Cloud Storage)"
    if settings.UPLOAD_DIR:
        if isinstance(settings.UPLOAD_DIR, Path):
            try:
                upload_dir_display = str(settings.UPLOAD_DIR.resolve())
            except Exception as e:
                upload_dir_display = f"Invalid Path ({settings.UPLOAD_DIR}): {e}"
        else:
            upload_dir_display = str(settings.UPLOAD_DIR)
    print(f"  Upload Directory: {upload_dir_display}")

    # Display TEMPLATES_DIR path
    templates_dir_display = "Not Set"
    if settings.TEMPLATES_DIR:
        if isinstance(settings.TEMPLATES_DIR, Path):
            try:
                templates_dir_display = str(settings.TEMPLATES_DIR.resolve())
            except Exception as e:
                templates_dir_display = f"Invalid Path ({settings.TEMPLATES_DIR}): {e}"
        else:
            templates_dir_display = str(settings.TEMPLATES_DIR)
    print(f"  Templates Directory: {templates_dir_display}")

    print(f"  Custom Tagline: {settings.Config.chatchonk_settings['app_tagline']}")

    if settings.REDIS_ENABLED:
        print(f"  Redis Enabled: Host={settings.REDIS_HOST}, Port={settings.REDIS_PORT}")
    else:
        print(f"  Redis Enabled: False")

    # Example for EPHEMERAL_STORAGE_PATH
    ephemeral_path_display = "Not Set"
    if settings.EPHEMERAL_STORAGE_PATH:
        if isinstance(settings.EPHEMERAL_STORAGE_PATH, Path):
            try:
                ephemeral_path_display = str(settings.EPHEMERAL_STORAGE_PATH.resolve())
            except Exception as e:
                ephemeral_path_display = f"Invalid Path ({settings.EPHEMERAL_STORAGE_PATH}): {e}"
        else:
            ephemeral_path_display = str(settings.EPHEMERAL_STORAGE_PATH)
    print(f"  Ephemeral Storage Path: {ephemeral_path_display}")

    print("\nTesting model_post_init behavior:")
    print(f"  Environment: {settings.ENVIRONMENT.value}")
    print(f"  TEMP_DIR: {settings.TEMP_DIR}")
    print(f"  EPHEMERAL_STORAGE_PATH: {settings.EPHEMERAL_STORAGE_PATH}")
    print(f"  LOG_FILE (after init): {settings.LOG_FILE}")

    if settings.ENVIRONMENT in {Environment.DEVELOPMENT, Environment.TEST}:
        if settings.TEMP_DIR: assert settings.TEMP_DIR.exists(), "TEMP_DIR should exist in dev/test"
        if settings.EPHEMERAL_STORAGE_PATH: assert settings.EPHEMERAL_STORAGE_PATH.exists(), "EPHEMERAL_STORAGE_PATH should exist in dev/test"
        if settings.LOG_FILE and settings.LOG_FILE.name == "chatchonk.log":
            assert settings.LOG_FILE.parent.exists(), "LOG_FILE parent should exist in dev/test if it's chatchonk.log"
            print("  Local directory creation for TEMP, EPHEMERAL, LOG_FILE parent verified (if applicable).")

    print("\nAll settings loaded and basic checks complete.")
