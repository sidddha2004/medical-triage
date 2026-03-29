# Inference Service + MLflow Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build production ML inference service with MLflow for model registry, A/B testing, and experiment tracking.

**Architecture:** Extract ML inference from Django monolith into dedicated service. MLflow tracks experiments, stores model versions, and enables A/B testing between model versions. Redis caching layer for low-latency predictions.

**Tech Stack:** MLflow, Redis, XGBoost, FastAPI (for inference API), Docker, Prometheus metrics

---

## Files Overview

| File | Action | Responsibility |
|------|--------|----------------|
| `services/inference-service/` | Modify | Refactor to FastAPI + gRPC |
| `services/inference-service/api.py` | Create | FastAPI inference endpoints |
| `services/inference-service/mlflow_client.py` | Create | MLflow integration |
| `mlflow/Dockerfile` | Create | MLflow tracking server |
| `docker/docker-compose.yml` | Modify | Add MLflow service |
| `backend/ml_pipeline/mlflow_tracking.py` | Create | MLflow experiment tracking |

---

### Task 1: MLflow Tracking Server

**Files:**
- Create: `docker/mlflow/Dockerfile`
- Create: `docker/mlflow/requirements.txt`
- Modify: `docker/docker-compose.yml`

- [ ] **Step 1: Create MLflow Dockerfile**

```dockerfile
# docker/mlflow/Dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Expose MLflow ports
EXPOSE 5000  # MLflow UI
EXPOSE 5001  # Artifact proxy

# Health check
HEALTHCHECK --interval=30s --timeout=3s CMD curl -f http://localhost:5000/health || exit 1

# Run MLflow server
CMD ["mlflow", "server", \
     "--host", "0.0.0.0", \
     "--port", "5000", \
     "--backend-store-uri", "sqlite:///mlflow.db", \
     "--default-artifact-root", "/mlflow/artifacts", \
     "--serve-artifacts"]
```

- [ ] **Step 2: Create MLflow requirements**

```txt
# docker/mlflow/requirements.txt
mlflow>=2.10.0
psycopg2-binary>=2.9
boto3>=1.34  # For S3 artifact storage (optional)
```

- [ ] **Step 3: Add MLflow to docker-compose**

Read current `docker/docker-compose.yml`, then add:

```yaml
services:
  # ... existing services ...

  # MLflow Tracking Server
  mlflow:
    build:
      context: ./mlflow
      dockerfile: Dockerfile
    container_name: medical_triage_mlflow
    ports:
      - "5000:5000"  # MLflow UI
    environment:
      - MLFLOW_TRACKING_URI=http://mlflow:5000
      - MLFLOW_S3_ENDPOINT_URL=http://minio:9000  # Optional: for S3
      - AWS_ACCESS_KEY_ID=minioadmin
      - AWS_SECRET_ACCESS_KEY=minioadmin
    volumes:
      - mlflow_data:/mlflow
      - ../backend/ml_pipeline/models:/app/models
    depends_on:
      - postgres
    networks:
      - medical_triage_network
    restart: unless-stopped

volumes:
  mlflow_data:
```

- [ ] **Step 4: Commit**

```bash
git add docker/mlflow/ docker/docker-compose.yml
git commit -m "infra: add MLflow tracking server"
```

---

### Task 2: MLflow Client Integration

**Files:**
- Create: `backend/ml_pipeline/mlflow_tracking.py`
- Modify: `backend/ml_pipeline/api.py`

- [ ] **Step 1: Create MLflow tracking module**

