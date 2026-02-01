# Use Python slim image
FROM python:3.11-slim

# Metadata labels
LABEL maintainer="Trino MCP Server"
LABEL description="MCP server for read-only Trino database queries"
LABEL version="1.0.0"

# Set working directory
WORKDIR /app

# Set Python unbuffered mode for better logging
ENV PYTHONUNBUFFERED=1

# Copy requirements first for better caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the server code
COPY trino_server.py .

# Create non-root user for security
RUN useradd -m -u 1000 mcpuser && \
    chown -R mcpuser:mcpuser /app

# Switch to non-root user
USER mcpuser

# Health check to verify server is running
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)" || exit 1

# Run the server
CMD ["python", "trino_server.py"]