"""
Rate Limiting Utilities

This module provides a simple in-memory rate limiter for FastAPI endpoints.
It is designed to be a lightweight dependency that can be used to protect
against denial-of-service attacks and API abuse.

Author: Rip Jonesy
"""

import time
from collections import defaultdict
from typing import Dict, Tuple

from fastapi import Request, HTTPException, status

# In-memory storage for rate limiting
# Format: {user_id: (last_request_time, request_count)}
rate_limit_storage: Dict[str, Tuple[float, int]] = defaultdict(lambda: (0.0, 0))

async def rate_limiter(
    request: Request,
    user_id: str,
    limit: int = 100,
    window: int = 60  # in seconds
):
    """
    A simple in-memory rate limiter.

    Args:
        request: The incoming request.
        user_id: The ID of the user making the request.
        limit: The maximum number of requests allowed in the window.
        window: The time window in seconds.

    Raises:
        HTTPException: If the user has exceeded the rate limit.
    """
    last_time, count = rate_limit_storage[user_id]
    current_time = time.time()

    if current_time - last_time > window:
        # Reset the counter if the window has passed
        rate_limit_storage[user_id] = (current_time, 1)
    else:
        if count >= limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Too many requests. Please try again in {int(window - (current_time - last_time))} seconds."
            )
        rate_limit_storage[user_id] = (last_time, count + 1)