```python
# backend/ml_pipeline/mlflow_tracking.py
"""
MLflow Integration for Health Triage ML Pipeline.

Provides experiment tracking, model registry, and A/B testing support.
"""

import os
import mlflow
import mlflow.xgboost
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class MLflowClient:
    """MLflow client for experiment tracking and model registry."""

    def __init__(self, tracking_uri: Optional[str] = None):
        self.tracking_uri = tracking_uri or os.getenv(
            'MLFLOW_TRACKING_URI',
            'http://localhost:5000'
        )
        mlflow.set_tracking_uri(self.tracking_uri)
        mlflow.set_experiment('health-triage-symptom-classifier')
        logger.info(f'MLflow tracking URI: {self.tracking_uri}')

    def start_run(
        self,
        run_name: str,
        tags: Optional[Dict[str, str]] = None
    ) -> mlflow.ActiveRun:
        """Start a new MLflow run."""
        run = mlflow.start_run(run_name=run_name)

        if tags:
            mlflow.set_tags(tags)

        logger.info(f'Started MLflow run: {run.info.run_id}')
        return run

    def end_run(self):
        """End the current MLflow run."""
        mlflow.end_run()
        logger.info('Ended MLflow run')

    def log_params(self, params: Dict[str, Any]):
        """Log hyperparameters."""
        mlflow.log_params(params)

    def log_metrics(self, metrics: Dict[str, float], step: Optional[int] = None):
        """Log metrics."""
        mlflow.log_metrics(metrics, step=step)

    def log_model(
        self,
        model,
        artifact_path: str = 'model',
        registered_model_name: Optional[str] = None,
        signature=None,
        input_example=None
    ):
        """Log model and optionally register it."""
        mlflow.xgboost.log_model(
            xgb_model=model,
            artifact_path=artifact_path,
            registered_model_name=registered_model_name,
            signature=signature,
            input_example=input_example
        )
        logger.info(f'Logged model to {artifact_path}')

    def get_latest_model_version(self, model_name: str) -> Optional[str]:
        """Get the latest version of a registered model."""
        from mlflow.tracking import MlflowClient

        client = MlflowClient(self.tracking_uri)

        try:
            versions = client.search_model_versions(
                f"name='{model_name}'",
                max_results=1
            )
            if versions:
                return versions[0].version
            return None
        except Exception as e:
            logger.error(f'Error getting model version: {e}')
            return None

    def load_model(
        self,
        model_name: str,
        version: Optional[str] = None
    ):
        """Load a model from the registry."""
        if version:
            model_uri = f'models:/{model_name}/{version}'
        else:
            # Load latest version
            latest_version = self.get_latest_model_version(model_name)
            if latest_version:
                model_uri = f'models:/{model_name}/{latest_version}'
            else:
                # Fallback to local model
                model_uri = 'ml_pipeline/models/classifier.joblib'
                logger.warning(f'Using fallback model: {model_uri}')

        logger.info(f'Loading model: {model_uri}')
        return mlflow.pyfunc.load_model(model_uri)

    def transition_model_stage(
        self,
        model_name: str,
        version: str,
        stage: str
    ):
        """Transition model to a different stage (Staging, Production, etc.)."""
        from mlflow.tracking import MlflowClient

        client = MlflowClient(self.tracking_uri)

        try:
            client.transition_model_version_stage(
                name=model_name,
                version=version,
                stage=stage
            )
            logger.info(f'Transitioned {model_name} v{version} to {stage}')
        except Exception as e:
            logger.error(f'Error transitioning model stage: {e}')

    def log_inference(
        self,
        model_name: str,
        inputs: List[str],
        prediction: str,
        confidence: float,
        latency_ms: float,
        cache_hit: bool = False
    ):
        """Log a single inference request."""
        mlflow.log_metric(f'{model_name}.inference_latency', latency_ms)
        mlflow.log_metric(f'{model_name}.confidence', confidence)
        mlflow.log_metric(f'{model_name}.cache_hit', 1 if cache_hit else 0)


# Global MLflow client
_mlflow_client = None


def get_mlflow_client() -> MLflowClient:
    """Get or create the global MLflow client."""
    global _mlflow_client
    if _mlflow_client is None:
        _mlflow_client = MLflowClient()
    return _mlflow_client


def log_training_run(
    model,
    metrics: Dict[str, float],
    params: Dict[str, Any],
    model_name: str = 'health-triage-classifier',
    run_name: Optional[str] = None
) -> str:
    """Log a complete training run to MLflow."""
    client = get_mlflow_client()

    run_name = run_name or f'training-{datetime.now().strftime("%Y%m%d-%H%M%S")}'

    with client.start_run(run_name=run_name):
        client.log_params(params)
        client.log_metrics(metrics)
        client.log_model(
            model=model,
            artifact_path='model',
            registered_model_name=model_name
        )

        run_id = mlflow.active_run().info.run_id
        logger.info(f'Logged training run: {run_id}')
        return run_id
```

