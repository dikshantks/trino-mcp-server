#!/usr/bin/env python3
"""
Trino MCP Server - Read-only query interface for Trino databases

A Model Context Protocol (MCP) server that provides secure, read-only access
to Trino databases for data engineers and analysts using AI tools.
"""
import os
import sys
import logging
from typing import Optional, Tuple
from datetime import datetime, timezone
import httpx
from mcp.server.fastmcp import FastMCP
import trino
from trino.auth import BasicAuthentication
import pandas as pd
from tabulate import tabulate
import json
import re

# Configure logging
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger("trino-server")

# Initialize MCP server
mcp = FastMCP("trino")

# Configuration from environment variables
TRINO_HOST = os.environ.get("TRINO_HOST", "host.docker.internal")
TRINO_PORT = int(os.environ.get("TRINO_PORT", "8088"))
TRINO_USER = os.environ.get("TRINO_USER", "trino")
TRINO_PASSWORD = os.environ.get("TRINO_PASSWORD")  # Optional
TRINO_USE_HTTPS = os.environ.get("TRINO_USE_HTTPS", "false").lower() == "true"
TRINO_CATALOG = os.environ.get("TRINO_CATALOG", "tpch")
TRINO_SCHEMA = os.environ.get("TRINO_SCHEMA", "tiny")

# === UTILITY FUNCTIONS ===

def format_error_message(error: Exception, context: str = "") -> str:
    """
    Format error messages with helpful troubleshooting information.
    
    Args:
        error: The exception that occurred
        context: Additional context about what was being attempted
        
    Returns:
        Formatted error message with troubleshooting hints
    """
    error_msg = str(error)
    error_type = type(error).__name__
    
    # Connection errors
    if "connection" in error_msg.lower() or "connect" in error_msg.lower():
        return f"""❌ Connection Error: Cannot connect to Trino server

Details: {error_msg}

Troubleshooting:
1. Verify Trino server is running:
   curl http://{TRINO_HOST}:{TRINO_PORT}/v1/info

2. Check environment variables:
   - TRINO_HOST={TRINO_HOST}
   - TRINO_PORT={TRINO_PORT}
   - TRINO_USER={TRINO_USER}

3. For remote servers, ensure SSH tunnel is active (if required)

4. For Docker, verify network configuration:
   - Use 'host.docker.internal' for localhost connections
   - On Linux, add: --add-host=host.docker.internal:host-gateway
   - Check Docker network mode settings

5. Check firewall rules and network connectivity"""
    
    # Authentication errors
    if "authentication" in error_msg.lower() or "unauthorized" in error_msg.lower():
        return f"""❌ Authentication Error: Failed to authenticate with Trino

Details: {error_msg}

Troubleshooting:
1. Verify TRINO_USER is correct: {TRINO_USER}
2. If using password authentication, check TRINO_PASSWORD is set correctly
3. Verify user has read permissions on catalog: {TRINO_CATALOG}
4. Check Trino server authentication configuration"""
    
    # Query errors
    if "syntax" in error_msg.lower() or "parse" in error_msg.lower():
        return f"""❌ Query Error: SQL syntax or parsing error

Details: {error_msg}

Troubleshooting:
1. Check SQL syntax for Trino-specific requirements
2. Verify table/schema/catalog names are correct
3. Ensure proper quoting for identifiers with special characters
4. Check Trino SQL documentation for supported syntax"""
    
    # Generic error
    return f"""❌ Error: {error_type}

Details: {error_msg}

Context: {context if context else 'No additional context'}

For more help, check:
- Trino server logs
- Network connectivity
- Environment variable configuration"""


def get_trino_connection():
    """
    Create a connection to Trino server with optional authentication.
    
    Returns:
        Trino database connection object
        
    Raises:
        Exception: If connection fails, raises with formatted error message
    """
    try:
        # Determine host - use host.docker.internal for localhost in Docker
        host = TRINO_HOST if TRINO_HOST != "localhost" else "host.docker.internal"
        
        # Set up authentication if password is provided
        auth = None
        if TRINO_PASSWORD:
            auth = BasicAuthentication(TRINO_USER, TRINO_PASSWORD)
            logger.debug("Using BasicAuthentication")
        
        # Determine HTTP scheme
        http_scheme = "https" if TRINO_USE_HTTPS else "http"
        
        # Create connection
        conn = trino.dbapi.connect(
            host=host,
            port=TRINO_PORT,
            user=TRINO_USER,
            auth=auth,
            http_scheme=http_scheme,
            catalog=TRINO_CATALOG,
            schema=TRINO_SCHEMA,
        )
        logger.debug(f"Connected to Trino at {http_scheme}://{host}:{TRINO_PORT}")
        return conn
    except Exception as e:
        logger.error(f"Failed to connect to Trino: {e}")
        raise Exception(format_error_message(e, "Connection attempt"))

