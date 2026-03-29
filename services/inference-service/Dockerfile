FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Copy ML models from backend
COPY ../backend/ml_pipeline/models ./models

# Expose ports
EXPOSE 8004  # HTTP API
EXPOSE 50053  # gRPC

# Health check
HEALTHCHECK --interval=30s --timeout=3s \
    CMD curl -f http://localhost:8004/health || exit 1

# Run service
CMD ["python", "main.py"]