- [ ] **Step 2: Commit**

```bash
git add backend/ml_pipeline/mlflow_tracking.py
git commit -m "feat(mlflow): add MLflow tracking client"
```

---

### Task 3: FastAPI Inference Service

**Files:**
- Create: `services/inference-service/api.py`
- Create: `services/inference-service/main.py`
- Create: `services/inference-service/requirements.txt`

- [ ] **Step 1: Create FastAPI requirements**

```txt
# services/inference-service/requirements.txt
fastapi>=0.109.0
uvicorn[standard]>=0.27.0
grpcio>=1.60.0
grpcio-tools>=1.60.0
mlflow>=2.10.0
redis>=5.0
scikit-learn>=1.5
xgboost>=2.1
joblib>=1.4
prometheus-client>=0.19.0
python-decouple>=3.8
```

- [ ] **Step 2: Create FastAPI inference API**

```python
# services/inference-service/api.py
"""
FastAPI Inference Service with MLflow and Redis caching.
"""

from fastapi import FastAPI, HTTPException, Header, Depends
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import time
import hashlib
import json
import os
import logging
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
import redis

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title='Health Triage Inference Service',
    description='ML inference API with MLflow model registry and Redis caching',
    version='1.0.0'
)

# Prometheus metrics
INFERENCE_REQUESTS = Counter(
    'inference_requests_total',
    'Total inference requests',
    ['status', 'model_version', 'cache_hit']
)

INFERENCE_LATENCY = Histogram(
    'inference_latency_seconds',
    'Inference latency',
    ['model_version'],
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0]
)

MODEL_ACCURACY = Counter(
    'model_predictions_total',
    'Model predictions by disease',
    ['disease', 'model_version']
)


# Redis cache
redis_client = redis.Redis(
    host=os.getenv('REDIS_HOST', 'localhost'),
    port=int(os.getenv('REDIS_PORT', 6379)),
    db=0,
    decode_responses=True
)


# Request/Response models
class PredictRequest(BaseModel):
    symptoms: List[str] = Field(..., description='List of symptoms')
    model_version: Optional[str] = Field(None, description='Specific model version')
    patient_id: Optional[int] = None


class PredictResponse(BaseModel):
    success: bool
    disease: Optional[str] = None
    confidence: Optional[float] = None
    matched_symptoms: Optional[List[str]] = None
    precautions: Optional[List[str]] = None
    model_version: Optional[str] = None
    latency_ms: Optional[float] = None
    cache_hit: Optional[bool] = None
    error: Optional[str] = None


class BatchPredictRequest(BaseModel):
    requests: List[PredictRequest]


class BatchPredictResponse(BaseModel):
    success: bool
    predictions: List[PredictResponse]
    error: Optional[str] = None


class ModelStatusResponse(BaseModel):
    loaded: bool
    model_version: str
    model_name: str
    total_diseases: int
    total_symptoms: int
    mlflow_uri: str


# Model loader
class ModelService:
    """ML model service with MLflow integration."""

    def __init__(self):
        self.model = None
        self.encoder = None
        self.model_version = None
        self.model_name = 'health-triage-classifier'
        self.load_model()

    def load_model(self):
        """Load model from MLflow or fallback to local."""
        import joblib
        import mlflow.pyfunc

        mlflow_uri = os.getenv('MLFLOW_TRACKING_URI', 'http://mlflow:5000')
        mlflow.set_tracking_uri(mlflow_uri)

        try:
            # Try to load from MLflow registry
            from mlflow.tracking import MlflowClient
            client = MlflowClient(mlflow_uri)

            versions = client.search_model_versions(
                f"name='{self.model_name}'",
                max_results=1
            )

            if versions:
                version = versions[0].version
                model_uri = f'models:/{self.model_name}/{version}'
                self.model = mlflow.pyfunc.load_model(model_uri)
                self.model_version = f'v{version}'
                logger.info(f'Loaded model from MLflow: {model_uri}')
            else:
                raise FileNotFoundError('No model in MLflow registry')

        except Exception as e:
            logger.warning(f'MLflow load failed: {e}, using local model')
            # Fallback to local model
            model_path = os.getenv('MODEL_PATH', 'models/classifier.joblib')
            encoder_path = os.getenv('ENCODER_PATH', 'models/encoder.joblib')

            self.model = joblib.load(model_path)
            self.encoder = joblib.load(encoder_path)
            self.model_version = 'v1.0-local'
            logger.info(f'Loaded local model: {model_path}')

    def predict(self, symptoms: List[str]) -> Dict[str, Any]:
        """Run inference."""
        if self.model is None:
            raise RuntimeError('Model not loaded')

        # Encode symptoms
        if self.encoder:
            symptom_vector = self.encoder.transform([symptoms])
        else:
            # MLflow pyfunc model handles preprocessing
            symptom_vector = symptoms

        # Predict
        if hasattr(self.model, 'predict'):
            prediction = self.model.predict(symptom_vector)[0]
            if hasattr(self.model, 'predict_proba'):
                probabilities = self.model.predict_proba(symptom_vector)[0]
                confidence = float(max(probabilities))
            else:
                confidence = 1.0
        else:
            # MLflow pyfunc
            result = self.model.predict([symptoms])[0]
            prediction = result.get('prediction', 'Unknown')
            confidence = result.get('confidence', 0.0)

        return {
            'disease': prediction,
            'confidence': confidence,
            'matched_symptoms': symptoms
        }


# Global model service
model_service = ModelService()


def get_cache_key(symptoms: List[str]) -> str:
    """Generate cache key from sorted symptoms."""
    sorted_symptoms = sorted(symptoms)
    key_str = '|'.join(sorted_symptoms)
    return hashlib.md5(key_str.encode()).hexdigest()


def get_precautions(disease: str) -> List[str]:
    """Get precautions for a disease."""
    precautions_map = {
        'Flu': ['Rest', 'Hydrate', 'Isolate from others'],
        'Migraine': ['Rest in dark room', 'Hydrate', 'Avoid bright lights'],
        'Common Cold': ['Rest', 'Hydrate', 'Over-the-counter medication'],
        'Allergy': ['Avoid allergens', 'Antihistamines', 'Monitor symptoms'],
    }
    return precautions_map.get(disease, ['Consult a healthcare provider'])


@app.get('/health')
async def health_check():
    """Health check endpoint."""
    return {
        'status': 'healthy',
        'model_loaded': model_service.model is not None,
        'model_version': model_service.model_version
    }


@app.get('/metrics')
async def metrics():
    """Prometheus metrics endpoint."""
    return generate_latest(CONTENT_TYPE_LATEST)


@app.get('/model/status', response_model=ModelStatusResponse)
async def get_model_status():
    """Get model status and metadata."""
    return ModelStatusResponse(
        loaded=model_service.model is not None,
        model_version=model_service.model_version,
        model_name=model_service.model_name,
        total_diseases=len(model_service.model.classes_) if hasattr(model_service.model, 'classes_') else 0,
        total_symptoms=len(model_service.encoder.categories_[0]) if hasattr(model_service.encoder, 'categories_') else 0,
        mlflow_uri=os.getenv('MLFLOW_TRACKING_URI', 'http://mlflow:5000')
    )


@app.post('/predict', response_model=PredictResponse)
async def predict(request: PredictRequest):
    """
    Get ML prediction for symptoms.

    - **symptoms**: List of symptom strings
    - **model_version**: Optional specific model version
    - **patient_id**: Optional patient ID for tracking
    """
    start_time = time.time()

    try:
        # Check cache first
        cache_key = get_cache_key(request.symptoms)
        cached_result = redis_client.get(cache_key)

        if cached_result:
            result = json.loads(cached_result)
            latency_ms = (time.time() - start_time) * 1000

            INFERENCE_REQUESTS.labels(
                status='success',
                model_version=model_service.model_version,
                cache_hit='true'
            ).inc()

            return PredictResponse(
                success=True,
                disease=result['disease'],
                confidence=result['confidence'],
                matched_symptoms=result['matched_symptoms'],
                precautions=result['precautions'],
                model_version=model_service.model_version,
                latency_ms=latency_ms,
                cache_hit=True
            )

        # Run inference
        inference_result = model_service.predict(request.symptoms)
        precautions = get_precautions(inference_result['disease'])

        latency_ms = (time.time() - start_time) * 1000

        # Cache result (24 hour TTL)
        result_to_cache = {
            **inference_result,
            'precautions': precautions,
            'model_version': model_service.model_version
        }
        redis_client.setex(cache_key, 86400, json.dumps(result_to_cache))

        # Log metrics
        INFERENCE_REQUESTS.labels(
            status='success',
            model_version=model_service.model_version,
            cache_hit='false'
        ).inc()
        INFERENCE_LATENCY.labels(
            model_version=model_service.model_version
        ).observe(latency_ms / 1000)  # Convert to seconds
        MODEL_ACCURACY.labels(
            disease=inference_result['disease'],
            model_version=model_service.model_version
        ).inc()

        return PredictResponse(
            success=True,
            disease=inference_result['disease'],
            confidence=inference_result['confidence'],
            matched_symptoms=inference_result['matched_symptoms'],
            precautions=precautions,
            model_version=model_service.model_version,
            latency_ms=latency_ms,
            cache_hit=False
        )

    except Exception as e:
        logger.error(f'Inference error: {e}')
        INFERENCE_REQUESTS.labels(
            status='error',
            model_version=model_service.model_version,
            cache_hit='false'
        ).inc()

        return PredictResponse(
            success=False,
            error=str(e)
        )


@app.post('/batch/predict', response_model=BatchPredictResponse)
async def batch_predict(request: BatchPredictRequest):
    """Batch predictions."""
    predictions = []

    for req in request.requests:
        pred = await predict(req)
        predictions.append(pred)

    return BatchPredictResponse(
        success=True,
        predictions=predictions
    )


# gRPC server (for service-to-service communication)
def start_grpc_server():
    """Start gRPC server alongside FastAPI."""
    from concurrent import futures
    import grpc
    import inference_pb2
    import inference_pb2_grpc

    class InferenceServiceServicer(inference_pb2_grpc.InferenceServiceServicer):
        def Predict(self, request, context):
            try:
                symptoms = list(request.symptoms)
                result = model_service.predict(symptoms)
                precautions = get_precautions(result['disease'])

                return inference_pb2.PredictResponse(
                    success=True,
                    disease=result['disease'],
                    confidence=result['confidence'],
                    matched_symptoms=result['matched_symptoms'],
                    precautions=precautions,
                    model_version=model_service.model_version,
                    cache_hit=False
                )
            except Exception as e:
                context.set_details(str(e))
                context.set_code(grpc.StatusCode.INTERNAL)
                return inference_pb2.PredictResponse(success=False, error=str(e))

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    inference_pb2_grpc.add_InferenceServiceServicer_to_server(
        InferenceServiceServicer(), server
    )
    server.add_insecure_port('[::]:50053')
    server.start()
    logger.info('gRPC server started on port 50053')
    return server
```