def validate_query(query: str) -> bool:
    """Validate that query is read-only (SELECT, SHOW, DESCRIBE only)."""
    # Clean up the query - remove comments and normalize whitespace
    query_clean = re.sub(r'--.*$', '', query, flags=re.MULTILINE)  # Remove SQL comments
    query_clean = re.sub(r'/\*.*?\*/', '', query_clean, flags=re.DOTALL)  # Remove multi-line comments
    query_clean = ' '.join(query_clean.split())  # Normalize whitespace
    query_upper = query_clean.upper()
    
    # List of write operations that should be blocked
    # Using word boundaries to avoid false positives
    forbidden_patterns = [
        r'\bINSERT\s+INTO\b',
        r'\bUPDATE\s+\w+\s+SET\b',
        r'\bDELETE\s+FROM\b',
        r'\bCREATE\s+(TABLE|VIEW|SCHEMA|DATABASE)\b',
        r'\bDROP\s+(TABLE|VIEW|SCHEMA|DATABASE)\b',
        r'\bALTER\s+(TABLE|VIEW|SCHEMA|DATABASE)\b',
        r'\bMERGE\s+INTO\b',
        r'\bTRUNCATE\s+TABLE\b',
        r'\bGRANT\s+\w+\s+ON\b',
        r'\bREVOKE\s+\w+\s+ON\b'
    ]
    
    # Check for forbidden patterns
    for pattern in forbidden_patterns:
        if re.search(pattern, query_upper):
            logger.warning(f"Query blocked - matched forbidden pattern: {pattern}")
            return False
    
    # Check if query starts with allowed keywords (after removing whitespace)
    query_trimmed = query_upper.strip()
    allowed_starts = ['SELECT', 'WITH', 'SHOW', 'DESCRIBE', 'DESC', 'EXPLAIN', 'VALUES']
    
    # Also allow parentheses at the start (for CTEs or subqueries)
    if query_trimmed.startswith('('):
        # Look for the first non-parenthesis keyword
        inner_query = re.sub(r'^\s*\(+\s*', '', query_trimmed)
        if not any(inner_query.startswith(keyword) for keyword in allowed_starts):
            logger.warning(f"Query blocked - doesn't start with allowed keyword")
            return False
    elif not any(query_trimmed.startswith(keyword) for keyword in allowed_starts):
        logger.warning(f"Query blocked - doesn't start with allowed keyword")
        return False
    
    logger.debug(f"Query validated successfully")
    return True

def format_results(cursor, limit: int = 100) -> str:
    """
    Format query results as a readable table.
    
    Args:
        cursor: Database cursor with query results
        limit: Maximum number of rows to display
        
    Returns:
        Formatted table string with result count
    """
    try:
        # Get column names
        columns = [col[0] for col in cursor.description] if cursor.description else []
        
        if not columns:
            return "No columns returned"
        
        # Fetch results
        rows = cursor.fetchmany(limit)
        
        if not rows:
            return "No results returned"
        
        # Create DataFrame for better formatting
        df = pd.DataFrame(rows, columns=columns)
        
        # Format as table with column width limits
        table = tabulate(df, headers='keys', tablefmt='grid', showindex=False, maxcolwidths=50)
        
        result_count = len(rows)
        total_msg = f"\n\nShowing {result_count} row(s)"
        if result_count == limit:
            total_msg += f" (limited to {limit} rows)"
        
        return f"{table}{total_msg}"
    except Exception as e:
        logger.error(f"Error formatting results: {e}")
        return f"Error formatting results: {str(e)}"

# === MCP TOOLS ===

@mcp.tool()
async def execute_query(query: str = "") -> str:
    """Execute a read-only SQL query on Trino (SELECT, SHOW, DESCRIBE only)."""
    logger.info(f"Executing query: {query[:100]}...")
    
    if not query.strip():
        return "❌ Error: Query is required"
    
    # Validate query is read-only
    if not validate_query(query):
        return "❌ Error: Only read-only queries are allowed (SELECT, SHOW, DESCRIBE, EXPLAIN, WITH)"
    
    try:
        conn = get_trino_connection()
        cursor = conn.cursor()
        
        cursor.execute(query)
        result = format_results(cursor)
        
        cursor.close()
        conn.close()
        
        return f"✅ Query executed successfully:\n\n{result}"
    except Exception as e:
        logger.error(f"Query execution error: {e}")
        return format_error_message(e, f"Executing query: {query[:100]}...")

