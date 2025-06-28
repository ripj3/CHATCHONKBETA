#!/usr/bin/env python3
"""
Test Database Connections - Verify CHCH3 and MSWAP Supabase connections

This script tests the database connections for both CHCH3 (main) and MSWAP
(ModelSwapper) databases to ensure they're properly configured.

Usage:
    python test_database_connections.py

Author: Rip Jonesy
"""

import asyncio
import logging
import sys
from pathlib import Path

from app.services.database_service import get_database_service
from app.services.modelswapper_service import ModelSwapperService
from app.core.config import get_settings

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def test_chch3_connection():
    """Test CHCH3 (main) database connection."""
    logger.info("Testing CHCH3 database connection...")

    try:
        db_service = get_database_service()

        # Try to query a basic table (profiles should exist in CHCH3)
        results = await db_service.execute_chch3_query("profiles", limit=1)
        logger.info(f"✅ CHCH3 connection successful! Found {len(results)} profile(s)")
        return True

    except Exception as e:
        logger.error(f"❌ CHCH3 connection failed: {e}")
        return False


async def test_mswap_connection():
    """Test MSWAP (ModelSwapper) database connection."""
    logger.info("Testing MSWAP database connection...")

    try:
        db_service = get_database_service()

        # Try to query the providers table
        results = await db_service.execute_mswap_query("providers", limit=1)
        logger.info(f"✅ MSWAP connection successful! Found {len(results)} provider(s)")

        # Test with a simple SELECT query
        raw_results = await db_service.execute_mswap_raw_query(
            "SELECT COUNT(*) as count FROM providers WHERE enabled = true"
        )
        logger.info(f"✅ MSWAP raw query successful! Results: {raw_results}")
        return True

    except Exception as e:
        logger.error(f"❌ MSWAP connection failed: {e}")
        return False


async def test_modelswapper_service():
    """Test ModelSwapper service functionality."""
    logger.info("Testing ModelSwapper service...")

    try:
        service = ModelSwapperService()

        # Test health check
        health = await service.health_check()
        logger.info(f"✅ ModelSwapper health check: {health}")

        # Test getting providers
        providers = await service._get_providers()
        logger.info(f"✅ ModelSwapper found {len(providers)} providers")

        return True

    except Exception as e:
        logger.error(f"❌ ModelSwapper service test failed: {e}")
        return False


async def test_environment_variables():
    """Test that all required environment variables are set."""
    logger.info("Testing environment variables...")

    settings = get_settings()

    # Check CHCH3 configuration
    chch3_ok = True
    if not settings.SUPABASE_URL:
        logger.error("❌ SUPABASE_URL not set")
        chch3_ok = False
    if not settings.SUPABASE_SERVICE_ROLE_KEY:
        logger.error("❌ SUPABASE_SERVICE_ROLE_KEY not set")
        chch3_ok = False

    if chch3_ok:
        logger.info("✅ CHCH3 environment variables configured")

    # Check MSWAP configuration
    mswap_ok = True
    if not settings.MSWAP_SUPABASE_URL:
        logger.error("❌ MSWAP_SUPABASE_URL not set")
        mswap_ok = False
    if not settings.MSWAP_SUPABASE_SERVICE_ROLE_KEY:
        logger.error("❌ MSWAP_SUPABASE_SERVICE_ROLE_KEY not set")
        mswap_ok = False

    if mswap_ok:
        logger.info("✅ MSWAP environment variables configured")

    # Check Redis configuration (optional)
    if settings.REDIS_ENABLED:
        logger.info(f"✅ Redis enabled: {settings.REDIS_HOST}:{settings.REDIS_PORT}")
    else:
        logger.info("ℹ️  Redis not enabled (using in-memory cache)")

    return chch3_ok and mswap_ok


async def main():
    """Run all database connection tests."""
    logger.info("🚀 Starting ChatChonk Database Connection Tests")
    logger.info("=" * 60)

    # Test environment variables first
    env_ok = await test_environment_variables()

    if not env_ok:
        logger.error("❌ Environment variables not properly configured")
        logger.error(
            "Please check your .env file and ensure all required variables are set"
        )
        return False

    logger.info("-" * 60)

    # Test database connections
    chch3_ok = await test_chch3_connection()
    logger.info("-" * 30)

    mswap_ok = await test_mswap_connection()
    logger.info("-" * 30)

    # Test ModelSwapper service
    service_ok = await test_modelswapper_service()

    logger.info("=" * 60)

    # Summary
    all_ok = chch3_ok and mswap_ok and service_ok

    if all_ok:
        logger.info("🎉 All tests passed! Database connections are working correctly.")
        logger.info("✅ Ready for deployment to Render!")
    else:
        logger.error("❌ Some tests failed. Please fix the issues before deploying.")

        if not chch3_ok:
            logger.error("   - CHCH3 database connection issues")
        if not mswap_ok:
            logger.error("   - MSWAP database connection issues")
        if not service_ok:
            logger.error("   - ModelSwapper service issues")

    return all_ok


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)
