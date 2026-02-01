# Trino MCP Server

A production-ready Model Context Protocol (MCP) server that provides secure, read-only access to Trino databases. Perfect for data engineers and analysts who want to leverage AI tools (like Cursor) to query and explore Trino databases.

## 🚀 Quick Start

Get up and running in 5 minutes:

1. **Prerequisites**: Docker Desktop, Cursor IDE, and access to a Trino server
2. **Build**: `docker build -t trino-mcp-server:latest .`
3. **Configure**: Add MCP server to Cursor configuration
4. **Test**: Ask Cursor to "show me all catalogs in Trino"

See [Installation](##installation) for detailed platform-specific instructions.

## 📋 Features

### Core Capabilities

- ✅ **Read-Only Safety**: All write operations (INSERT, UPDATE, DELETE, etc.) are blocked
- ✅ **Query Execution**: Execute SELECT, SHOW, DESCRIBE, EXPLAIN queries
- ✅ **Database Exploration**: List catalogs, schemas, tables, and columns
- ✅ **Data Sampling**: Preview table data with configurable limits
- ✅ **Table Statistics**: Get row counts and column statistics
- ✅ **Optional Authentication**: Support for password-based authentication
- ✅ **Health Checks**: Built-in connection testing tool

### Available Tools

| Tool | Description |
|------|-------------|
| `execute_query` | Execute read-only SQL queries (SELECT, SHOW, DESCRIBE only) |
| `show_catalogs` | List all available catalogs in Trino |
| `show_schemas` | Show all schemas in a specific catalog |
| `show_tables` | List all tables in a schema |
| `describe_table` | Get the structure and column details of a table |
| `show_columns` | Show detailed column information for a table |
| `get_table_stats` | Get statistics about a table including row count |
| `sample_table` | Get a sample of rows from a table (default 10, max 100) |
| `test_connection` | Test connection to Trino and get server information |

## 🎯 Use Cases

### For Data Engineers

- **Database Exploration**: Quickly discover available catalogs, schemas, and tables
- **Schema Analysis**: Understand table structures and relationships
- **Data Quality Checks**: Sample data and check statistics before running full queries
- **Query Development**: Test and refine SQL queries with AI assistance

### For Data Analysts

- **Ad-Hoc Analysis**: Run analytical queries without writing complex SQL
- **Data Discovery**: Explore datasets and understand their structure
- **Quick Insights**: Get table statistics and sample data for rapid analysis
- **Report Generation**: Use AI to generate queries for common reporting needs

## Installation

### Prerequisites

Before you begin, ensure you have:

1. **Docker Desktop** installed and running
   - [Download Docker Desktop](https://www.docker.com/products/docker-desktop/)
   - Verify installation: `docker --version`

2. **Cursor IDE** installed
   - [Download Cursor](https://cursor.sh/)
   - Ensure MCP Toolkit is enabled in settings

3. **Trino Server** access
   - A running Trino server (local or remote)
   - Connection details (host, port, user, catalog, schema)
   - Network access to the Trino server

### Step 1: Clone or Download

```bash
git clone https://github.com/dikshantks/trino-mcp-server.git
cd trino-mcp-server
```

Or download and extract the project files.

### Step 2: Build Docker Image

```bash
docker build -t trino-mcp-server:latest .
```

Verify the image was created:

```bash
docker images | grep trino-mcp-server
```

### Step 3: Configure Environment Variables

The server uses environment variables for configuration. You'll set these when configuring Cursor MCP.

**Required Variables:**
- `TRINO_HOST`: Trino server hostname (default: `host.docker.internal`)
- `TRINO_PORT`: Trino server port (default: `8088`)
- `TRINO_USER`: Trino username (default: `trino`)
- `TRINO_CATALOG`: Default catalog name (default: `tpch`)
- `TRINO_SCHEMA`: Default schema name (default: `tiny`)

**Optional Variables:**
- `TRINO_PASSWORD`: Password for authentication (if required)
- `TRINO_USE_HTTPS`: Use HTTPS instead of HTTP (`true`/`false`, default: `false`)
- `LOG_LEVEL`: Logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`, default: `INFO`)

## 💻 Platform-Specific Setup

### Windows

#### 1. Install Docker Desktop

1. Download [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop/)
2. Install and start Docker Desktop
3. Enable WSL 2 backend (recommended) if prompted

#### 2. Build the Image

Open PowerShell or Command Prompt:

```powershell
cd path\to\trino-mcp-server
docker build -t trino-mcp-server:latest .
```

#### 3. Configure Cursor MCP

1. Open Cursor Settings (Ctrl+,)
2. Navigate to **MCP** or search for "MCP"
3. Open the MCP configuration file:
   ```
   %APPDATA%\Cursor\mcp.json
   ```
4. Add the Trino MCP server configuration (see [Cursor MCP Integration](#cursor-mcp-integration))

#### Common Windows Issues

- **Docker daemon not running**: Start Docker Desktop
- **Permission denied**: Run PowerShell as Administrator
- **Path issues**: Use forward slashes or escaped backslashes in paths

### Linux

#### 1. Install Docker

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install docker.io docker-compose
sudo systemctl start docker
sudo systemctl enable docker
```

#### 2. Build the Image

```bash
cd trino-mcp-server
docker build -t trino-mcp-server:latest .
```

#### 3. Configure Cursor MCP

1. Open Cursor Settings
2. Navigate to **MCP**
3. Open the MCP configuration file:
4. Add the Trino MCP server configuration

#### Linux-Specific Configuration


#### Common Linux Issues

- **Permission denied**: Add user to docker group (see above)
- **host.docker.internal not working**: Use `--network host` or `--add-host` flag
- **Firewall blocking**: Check firewall rules for Docker

### macOS

#### 1. Install Docker Desktop

1. Download [Docker Desktop for Mac](https://www.docker.com/products/docker-desktop/)
2. Install and start Docker Desktop
3. Verify installation: `docker --version`

#### 2. Build the Image

Open Terminal:

```bash
cd path/to/trino-mcp-server
docker build -t trino-mcp-server:latest .
```

#### 3. Configure Cursor MCP

1. Open Cursor Settings (Cmd+,)
2. Navigate to **MCP**
3. Open the MCP configuration file:
   ```
   ~/cursor/mcp.json
   ```
4. Add the Trino MCP server configuration

## 🔌 Cursor MCP Integration

### Step-by-Step Configuration

1. **Open Cursor Settings**
   - Press `Ctrl+,` (Windows/Linux) or `Cmd+,` (macOS)
   - Or go to File → Preferences → Settings

2. **Navigate to MCP Settings**
   - Search for "MCP" in settings
   - Or manually navigate to the MCP configuration file (see platform-specific paths above)

3. **Edit Configuration File**
   - Open the `mcp.json` file
   - Add the Trino MCP server configuration

4. **Restart Cursor**
   - Fully quit and restart Cursor to load the new configuration

5. **Test Connection**
   - Open a chat in Cursor
   - Ask: "Show me all catalogs in Trino"
   - The AI should use the Trino MCP tools

   or use 

  ```json
   $ /.cursor/mcp.json
    {
     "mcpServers": {
        "trino": {
          "command": "docker",
          "args": [
            "run", "-i", "--rm",
            "-e", "TRINO_HOST=localhost",
            "-e", "TRINO_PORT=8088",
            "-e", "TRINO_USER=trino",
            "-e", "TRINO_CATALOG=iceberg",
            "-e", "TRINO_SCHEMA=tiny",
            "trino-mcp-test:latest"
          ]
        }
      }
    }

   ```

### Configuration Examples

#### Basic Configuration (Local Trino)

```json
{
  "mcpServers": {
    "trino": {
      "command": "docker",
      "args": [
        "run", "-i", "--rm",
        "-e", "TRINO_HOST=host.docker.internal",
        "-e", "TRINO_PORT=8088",
        "-e", "TRINO_USER=trino",
        "-e", "TRINO_CATALOG=tpch",
        "-e", "TRINO_SCHEMA=tiny",
        "trino-mcp-server:latest"
      ]
    }
  }
}
```

#### With Authentication

```json
{
  "mcpServers": {
    "trino": {
      "command": "docker",
      "args": [
        "run", "-i", "--rm",
        "-e", "TRINO_HOST=host.docker.internal",
        "-e", "TRINO_PORT=8088",
        "-e", "TRINO_USER=admin",
        "-e", "TRINO_PASSWORD=your_password_here",
        "-e", "TRINO_CATALOG=my_catalog",
        "-e", "TRINO_SCHEMA=my_schema",
        "trino-mcp-server:latest"
      ]
    }
  }
}
```

#### Remote Trino via SSH Tunnel

First, establish SSH tunnel in a separate terminal:

```bash
ssh -L 8088:localhost:8088 user@trino-server-host
```

Then use this configuration:

```json
{
  "mcpServers": {
    "trino": {
      "command": "docker",
      "args": [
        "run", "-i", "--rm",
        "--network", "host",
        "-e", "TRINO_HOST=localhost",
        "-e", "TRINO_PORT=8088",
        "-e", "TRINO_USER=trino",
        "-e", "TRINO_CATALOG=tpch",
        "-e", "TRINO_SCHEMA=tiny",
        "trino-mcp-server:latest"
      ]
    }
  }
}
```

#### HTTPS Connection

```json
{
  "mcpServers": {
    "trino": {
      "command": "docker",
      "args": [
        "run", "-i", "--rm",
        "-e", "TRINO_HOST=trino.example.com",
        "-e", "TRINO_PORT=8443",
        "-e", "TRINO_USER=trino",
        "-e", "TRINO_USE_HTTPS=true",
        "-e", "TRINO_CATALOG=tpch",
        "-e", "TRINO_SCHEMA=tiny",
        "trino-mcp-server:latest"
      ]
    }
  }
}
```

### Verifying the Connection

1. **Check MCP Server Status**
   - Look for MCP server status in Cursor's status bar
   - Or check Cursor's MCP panel (if available)

2. **Test with a Simple Query**
   - Ask Cursor: "Test the Trino connection"
   - Or: "Show me all catalogs in Trino"
   - The AI should successfully use the MCP tools

3. **Check Logs** (if issues occur)
   - Docker logs: `docker ps` to find container, then `docker logs <container-id>`
   - Cursor logs: Check Cursor's developer console

## ⚙️ Configuration Reference

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `TRINO_HOST` | Yes | `host.docker.internal` | Trino server hostname |
| `TRINO_PORT` | Yes | `8088` | Trino server port |
| `TRINO_USER` | Yes | `trino` | Trino username |
| `TRINO_CATALOG` | Yes | `tpch` | Default catalog name |
| `TRINO_SCHEMA` | Yes | `tiny` | Default schema name |
| `TRINO_PASSWORD` | No | - | Password for authentication (if required) |
| `TRINO_USE_HTTPS` | No | `false` | Use HTTPS instead of HTTP |
| `LOG_LEVEL` | No | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR) |

### Authentication

The server supports optional password-based authentication:

- **No Authentication**: If `TRINO_PASSWORD` is not set, connections use no authentication
- **Basic Authentication**: If `TRINO_PASSWORD` is set, BasicAuth is used
- **HTTPS**: Set `TRINO_USE_HTTPS=true` for secure connections

### Network Configuration

**Local Trino Server:**
- Use `host.docker.internal` as `TRINO_HOST` (Windows/macOS)
- On Linux, use `--network host` or `--add-host` flag

**Remote Trino Server:**
- Use SSH tunnel: `ssh -L 8088:localhost:8088 user@host`
- Set `TRINO_HOST=localhost` and use `--network host`
- Or use direct connection with proper firewall rules

## 📖 Usage Examples

### Basic Database Exploration

```
User: Show me all catalogs in Trino
AI: [Uses show_catalogs tool]

User: What schemas are in the tpch catalog?
AI: [Uses show_schemas tool with catalog="tpch"]

User: List all tables in tpch.tiny
AI: [Uses show_tables tool]
```

### Table Analysis

```
User: Describe the customer table structure
AI: [Uses describe_table tool]

User: Show me 5 sample rows from the orders table
AI: [Uses sample_table tool with limit=5]

User: Get statistics for the lineitem table
AI: [Uses get_table_stats tool]
```

### Query Execution

```
User: Run this query: SELECT COUNT(*) FROM tpch.tiny.customer
AI: [Uses execute_query tool]

User: Show me the top 10 customers by order count
AI: [Uses execute_query with a JOIN query]
```

### Data Engineering Workflows

```
User: Help me explore the sales database
AI: [Uses multiple tools: show_catalogs, show_schemas, show_tables]

User: What's the schema of the transactions table?
AI: [Uses describe_table tool]

User: Check if the transactions table has any data
AI: [Uses get_table_stats tool]
```

## 🔧 Troubleshooting

### Connection Issues

**Problem**: Cannot connect to Trino server

**Solutions**:
1. Verify Trino server is running:
   ```bash
   curl http://localhost:8088/v1/info
   ```

2. Check environment variables are correct:
   - `TRINO_HOST` matches your Trino server address
   - `TRINO_PORT` matches your Trino server port
   - `TRINO_USER` is valid

3. For Docker networking:
   - Windows/macOS: Use `host.docker.internal`
   - Linux: Use `--network host` or `--add-host=host.docker.internal:host-gateway`

4. Check firewall rules and network connectivity

**Problem**: Connection works locally but not in Docker

**Solutions**:
- Use `host.docker.internal` instead of `localhost`
- On Linux, add `--add-host=host.docker.internal:host-gateway`
- Or use `--network host` mode

### Cursor MCP Integration Issues

**Problem**: MCP server not appearing in Cursor

**Solutions**:
1. Verify JSON syntax in configuration file
2. Check Docker image exists: `docker images | grep trino-mcp-server`
3. Test Docker run manually:
   ```bash
   docker run -i --rm -e TRINO_HOST=host.docker.internal -e TRINO_PORT=8088 trino-mcp-server:latest
   ```
4. Fully restart Cursor (not just reload window)
5. Check Cursor logs for errors

**Problem**: Tools not working in Cursor

**Solutions**:
1. Use the `test_connection` tool to verify connectivity
2. Check Docker container logs
3. Verify environment variables are set correctly
4. Ensure Trino server is accessible from Docker container

### Query Execution Issues

**Problem**: Query execution fails

**Solutions**:
1. Verify query is read-only (SELECT, SHOW, DESCRIBE only)
2. Check table/schema/catalog names are correct
3. Verify user has read permissions
4. Check Trino server logs for detailed errors

**Problem**: "Only read-only queries are allowed" error

**Solutions**:
- The server blocks all write operations for safety
- Use only SELECT, SHOW, DESCRIBE, EXPLAIN, WITH queries
- Check query doesn't contain INSERT, UPDATE, DELETE, etc.

### Authentication Issues

**Problem**: Authentication failed

**Solutions**:
1. Verify `TRINO_USER` is correct
2. Check `TRINO_PASSWORD` is set correctly (if required)
3. Verify user has read permissions on the catalog
4. Check Trino server authentication configuration

### Docker Issues

**Problem**: Docker build fails

**Solutions**:
1. Check Docker is running: `docker ps`
2. Verify Dockerfile syntax
3. Check internet connection (for downloading dependencies)
4. Try rebuilding: `docker build --no-cache -t trino-mcp-server:latest .`

**Problem**: Container exits immediately

**Solutions**:
1. Check logs: `docker logs <container-id>`
2. Verify environment variables are set
3. Test connection manually
4. Check Trino server is accessible

## 🛠️ Development

### Local Development Setup

1. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Set environment variables**:
   ```bash
   export TRINO_HOST="localhost"
   export TRINO_PORT="8088"
   export TRINO_USER="trino"
   export TRINO_CATALOG="tpch"
   export TRINO_SCHEMA="tiny"
   ```

3. **Run server directly**:
   ```bash
   python trino_server.py
   ```

4. **Test MCP protocol**:
   ```bash
   echo '{"jsonrpc":"2.0","method":"tools/list","id":1}' | python trino_server.py
   ```

### Adding New Tools

1. Add function to `trino_server.py`
2. Decorate with `@mcp.tool()`
3. Ensure it validates queries for read-only access (if executing queries)
4. Add comprehensive docstring
5. Test locally
6. Rebuild Docker image

### Code Style

- Follow PEP 8 Python style guide
- Use type hints for all functions
- Add docstrings with examples
- Keep functions focused and single-purpose

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🤝 Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## 📚 Additional Resources

- [Trino Documentation](https://trino.io/docs/)
- [Model Context Protocol](https://modelcontextprotocol.io/)
- [Cursor Documentation](https://cursor.sh/docs)


**Happy Querying!** 🚀