@mcp.tool()
async def show_catalogs() -> str:
    """Show all available catalogs in Trino."""
    logger.info("Showing catalogs")
    
    try:
        conn = get_trino_connection()
        cursor = conn.cursor()
        
        cursor.execute("SHOW CATALOGS")
        result = format_results(cursor)
        
        cursor.close()
        conn.close()
        
        return f"✅ Available catalogs:\n\n{result}"
    except Exception as e:
        logger.error(f"Error showing catalogs: {e}")
        return format_error_message(e, "Showing catalogs")

@mcp.tool()
async def show_schemas(catalog: str = "") -> str:
    """Show all schemas in a specific catalog or current catalog."""
    catalog_name = catalog.strip() or TRINO_CATALOG
    logger.info(f"Showing schemas in catalog: {catalog_name}")
    
    try:
        conn = get_trino_connection()
        cursor = conn.cursor()
        
        query = f"SHOW SCHEMAS FROM {catalog_name}" if catalog.strip() else "SHOW SCHEMAS"
        cursor.execute(query)
        result = format_results(cursor)
        
        cursor.close()
        conn.close()
        
        return f"✅ Schemas in {catalog_name}:\n\n{result}"
    except Exception as e:
        logger.error(f"Error showing schemas: {e}")
        return format_error_message(e, f"Showing schemas in catalog: {catalog_name}")

@mcp.tool()
async def show_tables(schema: str = "", catalog: str = "") -> str:
    """Show all tables in a schema."""
    catalog_name = catalog.strip() or TRINO_CATALOG
    schema_name = schema.strip() or TRINO_SCHEMA
    logger.info(f"Showing tables in {catalog_name}.{schema_name}")
    
    try:
        conn = get_trino_connection()
        cursor = conn.cursor()
        
        query = f"SHOW TABLES FROM {catalog_name}.{schema_name}"
        cursor.execute(query)
        result = format_results(cursor)
        
        cursor.close()
        conn.close()
        
        return f"✅ Tables in {catalog_name}.{schema_name}:\n\n{result}"
    except Exception as e:
        logger.error(f"Error showing tables: {e}")
        return format_error_message(e, f"Showing tables in {catalog_name}.{schema_name}")

@mcp.tool()
async def describe_table(table: str = "", schema: str = "", catalog: str = "") -> str:
    """Describe the structure of a table including columns and their types."""
    if not table.strip():
        return "❌ Error: Table name is required"
    
    catalog_name = catalog.strip() or TRINO_CATALOG
    schema_name = schema.strip() or TRINO_SCHEMA
    full_table = f"{catalog_name}.{schema_name}.{table}"
    
    logger.info(f"Describing table: {full_table}")
    
    try:
        conn = get_trino_connection()
        cursor = conn.cursor()
        
        cursor.execute(f"DESCRIBE {full_table}")
        result = format_results(cursor, limit=1000)
        
        cursor.close()
        conn.close()
        
        return f"✅ Structure of {full_table}:\n\n{result}"
    except Exception as e:
        logger.error(f"Error describing table: {e}")
        return format_error_message(e, f"Describing table: {full_table}")

@mcp.tool()
async def show_columns(table: str = "", schema: str = "", catalog: str = "") -> str:
    """Show columns of a specific table with detailed information."""
    if not table.strip():
        return "❌ Error: Table name is required"
    
    catalog_name = catalog.strip() or TRINO_CATALOG
    schema_name = schema.strip() or TRINO_SCHEMA
    full_table = f"{catalog_name}.{schema_name}.{table}"
    
    logger.info(f"Showing columns for: {full_table}")
    
    try:
        conn = get_trino_connection()
        cursor = conn.cursor()
        
        cursor.execute(f"SHOW COLUMNS FROM {full_table}")
        result = format_results(cursor, limit=1000)
        
        cursor.close()
        conn.close()
        
        return f"✅ Columns in {full_table}:\n\n{result}"
    except Exception as e:
        logger.error(f"Error showing columns: {e}")
        return format_error_message(e, f"Showing columns for: {full_table}")

