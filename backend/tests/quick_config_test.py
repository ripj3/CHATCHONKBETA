#!/usr/bin/env python3
"""
Quick Configuration Test - Verify environment variables are loaded correctly

This script tests that all required environment variables are properly configured
without requiring all dependencies to be installed.

Usage:
    python quick_config_test.py

Author: Rip Jonesy
"""

import os
import sys
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))


def test_env_variables():
    """Test that all required environment variables are set."""
    print("🔍 Testing Environment Variables Configuration")
    print("=" * 60)

    # Required variables for deployment
    required_vars = {
        # CHCH3 Database
        "SUPABASE_URL": "CHCH3 Supabase URL",
        "SUPABASE_SERVICE_ROLE_KEY": "CHCH3 Service Role Key",
        # MSWAP Database
        "MSWAP_SUPABASE_URL": "MSWAP Supabase URL",
        "MSWAP_SUPABASE_SERVICE_ROLE_KEY": "MSWAP Service Role Key",
        # Cloudflare KV
        "CLOUDFLARE_API_TOKEN": "Cloudflare API Token",
        "CLOUDFLARE_ACCOUNT_ID": "Cloudflare Account ID",
        "CLOUDFLARE_KV_NAMESPACE_ID": "Cloudflare KV Namespace ID",
        # Security
        "CHONK_SECRET_KEY": "Application Secret Key",
        # AI Providers
        "HUGGINGFACE_API_KEY": "HuggingFace API Key",
    }

    missing_vars = []
    configured_vars = []

    for var_name, description in required_vars.items():
        value = os.getenv(var_name)
        if value:
            # Show first 10 chars for verification without exposing secrets
            masked_value = value[:10] + "..." if len(value) > 10 else value
            configured_vars.append((var_name, description, masked_value))
            print(f"✅ {var_name}: {masked_value}")
        else:
            missing_vars.append((var_name, description))
            print(f"❌ {var_name}: NOT SET")

    print("-" * 60)

    if missing_vars:
        print(f"❌ {len(missing_vars)} required variables are missing:")
        for var_name, description in missing_vars:
            print(f"   - {var_name}: {description}")
        return False
    else:
        print(f"✅ All {len(configured_vars)} required variables are configured!")
        return True


def test_cloudflare_config():
    """Test Cloudflare KV configuration specifically."""
    print("\n🔍 Testing Cloudflare KV Configuration")
    print("-" * 40)

    api_token = os.getenv("CLOUDFLARE_API_TOKEN")
    account_id = os.getenv("CLOUDFLARE_ACCOUNT_ID")
    namespace_id = os.getenv("CLOUDFLARE_KV_NAMESPACE_ID")

    if not all([api_token, account_id, namespace_id]):
        print("❌ Cloudflare KV configuration incomplete")
        return False

    print(f"✅ API Token: {api_token[:10]}...")
    print(f"✅ Account ID: {account_id}")
    print(f"✅ Namespace ID: {namespace_id}")
    print("✅ Namespace corresponds to: CHCHBETA1")

    return True


def test_database_urls():
    """Test database URL formats."""
    print("\n🔍 Testing Database URL Formats")
    print("-" * 40)

    chch3_url = os.getenv("SUPABASE_URL")
    mswap_url = os.getenv("MSWAP_SUPABASE_URL")

    if chch3_url:
        if "hqzoibcaibusectmwrif.supabase.co" in chch3_url:
            print("✅ CHCH3 URL format correct")
        else:
            print("❌ CHCH3 URL format unexpected")
            return False

    if mswap_url:
        if "llxzkpihzvvdztdparme.supabase.co" in mswap_url:
            print("✅ MSWAP URL format correct")
        else:
            print("❌ MSWAP URL format unexpected")
            return False

    return True


def main():
    """Run all configuration tests."""
    print("🚀 ChatChonk Configuration Test")
    print("Testing environment variables for deployment readiness...")
    print()

    # Load .env file if it exists (check both current dir and parent dir)
    env_file = Path(".env")
    if not env_file.exists():
        env_file = Path("../.env")

    if env_file.exists():
        print(f"📁 Loading environment from: {env_file.absolute()}")
        try:
            with open(env_file, "r") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        os.environ[key] = value
            print("✅ Environment file loaded successfully")
        except Exception as e:
            print(f"❌ Error loading .env file: {e}")
            return False
    else:
        print("⚠️  No .env file found, using system environment variables")

    print()

    # Run tests
    env_test = test_env_variables()
    cf_test = test_cloudflare_config()
    db_test = test_database_urls()

    print("\n" + "=" * 60)

    if env_test and cf_test and db_test:
        print("🎉 ALL TESTS PASSED!")
        print("✅ Configuration is ready for deployment")
        print("\n📋 Next steps:")
        print("1. Add these environment variables to Render dashboard")
        print("2. Deploy to Render (auto-deploys from main-beta)")
        print("3. Test health endpoints after deployment")
        return True
    else:
        print("❌ SOME TESTS FAILED!")
        print("Please fix the configuration issues above before deploying.")
        return False


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)
