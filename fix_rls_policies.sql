-- Fix Multiple Permissive Policies Issue in Supabase
-- This script helps diagnose and fix RLS policy conflicts

-- =====================================================================
-- STEP 1: DIAGNOSE THE ISSUE
-- =====================================================================

-- Check all RLS policies on all tables
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

-- Count policies per table to identify tables with multiple permissive policies
SELECT 
    tablename,
    COUNT(*) as policy_count,
    COUNT(CASE WHEN permissive = 'PERMISSIVE' THEN 1 END) as permissive_count
FROM pg_policies 
WHERE schemaname = 'public'
GROUP BY tablename
HAVING COUNT(CASE WHEN permissive = 'PERMISSIVE' THEN 1 END) > 1
ORDER BY permissive_count DESC;

-- =====================================================================
-- STEP 2: FIX COMMON TABLES (CHCH3 Database)
-- =====================================================================

-- Fix profiles table
DROP POLICY IF EXISTS "Users can view own profile" ON profiles;
DROP POLICY IF EXISTS "Users can update own profile" ON profiles;
DROP POLICY IF EXISTS "Enable read access for all users" ON profiles;
DROP POLICY IF EXISTS "Enable insert for authenticated users only" ON profiles;
DROP POLICY IF EXISTS "Enable update for users based on email" ON profiles;

-- Create single, clear policy for profiles
CREATE POLICY "profiles_policy" ON profiles
    FOR ALL 
    USING (auth.uid() = id)
    WITH CHECK (auth.uid() = id);

-- Fix files table
DROP POLICY IF EXISTS "Users can view own files" ON files;
DROP POLICY IF EXISTS "Users can insert own files" ON files;
DROP POLICY IF EXISTS "Users can update own files" ON files;
DROP POLICY IF EXISTS "Users can delete own files" ON files;
DROP POLICY IF EXISTS "Enable read access for all users" ON files;
DROP POLICY IF EXISTS "Enable insert for authenticated users only" ON files;

-- Create single policy for files
CREATE POLICY "files_policy" ON files
    FOR ALL 
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

-- Fix processing_jobs table
DROP POLICY IF EXISTS "Users can view own jobs" ON processing_jobs;
DROP POLICY IF EXISTS "Users can insert own jobs" ON processing_jobs;
DROP POLICY IF EXISTS "Users can update own jobs" ON processing_jobs;
DROP POLICY IF EXISTS "Enable read access for all users" ON processing_jobs;
DROP POLICY IF EXISTS "Enable insert for authenticated users only" ON processing_jobs;

-- Create single policy for processing_jobs
CREATE POLICY "processing_jobs_policy" ON processing_jobs
    FOR ALL 
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

-- =====================================================================
-- STEP 3: FIX MSWAP TABLES (ModelSwapper Database)
-- =====================================================================

-- Fix providers table (system-managed, service role access)
DROP POLICY IF EXISTS "Enable read access for all users" ON providers;
DROP POLICY IF EXISTS "Enable insert for authenticated users only" ON providers;
DROP POLICY IF EXISTS "Enable update for authenticated users only" ON providers;
DROP POLICY IF EXISTS "Service role full access" ON providers;

-- Create service role only policy for providers
CREATE POLICY "providers_service_role_policy" ON providers
    FOR ALL 
    USING (auth.role() = 'service_role')
    WITH CHECK (auth.role() = 'service_role');

-- Fix models table
DROP POLICY IF EXISTS "Enable read access for all users" ON models;
DROP POLICY IF EXISTS "Enable insert for authenticated users only" ON models;
DROP POLICY IF EXISTS "Service role full access" ON models;

-- Create service role only policy for models
CREATE POLICY "models_service_role_policy" ON models
    FOR ALL 
    USING (auth.role() = 'service_role')
    WITH CHECK (auth.role() = 'service_role');

-- Fix task_types table
DROP POLICY IF EXISTS "Enable read access for all users" ON task_types;
DROP POLICY IF EXISTS "Enable insert for authenticated users only" ON task_types;
DROP POLICY IF EXISTS "Service role full access" ON task_types;

-- Create service role only policy for task_types
CREATE POLICY "task_types_service_role_policy" ON task_types
    FOR ALL 
    USING (auth.role() = 'service_role')
    WITH CHECK (auth.role() = 'service_role');

