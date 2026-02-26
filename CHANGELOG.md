# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-02-01

### Added
- Initial release of Trino MCP Server
- Read-only query execution tool (`execute_query`)
- Database exploration tools:
  - `show_catalogs` - List all catalogs
  - `show_schemas` - List schemas in a catalog
  - `show_tables` - List tables in a schema
  - `describe_table` - Get table structure
  - `show_columns` - Show column details
  - `get_table_stats` - Get table statistics
  - `sample_table` - Sample table data
- Connection testing tool (`test_connection`)
- Optional password-based authentication support
- HTTPS support via `TRINO_USE_HTTPS` environment variable
- Configurable logging levels via `LOG_LEVEL` environment variable
- Comprehensive error messages with troubleshooting hints
- Docker support with optimized Dockerfile
- Platform-specific setup guides (Windows, Linux, macOS)
- Cursor MCP integration documentation
- Example configurations and use cases
- Helper scripts for setup and testing

### Security
- Read-only query enforcement (blocks all write operations)
- Query validation to prevent SQL injection
- Result size limits to prevent overwhelming responses
- Non-root user in Docker container
- Secure default configurations

### Documentation
- Comprehensive README.md with quick start guide
- Platform-specific installation instructions
- Detailed Cursor MCP integration guide
- Troubleshooting section with common issues
- Usage examples for data engineers and analysts
- Contributing guidelines
- MIT License

### Infrastructure
- Dockerfile with health checks
- docker-compose.yml with multiple configuration examples
- .dockerignore for optimized builds
- Requirements.txt with pinned dependencies

## [1.1.0] - 2025-02-26

### Added
- **PII Masking Feature**: Automatic detection and masking of sensitive data before it reaches the LLM
  - Column-name heuristics to detect PII columns (email, phone, address, aadhaar, pan, etc.)
  - Regex-based content scanning for PII patterns in cell values
  - Partial masking mode (default): preserves data format while hiding values (e.g., `j***n@g***.com`)
  - Full masking mode: complete redaction with `***MASKED***`
  - Configurable via environment variables:
    - `PII_MASKING_ENABLED` - Enable/disable masking
    - `PII_MASK_STYLE` - `partial` or `full` masking
    - `PII_MASKED_COLUMNS` - Additional columns to always mask
    - `PII_ALLOWED_COLUMNS` - Columns to never mask (override auto-detection)
  - Supports Indian PII formats (Aadhaar, PAN, Indian phone numbers)
  - Supports international formats (email, phone, IP, credit card)
  - Masked column summary appended to query results

### Security
- PII masking prevents accidental exposure of sensitive data to LLMs
- Logging of masked columns for audit purposes

## [Unreleased]

### Planned
- Connection pooling for better performance
- Query timeout configuration
- Additional authentication methods (OAuth, certificates)
- More advanced query analysis tools
- Performance monitoring and metrics
- ML-based NER for advanced PII detection (optional)
