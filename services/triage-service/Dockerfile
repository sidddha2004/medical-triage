FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
COPY ../backend/core ./core

EXPOSE 50054

CMD ["python", "service.py"]
