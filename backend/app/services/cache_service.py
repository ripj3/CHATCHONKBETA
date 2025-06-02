"""
Cache Service - Simple In-Memory Cache for AutoModel

This service provides basic caching functionality for the AutoModel system.
In production, this could be replaced with Redis or another distributed cache.

Author: Rip Jonesy
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

logger = logging.getLogger("chatchonk.cache")


class CacheService:
    """Simple in-memory cache service."""
    
    def __init__(self):
        """Initialize the cache service."""
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._cleanup_task: Optional[asyncio.Task] = None
        self._start_cleanup_task()
    
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
                    logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")
                
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
        expires_at = datetime.utcnow() + timedelta(seconds=ttl)
        self._cache[key] = {
            "value": value,
            "expires_at": expires_at,
            "created_at": datetime.utcnow()
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
            1 for entry in self._cache.values()
            if entry["expires_at"] <= now
        )
        
        return {
            "total_entries": len(self._cache),
            "expired_entries": expired_count,
            "active_entries": len(self._cache) - expired_count,
            "cleanup_task_running": self._cleanup_task and not self._cleanup_task.done()
        }


# Global cache service instance
_cache_service: Optional[CacheService] = None


def get_cache_service() -> CacheService:
    """Get the global cache service instance."""
    global _cache_service
    if _cache_service is None:
        _cache_service = CacheService()
    return _cache_service
