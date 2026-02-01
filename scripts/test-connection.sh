#!/bin/bash
# Test Trino connection from Docker container

set -e

echo "Testing Trino connection..."
echo ""

docker run -i --rm \
  -e TRINO_HOST="${TRINO_HOST:-host.docker.internal}" \
  -e TRINO_PORT="${TRINO_PORT:-8088}" \
  -e TRINO_USER="${TRINO_USER:-trino}" \
  -e TRINO_CATALOG="${TRINO_CATALOG:-tpch}" \
  -e TRINO_SCHEMA="${TRINO_SCHEMA:-tiny}" \
  trino-mcp-server:latest \
  python -c "
import os
import sys
sys.path.insert(0, '/app')
from trino_server import get_trino_connection

try:
    conn = get_trino_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT 1')
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    print('✅ Connection successful!')
    print(f'Host: {os.environ.get(\"TRINO_HOST\")}:{os.environ.get(\"TRINO_PORT\")}')
    print(f'User: {os.environ.get(\"TRINO_USER\")}')
    print(f'Catalog: {os.environ.get(\"TRINO_CATALOG\")}')
    print(f'Schema: {os.environ.get(\"TRINO_SCHEMA\")}')
    sys.exit(0)
except Exception as e:
    print(f'❌ Connection failed: {e}')
    sys.exit(1)
"
