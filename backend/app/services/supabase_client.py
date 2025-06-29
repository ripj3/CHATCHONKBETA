"""
Supabase Client Service

This module initializes and provides a singleton instance of the Supabase client
for interacting with the Supabase backend (database, auth, storage).

It uses the application's core settings to configure the client.

Author: Rip Jonesy
"""

import logging
from supabase import create_client, Client

from app.core.config import settings

logger = logging.getLogger("chatchonk.services.supabase")

def create_supabase_client() -> Client:
    """
    Initializes the Supabase client using credentials from the application settings.

    This function is called once at startup to create a singleton client instance.

    Returns:
        An initialized Supabase client instance.

    Raises:
        ValueError: If Supabase URL or service key is not configured.
    """
    if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_ROLE_KEY:
        logger.error("Supabase URL or Service Role Key is not configured.")
        raise ValueError("Supabase credentials must be set in environment variables.")

    try:
        client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)
        logger.info("Supabase client initialized successfully.")
        return client
    except Exception as e:
        logger.critical(f"Failed to initialize Supabase client: {e}", exc_info=True)
        raise

# Create a singleton instance of the Supabase client
supabase_client: Client = create_supabase_client()
