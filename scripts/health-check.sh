#!/bin/bash
# Health check script for Trino MCP Server container

CONTAINER_NAME="${1:-trino-mcp-server}"

echo "Checking health of container: $CONTAINER_NAME"
echo ""

# Check if container is running
if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo "❌ Container '$CONTAINER_NAME' is not running"
    exit 1
fi

echo "✅ Container is running"

# Check container health status
HEALTH=$(docker inspect --format='{{.State.Health.Status}}' "$CONTAINER_NAME" 2>/dev/null || echo "no-healthcheck")
if [ "$HEALTH" != "no-healthcheck" ]; then
    echo "Health status: $HEALTH"
fi

# Check logs for errors
echo ""
echo "Recent logs (last 10 lines):"
docker logs --tail 10 "$CONTAINER_NAME"

echo ""
echo "✅ Health check complete"
