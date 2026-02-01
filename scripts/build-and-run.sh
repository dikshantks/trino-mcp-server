#!/bin/bash
# Build and run Trino MCP Server Docker container

set -e

echo "Building Trino MCP Server Docker image..."
docker build -t trino-mcp-server:latest .

echo ""
echo "Running container..."
echo "Press Ctrl+C to stop"
echo ""

docker run -i --rm \
  -e TRINO_HOST="${TRINO_HOST:-host.docker.internal}" \
  -e TRINO_PORT="${TRINO_PORT:-8088}" \
  -e TRINO_USER="${TRINO_USER:-trino}" \
  -e TRINO_CATALOG="${TRINO_CATALOG:-tpch}" \
  -e TRINO_SCHEMA="${TRINO_SCHEMA:-tiny}" \
  -e LOG_LEVEL="${LOG_LEVEL:-INFO}" \
  trino-mcp-server:latest
