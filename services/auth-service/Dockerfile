FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy code
COPY . .

# Expose gRPC port
EXPOSE 50051

# Run service
CMD ["python", "service.py"]
