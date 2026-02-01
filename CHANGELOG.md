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

## [Unreleased]

### Planned
- Connection pooling for better performance
- Query timeout configuration
- Additional authentication methods (OAuth, certificates)
- More advanced query analysis tools
- Performance monitoring and metrics