-- Fix user_providers table (user-specific)
DROP POLICY IF EXISTS "Users can view own providers" ON user_providers;
DROP POLICY IF EXISTS "Users can insert own providers" ON user_providers;
DROP POLICY IF EXISTS "Users can update own providers" ON user_providers;
DROP POLICY IF EXISTS "Enable read access for all users" ON user_providers;
DROP POLICY IF EXISTS "Enable insert for authenticated users only" ON user_providers;

-- Create user-specific policy for user_providers
CREATE POLICY "user_providers_policy" ON user_providers
    FOR ALL 
    USING (auth.uid() = user_id OR auth.role() = 'service_role')
    WITH CHECK (auth.uid() = user_id OR auth.role() = 'service_role');

-- Fix usage_logs table (user-specific + service role)
DROP POLICY IF EXISTS "Users can view own usage" ON usage_logs;
DROP POLICY IF EXISTS "Service role can insert usage" ON usage_logs;
DROP POLICY IF EXISTS "Enable read access for all users" ON usage_logs;
DROP POLICY IF EXISTS "Enable insert for authenticated users only" ON usage_logs;

-- Create combined policy for usage_logs
CREATE POLICY "usage_logs_policy" ON usage_logs
    FOR ALL 
    USING (auth.uid() = user_id OR auth.role() = 'service_role')
    WITH CHECK (auth.uid() = user_id OR auth.role() = 'service_role');

-- =====================================================================
-- STEP 4: VERIFY THE FIX
-- =====================================================================

-- Check that each table now has only one policy
SELECT 
    tablename,
    COUNT(*) as policy_count,
    string_agg(policyname, ', ') as policy_names
FROM pg_policies 
WHERE schemaname = 'public'
GROUP BY tablename
ORDER BY tablename;

-- Verify no tables have multiple permissive policies
SELECT 
    tablename,
    COUNT(CASE WHEN permissive = 'PERMISSIVE' THEN 1 END) as permissive_count
FROM pg_policies 
WHERE schemaname = 'public'
GROUP BY tablename
HAVING COUNT(CASE WHEN permissive = 'PERMISSIVE' THEN 1 END) > 1;

-- =====================================================================
-- STEP 5: ALTERNATIVE - DISABLE RLS TEMPORARILY (NOT RECOMMENDED)
-- =====================================================================

-- ONLY USE THIS IF YOU NEED TO QUICKLY TEST WITHOUT RLS
-- WARNING: This removes all security - only for development/testing

-- ALTER TABLE profiles DISABLE ROW LEVEL SECURITY;
-- ALTER TABLE files DISABLE ROW LEVEL SECURITY;
-- ALTER TABLE processing_jobs DISABLE ROW LEVEL SECURITY;
-- ALTER TABLE providers DISABLE ROW LEVEL SECURITY;
-- ALTER TABLE models DISABLE ROW LEVEL SECURITY;
-- ALTER TABLE task_types DISABLE ROW LEVEL SECURITY;
-- ALTER TABLE user_providers DISABLE ROW LEVEL SECURITY;
-- ALTER TABLE usage_logs DISABLE ROW LEVEL SECURITY;

-- =====================================================================
-- STEP 6: RE-ENABLE RLS WITH CLEAN POLICIES (RECOMMENDED)
-- =====================================================================

-- Ensure RLS is enabled on all tables
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE files ENABLE ROW LEVEL SECURITY;
ALTER TABLE processing_jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE providers ENABLE ROW LEVEL SECURITY;
ALTER TABLE models ENABLE ROW LEVEL SECURITY;
ALTER TABLE task_types ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_providers ENABLE ROW LEVEL SECURITY;
ALTER TABLE usage_logs ENABLE ROW LEVEL SECURITY;

-- Grant necessary permissions to service role
GRANT ALL ON ALL TABLES IN SCHEMA public TO service_role;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO service_role;
GRANT ALL ON ALL FUNCTIONS IN SCHEMA public TO service_role;

-- Grant read access to anon role for public data
GRANT SELECT ON providers TO anon;
GRANT SELECT ON models TO anon;
GRANT SELECT ON task_types TO anon;

-- =====================================================================
-- NOTES:
-- =====================================================================
-- 1. Run STEP 1 first to see which tables have multiple policies
-- 2. Run STEP 2 and 3 to fix the policies
-- 3. Run STEP 4 to verify the fix worked
-- 4. If you still have issues, you can temporarily use STEP 5
-- 5. Always re-enable RLS with STEP 6 for production

-- This script should resolve the "multiple_permissive_policies" error
-- by ensuring each table has only one clear, comprehensive policy.