- [ ] **Step 3: Create main entrypoint**

```python
# services/inference-service/main.py
#!/usr/bin/env python
"""
Inference Service Entrypoint

Runs FastAPI app and gRPC server.
"""

import uvicorn
import os
from api import start_grpc_server, app

if __name__ == '__main__':
    # Start gRPC server in background
    grpc_server = start_grpc_server()

    # Run FastAPI
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', 8004))

    print(f'Starting Inference Service on {host}:{port}')
    print(f'HTTP API: http://{host}:{port}')
    print(f'gRPC: {host}:50053')
    print(f'Metrics: http://{host}:{port}/metrics')

    uvicorn.run(app, host=host, port=port)
```

- [ ] **Step 4: Update Dockerfile**

```dockerfile
# services/inference-service/Dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
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
```

- [ ] **Step 5: Commit**

```bash
git add services/inference-service/
git commit -m "feat(inference): implement FastAPI inference service with MLflow"
```

---

### Task 4: A/B Testing Configuration

**Files:**
- Create: `services/inference-service/ab_testing.py`

- [ ] **Step 1: Create A/B testing module**

```python
# services/inference-service/ab_testing.py
"""
A/B Testing for Model Versions.

Routes traffic between champion and challenger models.
"""

import os
import random
from typing import Tuple
import logging

logger = logging.getLogger(__name__)


class ABTestRouter:
    """
    Routes inference requests between model versions.

    Configuration via environment variables:
    - AB_TEST_ENABLED: Enable/disable A/B testing
    - AB_TEST_CHAMPION_VERSION: Current production model version
    - AB_TEST_CHALLENGER_VERSION: Test model version
    - AB_TEST_CHALLENGER_TRAFFIC: Percentage of traffic to challenger (0-100)
    """

    def __init__(self):
        self.enabled = os.getenv('AB_TEST_ENABLED', 'false').lower() == 'true'
        self.champion_version = os.getenv('AB_TEST_CHAMPION_VERSION', 'v1.0')
        self.challenger_version = os.getenv('AB_TEST_CHALLENGER_VERSION', 'v2.0')
        self.challenger_traffic = int(os.getenv('AB_TEST_CHALLENGER_TRAFFIC', '10'))

        logger.info(
            f'A/B Testing: enabled={self.enabled}, '
            f'champion={self.champion_version}, challenger={self.challenger_version}, '
            f'challenger_traffic={self.challenger_traffic}%'
        )

    def get_model_version(self, patient_id: int = None) -> str:
        """
        Determine which model version to use.

        Args:
            patient_id: Optional patient ID for sticky routing

        Returns:
            Model version string
        """
        if not self.enabled:
            return self.champion_version

        # Sticky routing: same patient always gets same version
        if patient_id is not None:
            random.seed(patient_id)

        # Route to challenger based on traffic percentage
        if random.randint(1, 100) <= self.challenger_traffic:
            return self.challenger_version
        else:
            return self.champion_version

    def is_challenger(self, version: str) -> bool:
        """Check if a version is the challenger."""
        return version == self.challenger_version


# Global router
ab_router = ABTestRouter()


def get_model_version(patient_id: int = None) -> str:
    """Get model version for a request."""
    return ab_router.get_model_version(patient_id)
```

