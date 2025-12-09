FROM python:3.12-slim

WORKDIR /app

# Install system dependencies including Node.js for postgres-mcp
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    curl \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Install postgres-mcp MCP server globally via npm
RUN npm install -g @modelcontextprotocol/server-postgres

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy requirements and install Python dependencies with uv
COPY requirements.txt .
RUN uv pip install --system --no-cache -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Default command (can be overridden in docker-compose.yml)
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
