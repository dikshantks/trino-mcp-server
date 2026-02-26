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
from decimal import Decimal
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
TRINO_HOST = os.environ.get("TRINO_HOST", "localhost")
TRINO_PORT = int(os.environ.get("TRINO_PORT", "8088"))
TRINO_USER = os.environ.get("TRINO_USER", "trino")
TRINO_PASSWORD = os.environ.get("TRINO_PASSWORD")  # Optional
TRINO_USE_HTTPS = os.environ.get("TRINO_USE_HTTPS", "false").lower() == "true"
TRINO_CATALOG = os.environ.get("TRINO_CATALOG", "tpch")
TRINO_SCHEMA = os.environ.get("TRINO_SCHEMA", "tiny")

# PII Masking Configuration
PII_MASKING_ENABLED = os.environ.get("PII_MASKING_ENABLED", "true").lower() == "true"
PII_MASKED_COLUMNS = [col.strip().lower() for col in os.environ.get("PII_MASKED_COLUMNS", "").split(",") if col.strip()]
PII_ALLOWED_COLUMNS = [col.strip().lower() for col in os.environ.get("PII_ALLOWED_COLUMNS", "").split(",") if col.strip()]
PII_MASK_STYLE = os.environ.get("PII_MASK_STYLE", "partial").lower()  # "full" or "partial"

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
        host = TRINO_HOST
        
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

# === PII MASKING FUNCTIONS ===

# Known PII column name patterns (case-insensitive matching)
PII_COLUMN_PATTERNS = {
    'email': ['email', 'e_mail', 'email_address', 'gmail', 'mail_id', 'emailid', 'user_email', 'customer_email'],
    'phone': ['phone', 'mobile', 'cell', 'telephone', 'contact_number', 'phone_number', 'phoneno', 'mobileno', 
              'contact_no', 'tel', 'fax', 'whatsapp'],
    'address': ['address', 'street', 'city', 'state', 'zip', 'zipcode', 'postal', 'pincode', 'postal_code',
                'addr', 'locality', 'landmark', 'house_no', 'flat_no', 'building', 'apartment'],
    'identity': ['ssn', 'social_security', 'pan', 'pan_number', 'aadhaar', 'aadhar', 'aadhaar_number',
                 'passport', 'passport_number', 'license_number', 'driving_license', 'voter_id', 'ration_card'],
    'financial': ['credit_card', 'card_number', 'bank_account', 'account_number', 'ifsc', 'ifsc_code',
                  'cvv', 'card_cvv', 'upi', 'upi_id', 'vpa'],
    'personal': ['first_name', 'last_name', 'full_name', 'name', 'dob', 'date_of_birth', 'birth_date',
                 'father_name', 'mother_name', 'spouse_name'],
    'network': ['ip_address', 'ip', 'mac_address', 'mac', 'device_id', 'imei'],
}


def is_pii_column(column_name: str) -> tuple:
    """
    Check if a column name matches known PII patterns.
    
    Args:
        column_name: The column name to check
        
    Returns:
        Tuple of (is_pii: bool, pii_type: str or None)
    """
    col_lower = column_name.lower().strip()
    
    # Check if column is in the user-defined allowed list (skip masking)
    if col_lower in PII_ALLOWED_COLUMNS:
        return False, None
    
    # Check if column is in the user-defined forced mask list
    for forced_col in PII_MASKED_COLUMNS:
        if forced_col in col_lower or col_lower in forced_col:
            return True, 'user_defined'
    
    # Check against known PII patterns
    for pii_type, patterns in PII_COLUMN_PATTERNS.items():
        for pattern in patterns:
            # Match if pattern is contained in column name or vice versa
            if pattern in col_lower or col_lower == pattern:
                return True, pii_type
    
    return False, None


