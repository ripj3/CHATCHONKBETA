"""
Cache Service - Cloudflare KV with In-Memory Fallback for AutoModel

This service provides caching functionality for the AutoModel system.
It uses Cloudflare KV when available (1GB free tier) and falls back to in-memory cache.

Author: Rip Jonesy
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional
import httpx

logger = logging.getLogger("chatchonk.cache")


class CacheService:
    """Cache service with Cloudflare KV and in-memory fallback."""

    def __init__(self):
        """Initialize the cache service."""
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._cleanup_task: Optional[asyncio.Task] = None
        self._http_client: Optional[httpx.AsyncClient] = None
        self._use_cloudflare = False
        self._start_cleanup_task()

        # Try to initialize Cloudflare KV if available
        self._init_cloudflare()

    def _init_cloudflare(self):
        """Initialize Cloudflare KV connection if available."""
        try:
            from app.core.config import get_settings

            settings = get_settings()

            # Check if Cloudflare credentials are available
            cf_api_token = getattr(settings, "CLOUDFLARE_API_TOKEN", None)
            cf_account_id = getattr(settings, "CLOUDFLARE_ACCOUNT_ID", None)
            cf_namespace_id = getattr(settings, "CLOUDFLARE_KV_NAMESPACE_ID", None)

            if cf_api_token and cf_account_id and cf_namespace_id:
                self._cf_api_token = (
                    cf_api_token.get_secret_value()
                    if hasattr(cf_api_token, "get_secret_value")
                    else cf_api_token
                )
                self._cf_account_id = cf_account_id
                self._cf_namespace_id = cf_namespace_id
                self._cf_base_url = f"https://api.cloudflare.com/client/v4/accounts/{cf_account_id}/storage/kv/namespaces/{cf_namespace_id}"

                self._http_client = httpx.AsyncClient(
                    headers={
                        "Authorization": f"Bearer {self._cf_api_token}",
                        "Content-Type": "application/json",
                    },
                    timeout=10.0,
                )
                self._use_cloudflare = True
                logger.info("Cloudflare KV cache initialized successfully")
            else:
                logger.info("Cloudflare KV not configured, using in-memory cache")
        except Exception as e:
            logger.warning(
                f"Failed to initialize Cloudflare KV, falling back to in-memory cache: {e}"
            )
            self._use_cloudflare = False

    def _start_cleanup_task(self):
        """Start the background cleanup task."""
        if self._cleanup_task is None or self._cleanup_task.done():
            self._cleanup_task = asyncio.create_task(self._cleanup_expired())

    async def _cleanup_expired(self):
        """Background task to clean up expired cache entries."""
        while True:
            try:
                now = datetime.utcnow()
                expired_keys = []

                for key, entry in self._cache.items():
                    if entry["expires_at"] <= now:
                        expired_keys.append(key)

                for key in expired_keys:
                    del self._cache[key]

                if expired_keys:
                    logger.debug(
                        f"Cleaned up {len(expired_keys)} expired cache entries"
                    )

                # Sleep for 60 seconds before next cleanup
                await asyncio.sleep(60)

            except Exception as e:
                logger.error(f"Cache cleanup error: {e}")
                await asyncio.sleep(60)

    async def get(self, key: str) -> Optional[str]:
        """
        Get a value from the cache.

        Args:
            key: Cache key

        Returns:
            Cached value as string, or None if not found or expired
        """
        if self._use_cloudflare and self._http_client:
            try:
                response = await self._http_client.get(
                    f"{self._cf_base_url}/values/{key}"
                )
                if response.status_code == 200:
                    return response.text
                elif response.status_code == 404:
                    return None
                else:
                    logger.warning(
                        f"Cloudflare KV get failed with status {response.status_code}"
                    )
                    self._use_cloudflare = False
            except Exception as e:
                logger.warning(
                    f"Cloudflare KV get failed, falling back to in-memory: {e}"
                )
                self._use_cloudflare = False

        # Fallback to in-memory cache
        entry = self._cache.get(key)
        if not entry:
            return None

        if entry["expires_at"] <= datetime.utcnow():
            # Entry expired, remove it
            del self._cache[key]
            return None

        return entry["value"]

    async def set(self, key: str, value: str, ttl: int = 3600) -> None:
        """
        Set a value in the cache.

        Args:
            key: Cache key
            value: Value to cache (as string)
            ttl: Time to live in seconds (default: 1 hour)
        """
        if self._use_cloudflare and self._http_client:
            try:
                # Cloudflare KV PUT with TTL
                params = {"expiration_ttl": ttl} if ttl > 0 else {}
                response = await self._http_client.put(
                    f"{self._cf_base_url}/values/{key}", content=value, params=params
                )
                if response.status_code in [200, 201]:
                    return
                else:
                    logger.warning(
                        f"Cloudflare KV set failed with status {response.status_code}"
                    )
                    self._use_cloudflare = False
            except Exception as e:
                logger.warning(
                    f"Cloudflare KV set failed, falling back to in-memory: {e}"
                )
                self._use_cloudflare = False

        # Fallback to in-memory cache
        expires_at = datetime.utcnow() + timedelta(seconds=ttl)
        self._cache[key] = {
            "value": value,
            "expires_at": expires_at,
            "created_at": datetime.utcnow(),
        }

    async def delete(self, key: str) -> bool:
        """
        Delete a value from the cache.

        Args:
            key: Cache key

        Returns:
            True if key was found and deleted, False otherwise
        """
        if key in self._cache:
            del self._cache[key]
            return True
        return False

    async def clear(self) -> None:
        """Clear all cache entries."""
        self._cache.clear()

    def size(self) -> int:
        """Get the number of entries in the cache."""
        return len(self._cache)

    def stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        now = datetime.utcnow()
        expired_count = sum(
            1 for entry in self._cache.values() if entry["expires_at"] <= now
        )

        return {
            "total_entries": len(self._cache),
            "expired_entries": expired_count,
            "active_entries": len(self._cache) - expired_count,
            "cleanup_task_running": self._cleanup_task
            and not self._cleanup_task.done(),
        }


# Global cache service instance
_cache_service: Optional[CacheService] = None


def get_cache_service() -> CacheService:
    """Get the global cache service instance."""
    global _cache_service
    if _cache_service is None:
        _cache_service = CacheService()
    return _cache_service
