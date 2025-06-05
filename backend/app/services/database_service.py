"""
Database Service - Supabase Connection Management for ChatChonk

This service manages connections to both CHCH3 (main) and MSWAP (ModelSwapper) 
Supabase databases with proper error handling and connection pooling.

Author: Rip Jonesy
"""

import logging
from typing import Any, Dict, List, Optional, Union
from supabase import create_client, Client
from app.core.config import get_settings

logger = logging.getLogger("chatchonk.database")


class DatabaseService:
    """Manages Supabase database connections for ChatChonk."""
    
    def __init__(self):
        """Initialize database connections."""
        self.settings = get_settings()
        self._chch3_client: Optional[Client] = None
        self._mswap_client: Optional[Client] = None
        
    @property
    def chch3_client(self) -> Client:
        """Get or create CHCH3 (main) database client."""
        if self._chch3_client is None:
            if not self.settings.SUPABASE_URL or not self.settings.SUPABASE_SERVICE_ROLE_KEY:
                raise ValueError("CHCH3 Supabase configuration missing: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY required")
            
            self._chch3_client = create_client(
                str(self.settings.SUPABASE_URL),
                self.settings.SUPABASE_SERVICE_ROLE_KEY.get_secret_value()
            )
            logger.info("CHCH3 Supabase client initialized")
        
        return self._chch3_client
    
    @property
    def mswap_client(self) -> Client:
        """Get or create MSWAP (ModelSwapper) database client."""
        if self._mswap_client is None:
            if not self.settings.MSWAP_SUPABASE_URL or not self.settings.MSWAP_SUPABASE_SERVICE_ROLE_KEY:
                raise ValueError("MSWAP Supabase configuration missing: MSWAP_SUPABASE_URL and MSWAP_SUPABASE_SERVICE_ROLE_KEY required")
            
            self._mswap_client = create_client(
                str(self.settings.MSWAP_SUPABASE_URL),
                self.settings.MSWAP_SUPABASE_SERVICE_ROLE_KEY.get_secret_value()
            )
            logger.info("MSWAP Supabase client initialized")
        
        return self._mswap_client
    
    async def execute_chch3_query(self, table: str, operation: str = "select", **kwargs) -> List[Dict[str, Any]]:
        """
        Execute a query on the CHCH3 database.
        
        Args:
            table: Table name to query
            operation: Operation type (select, insert, update, delete)
            **kwargs: Additional parameters for the query
            
        Returns:
            Query results as list of dictionaries
        """
        try:
            client = self.chch3_client
            
            if operation == "select":
                query = client.table(table).select(kwargs.get("columns", "*"))
                
                # Add filters if provided
                if "filters" in kwargs:
                    for filter_item in kwargs["filters"]:
                        query = query.eq(filter_item["column"], filter_item["value"])
                
                # Add ordering if provided
                if "order" in kwargs:
                    query = query.order(kwargs["order"])
                
                # Add limit if provided
                if "limit" in kwargs:
                    query = query.limit(kwargs["limit"])
                
                response = query.execute()
                return response.data
                
            elif operation == "insert":
                response = client.table(table).insert(kwargs.get("data", {})).execute()
                return response.data
                
            elif operation == "update":
                query = client.table(table).update(kwargs.get("data", {}))
                
                # Add filters for update
                if "filters" in kwargs:
                    for filter_item in kwargs["filters"]:
                        query = query.eq(filter_item["column"], filter_item["value"])
                
                response = query.execute()
                return response.data
                
            elif operation == "delete":
                query = client.table(table)
                
                # Add filters for delete
                if "filters" in kwargs:
                    for filter_item in kwargs["filters"]:
                        query = query.eq(filter_item["column"], filter_item["value"])
                
                response = query.delete().execute()
                return response.data
                
            else:
                raise ValueError(f"Unsupported operation: {operation}")
                
        except Exception as e:
            logger.error(f"CHCH3 database error in {operation} on {table}: {e}")
            raise
    
    async def execute_mswap_query(self, table: str, operation: str = "select", **kwargs) -> List[Dict[str, Any]]:
        """
        Execute a query on the MSWAP database.
        
        Args:
            table: Table name to query
            operation: Operation type (select, insert, update, delete)
            **kwargs: Additional parameters for the query
            
        Returns:
            Query results as list of dictionaries
        """
        try:
            client = self.mswap_client
            
            if operation == "select":
                query = client.table(table).select(kwargs.get("columns", "*"))
                
                # Add filters if provided
                if "filters" in kwargs:
                    for filter_item in kwargs["filters"]:
                        query = query.eq(filter_item["column"], filter_item["value"])
                
                # Add ordering if provided
                if "order" in kwargs:
                    query = query.order(kwargs["order"])
                
                # Add limit if provided
                if "limit" in kwargs:
                    query = query.limit(kwargs["limit"])
                
                response = query.execute()
                return response.data
                
            elif operation == "insert":
                response = client.table(table).insert(kwargs.get("data", {})).execute()
                return response.data
                
            elif operation == "update":
                query = client.table(table).update(kwargs.get("data", {}))
                
                # Add filters for update
                if "filters" in kwargs:
                    for filter_item in kwargs["filters"]:
                        query = query.eq(filter_item["column"], filter_item["value"])
                
                response = query.execute()
                return response.data
                
            elif operation == "delete":
                query = client.table(table)
                
                # Add filters for delete
                if "filters" in kwargs:
                    for filter_item in kwargs["filters"]:
                        query = query.eq(filter_item["column"], filter_item["value"])
                
                response = query.delete().execute()
                return response.data
                
            else:
                raise ValueError(f"Unsupported operation: {operation}")
                
        except Exception as e:
            logger.error(f"MSWAP database error in {operation} on {table}: {e}")
            raise
    
    async def execute_mswap_raw_query(self, query: str, params: Optional[List] = None) -> List[Dict[str, Any]]:
        """
        Execute a raw SQL query on the MSWAP database.

        Args:
            query: SQL query string
            params: Optional parameters for the query

        Returns:
            Query results as list of dictionaries
        """
        try:
            logger.debug(f"Executing MSWAP raw query: {query} with params: {params}")

            # Parse the SQL query and convert to Supabase operations
            if query.strip().upper().startswith("SELECT"):
                return await self._parse_and_execute_select(query, params)
            elif query.strip().upper().startswith("INSERT"):
                return await self._parse_and_execute_insert(query, params)
            elif query.strip().upper().startswith("UPDATE"):
                return await self._parse_and_execute_update(query, params)
            else:
                # For complex queries, try to use Supabase RPC if available
                logger.warning(f"Complex query detected, attempting direct execution: {query}")
                # This would require a custom RPC function in Supabase
                # For now, return empty results
                return []

        except Exception as e:
            logger.error(f"MSWAP raw query error: {e}")
            raise
    
    async def _parse_and_execute_select(self, query: str, params: Optional[List] = None) -> List[Dict[str, Any]]:
        """Parse and execute a SELECT query using Supabase client."""
        try:
            query_lower = query.lower().strip()

            # Extract table name from FROM clause
            from_match = query_lower.find("from ")
            if from_match == -1:
                raise ValueError("No FROM clause found in SELECT query")

            # Get the part after FROM
            from_part = query[from_match + 5:].strip()

            # Extract table name (handle WHERE, ORDER BY, etc.)
            table_name_select = from_part.split()[0].strip()

            # Start building the Supabase query
            supabase_query = self.mswap_client.table(table_name_select).select("*")

            # Handle WHERE conditions
            if "where " in query_lower:
                where_index = query_lower.find("where ") + 6
                where_part = query[where_index:].strip()

                # Handle simple WHERE conditions
                if "enabled = true" in where_part.lower():
                    supabase_query = supabase_query.eq("enabled", True)
                elif "enabled = false" in where_part.lower():
                    supabase_query = supabase_query.eq("enabled", False)

                # Handle parameterized queries with %s
                if params and "%s" in where_part:
                    # Simple parameter substitution for common patterns
                    if "id = %s" in where_part.lower():
                        supabase_query = supabase_query.eq("id", params[0])
                    elif "name = %s" in where_part.lower():
                        supabase_query = supabase_query.eq("name", params[0])

            # Handle ORDER BY
            if "order by " in query_lower:
                order_index = query_lower.find("order by ") + 9
                order_part = query[order_index:].strip().split()[0]

                if "desc" in query_lower:
                    supabase_query = supabase_query.order(order_part, desc=True)
                else:
                    supabase_query = supabase_query.order(order_part)

            # Handle LIMIT
            if "limit " in query_lower:
                limit_index = query_lower.find("limit ") + 6
                limit_part = query[limit_index:].strip().split()[0]
                try:
                    limit_value = int(limit_part)
                    supabase_query = supabase_query.limit(limit_value)
                except ValueError:
                    pass  # Ignore invalid limit values

            response = supabase_query.execute()
            return response.data

        except Exception as e:
            logger.error(f"Error parsing SELECT query: {e}")
            return []

    async def _parse_and_execute_insert(self, query: str, params: Optional[List] = None) -> List[Dict[str, Any]]:
        """Parse and execute an INSERT query using Supabase client."""
        try:
            query_lower = query.lower().strip()

            # Extract table name
            into_match = query_lower.find("into ")
            if into_match == -1:
                raise ValueError("No INTO clause found in INSERT query")

            into_part = query[into_match + 5:].strip()

            # For now, return empty list as INSERT parsing is complex
            # In production, you'd want to parse the VALUES clause
            logger.warning(f"INSERT query parsing not fully implemented for: {query}")
            return []

        except Exception as e:
            logger.error(f"Error parsing INSERT query: {e}")
            return []

    async def _parse_and_execute_update(self, query: str, params: Optional[List] = None) -> List[Dict[str, Any]]:
        """Parse and execute an UPDATE query using Supabase client."""
        try:
            query_lower = query.lower().strip()

            # Extract table name
            update_match = query_lower.find("update ")
            if update_match == -1:
                raise ValueError("No UPDATE clause found")

            update_part = query[update_match + 7:].strip()

            # For now, return empty list as UPDATE parsing is complex
            logger.warning(f"UPDATE query parsing not fully implemented for: {query}")
            return []

        except Exception as e:
            logger.error(f"Error parsing UPDATE query: {e}")
            return []
    
    async def health_check(self) -> Dict[str, Any]:
        """Check health of both database connections."""
        health_status = {
            "chch3": {"status": "unknown", "error": None},
            "mswap": {"status": "unknown", "error": None}
        }
        
        # Test CHCH3 connection
        try:
            await self.execute_chch3_query("profiles", limit=1)
            health_status["chch3"]["status"] = "healthy"
        except Exception as e:
            health_status["chch3"]["status"] = "unhealthy"
            health_status["chch3"]["error"] = str(e)
        
        # Test MSWAP connection
        try:
            await self.execute_mswap_query("providers", limit=1)
            health_status["mswap"]["status"] = "healthy"
        except Exception as e:
            health_status["mswap"]["status"] = "unhealthy"
            health_status["mswap"]["error"] = str(e)
        
        return health_status


# Global database service instance
_database_service: Optional[DatabaseService] = None


def get_database_service() -> DatabaseService:
    """Get the global database service instance."""
    global _database_service
    if _database_service is None:
        _database_service = DatabaseService()
    return _database_service
