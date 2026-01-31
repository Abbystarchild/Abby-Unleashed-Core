# Dockerfile for Abby Unleashed Core
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    portaudio19-dev \
    libsndfile1 \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p memory/storage \
    persona_library/personas \
    logs

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV LOG_LEVEL=INFO
ENV OLLAMA_HOST=http://ollama:11434

# Expose port for web API and mobile access
EXPOSE 8080

# Health check for API server
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/api/health || exit 1

# Default command - API server for mobile access
CMD ["python", "api_server.py", "--host", "0.0.0.0", "--port", "8080"]