@mcp.tool()
async def get_table_stats(table: str = "", schema: str = "", catalog: str = "") -> str:
    """Get basic statistics about a table including row count."""
    if not table.strip():
        return "❌ Error: Table name is required"
    
    catalog_name = catalog.strip() or TRINO_CATALOG
    schema_name = schema.strip() or TRINO_SCHEMA
    full_table = f"{catalog_name}.{schema_name}.{table}"
    
    logger.info(f"Getting stats for: {full_table}")
    
    try:
        conn = get_trino_connection()
        cursor = conn.cursor()
        
        # Get row count
        cursor.execute(f"SELECT COUNT(*) as row_count FROM {full_table}")
        count_result = cursor.fetchone()
        row_count = count_result[0] if count_result else 0
        
        # Get table properties if available
        cursor.execute(f"SHOW STATS FOR {full_table}")
        stats_result = format_results(cursor, limit=1000)
        
        cursor.close()
        conn.close()
        
        return f"""✅ Statistics for {full_table}:

📊 Total Rows: {row_count:,}

📈 Column Statistics:
{stats_result}"""
    except Exception as e:
        logger.error(f"Error getting table stats: {e}")
        return format_error_message(e, f"Getting stats for: {full_table}")

@mcp.tool()
async def sample_table(table: str = "", limit: str = "10", schema: str = "", catalog: str = "") -> str:
    """Get a sample of rows from a table."""
    if not table.strip():
        return "❌ Error: Table name is required"
    
    catalog_name = catalog.strip() or TRINO_CATALOG
    schema_name = schema.strip() or TRINO_SCHEMA
    full_table = f"{catalog_name}.{schema_name}.{table}"
    
    try:
        limit_int = int(limit) if limit.strip() else 10
        if limit_int > 100:
            limit_int = 100
    except ValueError:
        return f"❌ Error: Invalid limit value: {limit}"
    
    logger.info(f"Sampling {limit_int} rows from: {full_table}")
    
    try:
        conn = get_trino_connection()
        cursor = conn.cursor()
        
        cursor.execute(f"SELECT * FROM {full_table} LIMIT {limit_int}")
        result = format_results(cursor, limit=limit_int)
        
        cursor.close()
        conn.close()
        
        return f"✅ Sample from {full_table}:\n\n{result}"
    except Exception as e:
        logger.error(f"Error sampling table: {e}")
        return format_error_message(e, f"Sampling table: {full_table}")

@mcp.tool()
async def test_connection() -> str:
    """
    Test connection to Trino server and return server information.
    
    This tool helps verify that the MCP server can connect to Trino
    and provides diagnostic information.
    
    Returns:
        Connection status and server information
    """
    logger.info("Testing Trino connection")
    
    try:
        conn = get_trino_connection()
        cursor = conn.cursor()
        
        # Get server version/info
        try:
            cursor.execute("SELECT version()")
            version_result = cursor.fetchone()
            version = version_result[0] if version_result else "Unknown"
        except Exception:
            version = "Unable to retrieve version"
        
        # Test a simple query
        cursor.execute("SELECT 1 as test")
        test_result = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        return f"""✅ Connection Test Successful!

📊 Server Information:
- Host: {TRINO_HOST}:{TRINO_PORT}
- User: {TRINO_USER}
- Catalog: {TRINO_CATALOG}
- Schema: {TRINO_SCHEMA}
- Version: {version}
- Authentication: {'Enabled (BasicAuth)' if TRINO_PASSWORD else 'Disabled'}
- Protocol: {'HTTPS' if TRINO_USE_HTTPS else 'HTTP'}

✅ Test query executed successfully"""
        
    except Exception as e:
        logger.error(f"Connection test failed: {e}")
        return format_error_message(e, "Testing connection")

# === SERVER STARTUP ===
if __name__ == "__main__":
    logger.info("Starting Trino MCP server...")
    logger.info(f"Configuration:")
    logger.info(f"  Host: {TRINO_HOST}:{TRINO_PORT}")
    logger.info(f"  User: {TRINO_USER}")
    logger.info(f"  Catalog: {TRINO_CATALOG}")
    logger.info(f"  Schema: {TRINO_SCHEMA}")
    logger.info(f"  Authentication: {'Enabled' if TRINO_PASSWORD else 'Disabled'}")
    logger.info(f"  Protocol: {'HTTPS' if TRINO_USE_HTTPS else 'HTTP'}")
    logger.info(f"  Log Level: {LOG_LEVEL}")
    
    # Validate configuration
    if not TRINO_HOST:
        logger.error("TRINO_HOST environment variable is required")
        sys.exit(1)
    
    if not TRINO_USER:
        logger.error("TRINO_USER environment variable is required")
        sys.exit(1)
    
    # Test connection on startup (non-blocking)
    try:
        conn = get_trino_connection()
        conn.close()
        logger.info("✅ Successfully connected to Trino")
    except Exception as e:
        logger.warning(f"⚠️ Could not connect to Trino on startup: {e}")
        logger.warning("Server will continue - connection will be attempted when tools are used")
        logger.warning("Use the 'test_connection' tool to diagnose connection issues")
    
    try:
        mcp.run(transport='stdio')
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
        sys.exit(1)
