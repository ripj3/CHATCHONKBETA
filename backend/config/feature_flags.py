"""
Feature flags for ChatChonk - Enable/disable features without redeployment
"""
import os
from typing import Dict, Any

class FeatureFlags:
    """Centralized feature flag management"""
    
    def __init__(self):
        self._flags = {
            # Core features - Start with minimal set
            "file_processing": self._get_bool_env("FEATURE_FILE_PROCESSING", False),
            "ai_processing": self._get_bool_env("FEATURE_AI_PROCESSING", False),
            "admin_dashboard": self._get_bool_env("FEATURE_ADMIN_DASHBOARD", False),

            # AutoModel features - Disabled initially
            "automodel_enabled": self._get_bool_env("FEATURE_AUTOMODEL", False),
            "model_swapper": self._get_bool_env("FEATURE_MODEL_SWAPPER", False),

            # Integrations - Disabled initially
            "discord_integration": self._get_bool_env("FEATURE_DISCORD", False),
            "cloudflare_kv": self._get_bool_env("FEATURE_CLOUDFLARE_KV", False),

            # Development features
            "debug_mode": self._get_bool_env("DEBUG_MODE", False),
            "metrics_enabled": self._get_bool_env("FEATURE_METRICS", False),
            "minimal_mode": self._get_bool_env("MINIMAL_MODE", True),
        }
    
    def _get_bool_env(self, key: str, default: bool) -> bool:
        """Get boolean environment variable"""
        value = os.getenv(key, str(default)).lower()
        return value in ("true", "1", "yes", "on")
    
    def is_enabled(self, flag_name: str) -> bool:
        """Check if a feature flag is enabled"""
        return self._flags.get(flag_name, False)
    
    def get_all_flags(self) -> Dict[str, Any]:
        """Get all feature flags"""
        return self._flags.copy()

# Global instance
feature_flags = FeatureFlags()
