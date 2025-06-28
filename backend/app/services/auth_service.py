from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from supabase import Client, create_client

from backend.app.core.config import settings
from backend.app.services.database_service import supabase

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def get_current_user(token: str = Depends(oauth2_scheme)):
    """
    Dependency to get the current authenticated user from a Supabase JWT.

    Args:
        token: The JWT token from the Authorization header.

    Returns:
        The user object extracted from the token.

    Raises:
        HTTPException: If the token is invalid or expired.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # Use Supabase client to get the user from the token
        user_response = await supabase.auth.get_user(token)
        user = user_response.user
        if user is None:
            raise credentials_exception
        return user
    except Exception:
        # Catch any exception during token validation (e.g., invalid token, network issues)
        raise credentials_exception