- [ ] **Step 2: Commit**

```bash
git add services/inference-service/ab_testing.py
git commit -m "feat(inference): add A/B testing router for model versions"
```

---

### Task 5: Update Docker Compose

**Files:**
- Modify: `docker/docker-compose.yml`

- [ ] **Step 1: Add inference service to docker-compose**

Read current file, modify the inference-service section:

```yaml
services:
  # ... existing services ...

  # Inference Service (FastAPI + gRPC)
  inference-service:
    build:
      context: ../services/inference-service
      dockerfile: Dockerfile
    container_name: medical_triage_inference
    ports:
      - "8004:8004"  # HTTP API
      - "50053:50053"  # gRPC
    environment:
      - MLFLOW_TRACKING_URI=http://mlflow:5000
      - REDIS_HOST=redis
      - REDIS_PORT=6379
      - AB_TEST_ENABLED=true
      - AB_TEST_CHAMPION_VERSION=v1.0
      - AB_TEST_CHALLENGER_VERSION=v2.0
      - AB_TEST_CHALLENGER_TRAFFIC=10
    volumes:
      - ../backend/ml_pipeline/models:/app/models
    depends_on:
      - mlflow
      - redis
    networks:
      - medical_triage_network
    restart: unless-stopped
    deploy:
      replicas: 2  # Scale inference service
```

