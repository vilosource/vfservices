# Use Python 3.12 slim as the base image for smaller size
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on

# Set the working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Azure CLI
RUN curl -sL https://aka.ms/InstallAzureCLIDeb | bash

# Install Azure Developer CLI
RUN curl -fsSL https://aka.ms/install-azd.sh | bash

# Copy requirements.txt first for better layer caching
COPY azure-rm-proxy-server/requirements.txt /tmp/requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Copy the rest of the application
COPY azure-rm-proxy-server/ /app/
COPY common/ /code/common/

# Set Python path to include common module
ENV PYTHONPATH=/code:/app

# Set default environment variables for Redis caching
ENV CACHE_TYPE=redis \
    REDIS_URL=redis://redis:6379/0 \
    REDIS_PREFIX=azure_rm_proxy: \
    PORT=7890

# Expose the port the app runs on
EXPOSE 7890

# Add a healthcheck
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:7890/api/ping || exit 1

# Create a non-root user and switch to it for security
RUN adduser --disabled-password --gecos "" appuser && \
    chown -R appuser:appuser /app && \
    chown -R appuser:appuser /code

USER appuser

# Command to run the application
CMD ["gunicorn", "azure_rm_proxy.app.main:app", "--workers", "4", "--worker-class", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:7890", "--timeout", "120"]