# Compiled regex patterns for PII detection in cell values
PII_REGEX_PATTERNS = {
    'email': re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b'),
    'phone_intl': re.compile(r'\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b'),
    'phone_indian': re.compile(r'\b(?:\+91|91|0)?[6-9]\d{9}\b'),
    'ip_address': re.compile(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b'),
    'credit_card': re.compile(r'\b(?:\d{4}[-\s]?){3}\d{4}\b'),
    'aadhaar': re.compile(r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}\b'),  # Indian Aadhaar format
    'pan': re.compile(r'\b[A-Z]{5}\d{4}[A-Z]\b'),  # Indian PAN format
}


def scan_for_pii_patterns(value: str) -> Optional[str]:
    """
    Scan a cell value for PII patterns using regex.
    
    Args:
        value: The string value to scan
        
    Returns:
        The type of PII detected, or None if no PII found
    """
    if not isinstance(value, str) or not value:
        return None
    
    # Check each pattern
    for pii_type, pattern in PII_REGEX_PATTERNS.items():
        if pattern.search(value):
            return pii_type
    
    return None


def mask_cell_value(value, pii_type: str = None) -> str:
    """
    Mask a single cell value based on the configured mask style.
    
    Args:
        value: The value to mask
        pii_type: The type of PII (used for smart partial masking)
        
    Returns:
        Masked value string
    """
    if value is None:
        return ""
    
    str_value = str(value)
    
    if not str_value or str_value.lower() in ('none', 'null', 'nan', ''):
        return str_value
    
    # Full masking - replace entire value
    if PII_MASK_STYLE == "full":
        return "***MASKED***"
    
    # Partial masking - keep some characters for context
    if pii_type == 'email' and '@' in str_value:
        # Email: j****n@g****.com
        parts = str_value.split('@')
        if len(parts) == 2:
            local = parts[0]
            domain = parts[1]
            if len(local) > 2:
                masked_local = local[0] + '****' + local[-1]
            elif len(local) > 0:
                masked_local = local[0] + '****'
            else:
                masked_local = '****'
            domain_parts = domain.split('.')
            if len(domain_parts) >= 2:
                masked_domain = domain_parts[0][0] + '****.' + domain_parts[-1]
            else:
                masked_domain = '****'
            return f"{masked_local}@{masked_domain}"
    
    if pii_type in ('phone_intl', 'phone_indian', 'phone'):
        # Phone: ***-***-4567 (show last 4 digits)
        digits = re.sub(r'\D', '', str_value)
        if len(digits) >= 4:
            return f"***-***-{digits[-4:]}"
        return "***-***-****"
    
    if pii_type == 'credit_card':
        # Credit card: ****-****-****-1234 (show last 4)
        digits = re.sub(r'\D', '', str_value)
        if len(digits) >= 4:
            return f"****-****-****-{digits[-4:]}"
        return "****-****-****-****"
    
    if pii_type == 'aadhaar':
        # Aadhaar: ****-****-1234 (show last 4)
        digits = re.sub(r'\D', '', str_value)
        if len(digits) >= 4:
            return f"****-****-{digits[-4:]}"
        return "****-****-****"
    
    if pii_type == 'pan':
        # PAN: show first 2 and last 1 character
        if len(str_value) >= 3:
            return f"{str_value[:2]}*****{str_value[-1]}"
        return "**********"
    
    if pii_type == 'ip_address':
        # IP: show first octet only
        parts = str_value.split('.')
        if len(parts) == 4:
            return f"{parts[0]}.***.***.*"
        return "***.***.***.***"
    
    # Generic masking: show first and last character with clear mask indicator
    if len(str_value) <= 2:
        return "[MASKED]"
    elif len(str_value) <= 4:
        return str_value[0] + "[**]" + str_value[-1]
    else:
        return str_value[0] + "[****]" + str_value[-1]


def mask_pii_in_dataframe(df: pd.DataFrame, columns: list) -> tuple:
    """
    Apply PII masking to a DataFrame.
    
    Args:
        df: The pandas DataFrame to mask
        columns: List of column names
        
    Returns:
        Tuple of (masked_df, masked_columns_summary)
    """
    masked_columns = {}
    df_masked = df.copy()
    
    for col in columns:
        # Layer 1: Check if column name indicates PII
        is_pii, pii_type = is_pii_column(col)
        
        if is_pii:
            # Mask entire column
            df_masked[col] = df_masked[col].apply(lambda x: mask_cell_value(x, pii_type))
            masked_columns[col] = pii_type
            logger.debug(f"Masked column '{col}' (type: {pii_type}) based on column name")
        else:
            # Layer 2: Scan cell values for PII patterns
            # Only scan string columns to avoid performance issues
            if df_masked[col].dtype == 'object':
                cells_with_pii = 0
                detected_type = None
                
                # Sample first few rows to detect pattern
                sample_size = min(10, len(df_masked))
                for idx in range(sample_size):
                    cell_value = df_masked[col].iloc[idx]
                    if cell_value is not None:
                        detected = scan_for_pii_patterns(str(cell_value))
                        if detected:
                            cells_with_pii += 1
                            detected_type = detected
                
                # If significant portion of sample has PII, mask the column
                if cells_with_pii >= 2 or (sample_size <= 3 and cells_with_pii >= 1):
                    df_masked[col] = df_masked[col].apply(lambda x: mask_cell_value(x, detected_type))
                    masked_columns[col] = f"{detected_type} (content)"
                    logger.debug(f"Masked column '{col}' (type: {detected_type}) based on content scan")
    
    return df_masked, masked_columns


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
        
        # Convert rows to list of lists, handling special types
        processed_rows = []
        for row in rows:
            processed_row = []
            for val in row:
                try:
                    if val is None:
                        processed_row.append(None)
                    elif isinstance(val, Decimal):
                        # Handle Decimal type (common in Trino)
                        processed_row.append(str(val))
                    elif hasattr(val, 'isoformat'):
                        # Handle datetime, date, time objects
                        processed_row.append(val.isoformat())
                    elif isinstance(val, (bytes, bytearray)):
                        # Handle binary data
                        processed_row.append(f"<binary:{len(val)} bytes>")
                    elif isinstance(val, (list, dict)):
                        # Handle arrays and maps
                        processed_row.append(str(val))
                    elif isinstance(val, (int, float, str, bool)):
                        # Handle basic types directly
                        processed_row.append(val)
                    else:
                        # Handle any other types by converting to string
                        processed_row.append(str(val))
                except Exception as e:
                    logger.warning(f"Error converting value {type(val)}: {e}")
                    processed_row.append(f"<error: {type(val).__name__}>")
            processed_rows.append(processed_row)
        
        # Create DataFrame for better formatting
        df = pd.DataFrame(processed_rows, columns=columns)
        
        # Convert all columns to string to avoid formatting issues
        # Replace None with empty string for tabulate compatibility
        for col in df.columns:
            df[col] = df[col].apply(lambda x: str(x) if x is not None else "")
        
        # Apply PII masking if enabled
        masked_columns = {}
        if PII_MASKING_ENABLED:
            df, masked_columns = mask_pii_in_dataframe(df, columns)
            if masked_columns:
                logger.info(f"PII masking applied to columns: {list(masked_columns.keys())}")
        
        # Format as table with column width limits
        table = tabulate(df, headers='keys', tablefmt='grid', showindex=False, maxcolwidths=50)
        
        result_count = len(rows)
        total_msg = f"\n\nShowing {result_count} row(s)"
        if result_count == limit:
            total_msg += f" (limited to {limit} rows)"
        
        # Add PII masking footer if columns were masked
        if masked_columns:
            masked_list = ", ".join([f"{col} ({ptype})" for col, ptype in masked_columns.items()])
            total_msg += f"\n\n[PII Masking Active] Masked columns: {masked_list}"
        
        return f"{table}{total_msg}"
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        logger.error(f"Error formatting results: {e}")
        logger.error(f"Full traceback:\n{error_trace}")
        # Return more details in error message for debugging
        return f"Error formatting results: {str(e)}\n\nDebug info:\n{error_trace}"

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
    logger.info(f"PII Masking Configuration:")
    logger.info(f"  Enabled: {PII_MASKING_ENABLED}")
    if PII_MASKING_ENABLED:
        logger.info(f"  Mask Style: {PII_MASK_STYLE}")
        logger.info(f"  Additional Masked Columns: {PII_MASKED_COLUMNS if PII_MASKED_COLUMNS else 'None'}")
        logger.info(f"  Allowed Columns (skip masking): {PII_ALLOWED_COLUMNS if PII_ALLOWED_COLUMNS else 'None'}")
    
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
