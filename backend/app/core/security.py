"""
Core Security Utilities - JWT Validation and User Authentication

This module handles the critical task of validating JWTs issued by Supabase, 
ensuring that API requests are properly authenticated and authorized.

Author: Rip Jonesy
"""

import logging
from typing import Any, Dict, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.config import settings
from app.services.supabase_client import supabase_client  # Assuming you have a Supabase client service

logger = logging.getLogger("chatchonk.core.security")
security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> Dict[str, Any]:
    """
    Validates the JWT token from the Authorization header and returns the user session.

    This function is a FastAPI dependency that can be used to protect API endpoints.

    Args:
        credentials: The HTTP Authorization credentials (Bearer token).

    Returns:
        The user session object from Supabase if the token is valid.

    Raises:
        HTTPException: If the token is invalid, expired, or not provided.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Bearer token not provided",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    try:
        # Verify the token using the Supabase client
        session = supabase_client.auth.get_user(token)

        if not session or not session.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Convert user session to a dictionary for easier use
        user_data = session.user.dict()
        logger.debug(f"Successfully authenticated user: {user_data.get('email')}")
        return user_data

    except Exception as e:
        logger.error(f"JWT validation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
