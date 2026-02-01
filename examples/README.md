# Examples

This directory contains example configurations, queries, and use cases for the Trino MCP Server.

## Directory Structure

```
examples/
├── cursor-mcp-configs/    # Cursor MCP configuration examples
├── queries/                # Example SQL queries and patterns
└── use-cases/              # Workflow examples for different roles
```

## Cursor MCP Configurations

The `cursor-mcp-configs/` directory contains ready-to-use Cursor MCP configuration files:

- **windows-local.json** - Configuration for Windows with local Trino
- **linux-local.json** - Configuration for Linux with local Trino (using host.docker.internal)
- **linux-host-network.json** - Configuration for Linux using host network mode
- **macos-local.json** - Configuration for macOS with local Trino
- **ssh-tunnel.json** - Configuration for remote Trino via SSH tunnel
- **with-authentication.json** - Configuration with password authentication

### How to Use

1. Copy the appropriate configuration file for your platform
2. Open your Cursor MCP configuration file (see main README for location)
3. Merge the configuration into your existing `mcpServers` object
4. Adjust environment variables as needed
5. Restart Cursor

## Query Examples

The `queries/` directory contains example queries organized by complexity:

- **01-explore-database.md** - Basic database exploration queries
- **02-basic-analytics.md** - Simple analytical queries
- **03-joins-aggregations.md** - Complex queries with joins and aggregations

These examples show how to use the MCP tools through natural language in Cursor.

## Use Cases

The `use-cases/` directory contains workflow examples:

- **data-engineer-workflow.md** - Typical workflow for data engineers
- **analyst-workflow.md** - Typical workflow for data analysts

These guides show complete workflows from exploration to analysis.

## Getting Started

1. Start with the configuration file that matches your platform
2. Review the query examples to understand what's possible
3. Follow a use case workflow for your role
4. Adapt the examples to your specific needs

For more information, see the main [README.md](../README.md).
