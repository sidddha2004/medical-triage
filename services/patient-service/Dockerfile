FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy code
COPY . .

# Copy shared backend code for models
COPY ../backend/core ./core

# Expose gRPC port
EXPOSE 50052

# Run service
CMD ["python", "service.py"]
