"""
ChatChonk Configuration Module

This module defines all configuration settings for the ChatChonk application.
It uses Pydantic's BaseSettings for automatic environment variable loading and validation.

Environment variables are loaded from .env file if present.

Author: Rip Jonesy
"""

import logging
import os
import secrets
from enum import Enum
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Union

from pydantic import (
    AnyHttpUrl,
    BaseSettings,
    EmailStr,
    Field,
    PostgresDsn, # Not directly used but good for reference if direct DB DSN needed
    SecretStr,
    validator,
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
    TEST = "test"


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
    PORT: int = Field(default=8080, description="Server port to listen on.") # User specified 8080
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
    # SUPABASE CONFIGURATION
    # ======================================================================
    SUPABASE_URL: Optional[AnyHttpUrl] = Field(default=None, description="Supabase project URL.")
    SUPABASE_KEY: Optional[SecretStr] = Field(default=None, alias="SUPABASE_ANON_KEY", description="Supabase anonymous key (public).") # Alias for common naming
    SUPABASE_SERVICE_ROLE_KEY: Optional[SecretStr] = Field(default=None, description="Supabase service role key (secret, for backend admin operations).")
    SUPABASE_PERSONAL_ACCESS_TOKEN: Optional[SecretStr] = Field(default=None, description="Supabase Personal Access Token for management API calls.")
    
    # Optional direct DB passwords if self-hosting or specific needs
    SUPABASE_DB_PASSWORD: Optional[SecretStr] = Field(default=None, description="Password for the main Supabase PostgreSQL database user.")
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
    UPLOAD_DIR: Path = Field(default=Path("./uploads"), description="Directory for initial file uploads (before moving to Supabase or processing).")
    TEMP_DIR: Path = Field(default=Path("./tmp"), description="Directory for temporary files during processing.")
    EXPORT_DIR: Path = Field(default=Path("./exports"), description="Directory for storing generated export files locally (if not directly streamed or sent to cloud).")
    STORAGE_PATH: Path = Field(default=Path("./storage"), description="General local storage path if not using cloud exclusively.")
    EPHEMERAL_STORAGE_PATH: Path = Field(default=Path("./ephemeral_storage"), description="Path for temporary storage of files that need quick cleanup.")
    EPHEMERAL_MAX_AGE_SECONDS: int = Field(default=7200, description="Max age for files in ephemeral storage (2 hours).")
    EPHEMERAL_CLEANUP_INTERVAL: int = Field(default=600, description="Interval for cleaning up ephemeral storage (10 minutes).")
    EPHEMERAL_ENCRYPTION_ENABLED: bool = Field(default=True, description="Enable encryption for files in ephemeral storage.")
    
    MAX_UPLOAD_SIZE: int = Field(default=2_147_483_648, description="Maximum upload size in bytes (2GB).") # 2GB
    CHUNK_SIZE: int = Field(default=1_048_576, description="Chunk size for streaming file uploads in bytes (1MB).")
    CLEANUP_INTERVAL: int = Field(default=3600, description="General interval for temporary file cleanup tasks (1 hour).")
    FILE_RETENTION_PERIOD: int = Field(default=86400, description="Time to keep processed files locally before potential deletion (24 hours).")
    ALLOWED_FILE_TYPES: Set[str] = Field(
        default={"zip", "json", "txt", "md", "csv"}, # From user's list
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
    LOG_FORMAT: str = Field(default="%(asctime)s - %(name)s - %(levelname)s - %(message)s", description="Log format string.")
    LOG_FILE: Optional[Path] = Field(default=Path("chatchonk.log"), description="Path to log file. If None, logs to stdout.")
    LOG_ROTATION_DAYS: int = Field(default=90, description="Number of days to keep log files before rotation/deletion.")
    ENABLE_AUDIT_LOGGING: bool = Field(default=True, description="Enable detailed audit logging for key actions.")

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
    # REDIS CACHING (Optional)
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


    # === Validators ===
    @validator("UPLOAD_DIR", "TEMP_DIR", "EXPORT_DIR", "TEMPLATES_DIR", "STORAGE_PATH", "EPHEMERAL_STORAGE_PATH", "LOG_FILE", pre=True, allow_reuse=True)
    def _ensure_path_type_and_create(cls, v: Union[str, Path, None]) -> Optional[Path]:
        """Ensure path variables are Path objects and create directories if they don't exist."""
        if v is None: # Handles optional LOG_FILE
            return None
        path = Path(v)
        # For LOG_FILE, only create parent directory. For others, create the directory itself.
        if str(v).endswith('.log'): # A bit heuristic, better if LOG_FILE was LOG_DIR
            path.parent.mkdir(parents=True, exist_ok=True)
        else:
            path.mkdir(parents=True, exist_ok=True)
        return path

    @validator("ALLOWED_ORIGINS", "ALLOWED_HOSTS", "ALLOWED_IPS", pre=True, allow_reuse=True)
    def _parse_comma_separated_list(cls, v: Union[str, List[str]]) -> List[str]:
        """Parse comma-separated string into a list of strings."""
        if isinstance(v, str):
            return [item.strip() for item in v.split(",") if item.strip()]
        return v
    
    @validator("ALLOWED_FILE_TYPES", pre=True, allow_reuse=True)
    def _parse_allowed_file_types(cls, v: Union[str, Set[str], List[str]]) -> Set[str]:
        """Parse allowed file types from string or list into a set of lowercase strings with leading dot."""
        if isinstance(v, str):
            types = {item.strip().lower() for item in v.split(",") if item.strip()}
        elif isinstance(v, list):
            types = {item.strip().lower() for item in v if isinstance(item, str) and item.strip()}
        elif isinstance(v, set):
            types = {item.strip().lower() for item in v if isinstance(item, str) and item.strip()}
        else:
            raise ValueError("ALLOWED_FILE_TYPES must be a comma-separated string, list, or set.")
        
        # Ensure leading dot for extensions
        return {f".{t}" if not t.startswith('.') else t for t in types}

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
    print(f"  Supabase URL: {settings.SUPABASE_URL or 'Not Set'}")
    print(f"  Allowed Origins: {settings.ALLOWED_ORIGINS}")
    print(f"  Upload Directory: {settings.UPLOAD_DIR.resolve()}")
    print(f"  Templates Directory: {settings.TEMPLATES_DIR.resolve()}")
    print(f"  Custom Tagline: {settings.Config.chatchonk_settings['app_tagline']}")

    if settings.REDIS_ENABLED:
        print(f"  Redis Enabled: Host={settings.REDIS_HOST}, Port={settings.REDIS_PORT}")
    else:
        print(f"  Redis Enabled: False")

