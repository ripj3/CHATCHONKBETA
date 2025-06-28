#!/usr/bin/env python
"""
check_schema.py - List all tables in the Supabase public schema

This script connects to the Supabase instance and lists all tables in the public schema.
It helps identify existing database structures, particularly those related to pricing,
tiers, or subscriptions.
"""

import asyncio
import sys
import os

# Add the project root to the Python path so we can import from backend
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the supabase client from the database service
from backend.app.services.database_service import supabase


async def list_tables():
    """
    Query Supabase to get a list of all tables in the public schema.
    """
    try:
        # Try first with a direct SQL query against information_schema
        response = await supabase.table("information_schema.tables") \
            .select("table_name") \
            .eq("table_schema", "public") \
            .execute()
        
        if response.data:
            print("Tables found in public schema:")
            for idx, table in enumerate(response.data, 1):
                print(f"{idx}. {table['table_name']}")
            
            # Specifically look for pricing/subscription related tables
            pricing_tables = [t['table_name'] for t in response.data 
                             if any(keyword in t['table_name'].lower() 
                                   for keyword in ['price', 'tier', 'subscription', 'payment', 'plan'])]
            
            if pricing_tables:
                print("\nPotential pricing/subscription related tables:")
                for table in pricing_tables:
                    print(f"- {table}")
            else:
                print("\nNo pricing/subscription related tables found.")
        else:
            print("No tables found or insufficient permissions to view schema.")
    
    except Exception as e:
        print(f"Error querying database schema: {e}")
        
        # Fallback to RPC method if available
        try:
            print("Trying alternative method...")
            response = await supabase.rpc('get_tables_in_schema', {'schema_name': 'public'}).execute()
            
            if response.data:
                print("Tables found in public schema:")
                for idx, table in enumerate(response.data, 1):
                    print(f"{idx}. {table['name']}")
            else:
                print("No tables found or insufficient permissions.")
        except Exception as fallback_error:
            print(f"Fallback method also failed: {fallback_error}")
            print("Please check your Supabase permissions and connection.")


if __name__ == "__main__":
    print("Connecting to Supabase and querying schema information...")
    asyncio.run(list_tables())
    print("Done.")