- [ ] **Step 2: Commit**

```bash
git add docker/docker-compose.yml
git commit -m "infra: add inference service with A/B testing config"
```

---

### Task 6: Training Script with MLflow

**Files:**
- Create: `backend/ml_pipeline/train_with_mlflow.py`

- [ ] **Step 1: Create training script**

```python
#!/usr/bin/env python
"""
Training script with MLflow tracking.

Usage:
    python train_with_mlflow.py
"""

import os
import sys
import pandas as pd
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, f1_score, classification_report
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ml_pipeline.mlflow_tracking import get_mlflow_client, log_training_run


def load_data(data_path: str = 'data/Disease_symptom_and_patient_profile_dataset.csv'):
    """Load and preprocess training data."""
    logger.info(f'Loading data from {data_path}')

    df = pd.read_csv(data_path)

    # Preprocess
    symptom_columns = [col for col in df.columns if col.startswith('Symptom_')]
    X = df[symptom_columns]
    y = df['Disease']

    logger.info(f'Data shape: {X.shape}, Classes: {y.nunique()}')

    return X, y


def train_model(X, y, params: dict = None):
    """Train XGBoost model."""
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    logger.info(f'Train: {len(X_train)}, Test: {len(X_test)}')

    # Default params
    if params is None:
        params = {
            'n_estimators': 100,
            'max_depth': 6,
            'learning_rate': 0.1,
            'subsample': 0.8,
            'colsample_bytree': 0.8,
            'random_state': 42,
            'use_label_encoder': False,
            'eval_metric': 'mlogloss'
        }

    # Train
    model = xgb.XGBClassifier(**params)
    model.fit(X_train, y_train)

    # Evaluate
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred, average='weighted')

    logger.info(f'Accuracy: {accuracy:.4f}, F1: {f1:.4f}')
    logger.info(f'\n{classification_report(y_test, y_pred)}')

    return model, {
        'accuracy': accuracy,
        'f1_score': f1,
        'n_classes': len(y.unique())
    }


def main():
    """Main training function."""
    logger.info('Starting training with MLflow tracking')

    # Load data
    data_path = os.getenv('DATA_PATH', 'data/Disease_symptom_and_patient_profile_dataset.csv')
    X, y = load_data(data_path)

    # Training params
    params = {
        'n_estimators': int(os.getenv('N_ESTIMATORS', '100')),
        'max_depth': int(os.getenv('MAX_DEPTH', '6')),
        'learning_rate': float(os.getenv('LEARNING_RATE', '0.1')),
    }

    # Train and log to MLflow
    model, metrics = train_model(X, y, params)

    # Log to MLflow
    run_id = log_training_run(
        model=model,
        metrics=metrics,
        params=params,
        model_name='health-triage-classifier',
        run_name=f'training-{pd.Timestamp.now().strftime("%Y%m%d-%H%M%S")}'
    )

    logger.info(f'Training complete! MLflow Run ID: {run_id}')

    # Save model locally as fallback
    import joblib
    os.makedirs('models', exist_ok=True)
    joblib.dump(model, 'models/classifier.joblib')
    logger.info('Model saved to models/classifier.joblib')


if __name__ == '__main__':
    main()
```

