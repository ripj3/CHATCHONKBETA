#!/usr/bin/env python3
"""
Diagnose RLS Policy Issues - Find Multiple Permissive Policies

This script connects to both CHCH3 and MSWAP databases to identify
tables with multiple permissive RLS policies that cause conflicts.

Usage:
    python diagnose_rls_issues.py

Author: Rip Jonesy
"""

import asyncio
import logging
import sys
from pathlib import Path

from app.services.database_service import get_database_service
from app.core.config import get_settings

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def diagnose_chch3_policies():
    """Diagnose RLS policy issues in CHCH3 database."""
    logger.info("🔍 Diagnosing CHCH3 RLS policies...")
    
    try:
        db_service = get_database_service()
        
        # Query to find tables with multiple permissive policies
        query = """
        SELECT 
            tablename,
            COUNT(*) as total_policies,
            COUNT(CASE WHEN permissive = 'PERMISSIVE' THEN 1 END) as permissive_policies,
            string_agg(policyname, ', ') as policy_names
        FROM pg_policies 
        WHERE schemaname = 'public'
        GROUP BY tablename
        HAVING COUNT(CASE WHEN permissive = 'PERMISSIVE' THEN 1 END) > 1
        ORDER BY permissive_policies DESC;
        """
        
        results = await db_service.execute_chch3_raw_query(query)
        
        if results:
            logger.error(f"❌ CHCH3 has {len(results)} tables with multiple permissive policies:")
            for row in results:
                logger.error(f"   📋 {row['tablename']}: {row['permissive_policies']} permissive policies")
                logger.error(f"      Policies: {row['policy_names']}")
        else:
            logger.info("✅ CHCH3 has no tables with multiple permissive policies")
        
        return len(results) == 0
        
    except Exception as e:
        logger.error(f"❌ Failed to diagnose CHCH3 policies: {e}")
        return False


async def diagnose_mswap_policies():
    """Diagnose RLS policy issues in MSWAP database."""
    logger.info("🔍 Diagnosing MSWAP RLS policies...")
    
    try:
        db_service = get_database_service()
        
        # Query to find tables with multiple permissive policies
        query = """
        SELECT 
            tablename,
            COUNT(*) as total_policies,
            COUNT(CASE WHEN permissive = 'PERMISSIVE' THEN 1 END) as permissive_policies,
            string_agg(policyname, ', ') as policy_names
        FROM pg_policies 
        WHERE schemaname = 'public'
        GROUP BY tablename
        HAVING COUNT(CASE WHEN permissive = 'PERMISSIVE' THEN 1 END) > 1
        ORDER BY permissive_policies DESC;
        """
        
        results = await db_service.execute_mswap_raw_query(query)
        
        if results:
            logger.error(f"❌ MSWAP has {len(results)} tables with multiple permissive policies:")
            for row in results:
                logger.error(f"   📋 {row['tablename']}: {row['permissive_policies']} permissive policies")
                logger.error(f"      Policies: {row['policy_names']}")
        else:
            logger.info("✅ MSWAP has no tables with multiple permissive policies")
        
        return len(results) == 0
        
    except Exception as e:
        logger.error(f"❌ Failed to diagnose MSWAP policies: {e}")
        return False


async def list_all_policies():
    """List all RLS policies for both databases."""
    logger.info("📋 Listing all RLS policies...")
    
    try:
        db_service = get_database_service()
        
        # Query to list all policies
        query = """
        SELECT 
            schemaname,
            tablename,
            policyname,
            permissive,
            roles,
            cmd,
            qual,
            with_check
        FROM pg_policies 
        WHERE schemaname = 'public'
        ORDER BY tablename, policyname;
        """
        
        logger.info("📋 CHCH3 Policies:")
        chch3_results = await db_service.execute_chch3_raw_query(query)
        for row in chch3_results:
            logger.info(f"   {row['tablename']}.{row['policyname']} ({row['permissive']}) - {row['cmd']}")
        
        logger.info("📋 MSWAP Policies:")
        mswap_results = await db_service.execute_mswap_raw_query(query)
        for row in mswap_results:
            logger.info(f"   {row['tablename']}.{row['policyname']} ({row['permissive']}) - {row['cmd']}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to list policies: {e}")
        return False


async def suggest_fixes():
    """Suggest fixes for common RLS policy issues."""
    logger.info("💡 Suggested fixes:")
    
    print("""
🔧 QUICK FIXES FOR MULTIPLE PERMISSIVE POLICIES:

1. **Run the SQL fix script:**
   - Open Supabase SQL Editor
   - Run the queries in 'fix_rls_policies.sql'
   - This will consolidate multiple policies into single policies

2. **For CHCH3 tables (profiles, files, processing_jobs):**
   - Each table should have ONE policy: users can access their own data
   - Policy pattern: USING (auth.uid() = user_id)

3. **For MSWAP tables (providers, models, task_types):**
   - System tables: service_role access only
   - User tables: user + service_role access

4. **Quick temporary fix (NOT for production):**
   - Disable RLS temporarily: ALTER TABLE tablename DISABLE ROW LEVEL SECURITY;
   - Test your app, then re-enable with proper policies

5. **Verify the fix:**
   - Run this script again to check for remaining issues
   - Test database connections with: python test_database_connections.py

📝 The 'fix_rls_policies.sql' file contains all the SQL commands needed.
""")


async def main():
    """Run RLS policy diagnosis."""
    logger.info("🚀 Starting RLS Policy Diagnosis")
    logger.info("=" * 60)
    
    # Test environment variables
    settings = get_settings()
    if not settings.SUPABASE_URL or not settings.MSWAP_SUPABASE_URL:
        logger.error("❌ Database URLs not configured properly")
        return False
    
    # Diagnose both databases
    chch3_ok = await diagnose_chch3_policies()
    logger.info("-" * 30)
    
    mswap_ok = await diagnose_mswap_policies()
    logger.info("-" * 30)
    
    # List all policies for reference
    await list_all_policies()
    logger.info("-" * 30)
    
    # Provide suggestions
    await suggest_fixes()
    
    logger.info("=" * 60)
    
    if chch3_ok and mswap_ok:
        logger.info("🎉 No RLS policy conflicts found! Your databases are ready.")
        return True
    else:
        logger.error("❌ RLS policy conflicts detected. Please run the fix script.")
        logger.error("📝 Use the SQL commands in 'fix_rls_policies.sql' to resolve these issues.")
        return False


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("Diagnosis interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)