- [ ] **Step 2: Commit**

```bash
git add backend/ml_pipeline/train_with_mlflow.py
git commit -m "feat(mlflow): add training script with MLflow tracking"
```

---

### Task 7: Testing & Verification

**Files:**
- Create: `scripts/test_inference_service.py`

- [ ] **Step 1: Create test script**

```python
#!/usr/bin/env python
"""Test Inference Service."""

import requests
import time
import json

BASE_URL = 'http://localhost:8004'


def test_health():
    """Test health endpoint."""
    print('\n=== Testing Health Endpoint ===')
    response = requests.get(f'{BASE_URL}/health')
    print(f'Status: {response.status_code}')
    print(f'Response: {response.json()}')


def test_model_status():
    """Test model status endpoint."""
    print('\n=== Testing Model Status ===')
    response = requests.get(f'{BASE_URL}/model/status')
    print(f'Status: {response.status_code}')
    print(f'Response: {json.dumps(response.json(), indent=2)}')


def test_predict():
    """Test prediction endpoint."""
    print('\n=== Testing Prediction ===')

    payload = {
        'symptoms': ['fever', 'headache', 'fatigue']
    }

    start = time.time()
    response = requests.post(f'{BASE_URL}/predict', json=payload)
    latency = (time.time() - start) * 1000

    print(f'Status: {response.status_code}')
    result = response.json()
    print(f'Disease: {result.get("disease")}')
    print(f'Confidence: {result.get("confidence", 0):.2%}')
    print(f'Latency: {latency:.2f}ms')
    print(f'Cache Hit: {result.get("cache_hit")}')


def test_cache():
    """Test caching (same request twice)."""
    print('\n=== Testing Caching ===')

    payload = {
        'symptoms': ['itching', 'skin_rash', 'fever']
    }

    # First request (cache miss)
    response1 = requests.post(f'{BASE_URL}/predict', json=payload)
    result1 = response1.json()

    # Second request (cache hit)
    response2 = requests.post(f'{BASE_URL}/predict', json=payload)
    result2 = response2.json()

    print(f'First request  - Cache Hit: {result1.get("cache_hit")}, Latency: {result1.get("latency_ms", 0):.2f}ms')
    print(f'Second request - Cache Hit: {result2.get("cache_hit")}, Latency: {result2.get("latency_ms", 0):.2f}ms')


def test_metrics():
    """Test Prometheus metrics."""
    print('\n=== Testing Metrics ===')
    response = requests.get(f'{BASE_URL}/metrics')
    metrics = response.text

    # Find inference metrics
    for line in metrics.split('\n'):
        if 'inference_' in line and not line.startswith('#'):
            print(line)


if __name__ == '__main__':
    print('Inference Service Tests')
    print('=' * 50)

    test_health()
    test_model_status()
    test_predict()
    test_cache()
    test_metrics()

    print('\n' + '=' * 50)
    print('Tests complete!')
```

- [ ] **Step 2: Run tests**

```bash
# Start all services
cd docker
docker-compose up -d inference-service mlflow redis

# Wait for services
sleep 15

# Run tests
cd ..
python scripts/test_inference_service.py
```

- [ ] **Step 3: Verify MLflow UI**

Open browser: `http://localhost:5000`

Check:
- Model registry shows `health-triage-classifier`
- Training runs are logged
- Model versions visible

- [ ] **Step 4: Commit**

```bash
git add scripts/test_inference_service.py
git commit -m "test(inference): add inference service test script"
```

---

## Success Criteria

- [ ] MLflow server starts and UI accessible at `localhost:5000`
- [ ] Inference service returns predictions via HTTP and gRPC
- [ ] Redis caching works (second request is faster)
- [ ] Prometheus metrics exposed at `/metrics`
- [ ] A/B testing routes traffic between versions
- [ ] Training script logs to MLflow
- [ ] Model can be loaded from MLflow registry
- [ ] All tests pass

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| MLflow won't start | Check SQLite permissions |
| Model not found | Verify model path or MLflow registry |
| Cache always miss | Check Redis connection |
| A/B not working | Set `AB_TEST_ENABLED=true` |
| Metrics empty | Make predictions first, then check `/metrics` |
