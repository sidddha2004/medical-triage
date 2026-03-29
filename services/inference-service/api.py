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

        if self.encoder:
            symptom_vector = self.encoder.transform([symptoms])
        else:
            symptom_vector = symptoms

        if hasattr(self.model, 'predict'):
            prediction = self.model.predict(symptom_vector)[0]
            if hasattr(self.model, 'predict_proba'):
                probabilities = self.model.predict_proba(symptom_vector)[0]
                confidence = float(max(probabilities))
            else:
                confidence = 1.0
        else:
            result = self.model.predict([symptoms])[0]
            prediction = result if isinstance(result, str) else str(result)
            confidence = 0.85

        return {
            'disease': prediction,
            'confidence': confidence,
            'matched_symptoms': symptoms
        }


model_service = ModelService()


def get_cache_key(symptoms: List[str]) -> str:
    sorted_symptoms = sorted(symptoms)
    key_str = '|'.join(sorted_symptoms)
    return hashlib.md5(key_str.encode()).hexdigest()


def get_precautions(disease: str) -> List[str]:
    precautions_map = {
        'Flu': ['Rest', 'Hydrate', 'Isolate from others'],
        'Migraine': ['Rest in dark room', 'Hydrate', 'Avoid bright lights'],
        'Common Cold': ['Rest', 'Hydrate', 'Over-the-counter medication'],
        'Allergy': ['Avoid allergens', 'Antihistamines', 'Monitor symptoms'],
    }
    return precautions_map.get(disease, ['Consult a healthcare provider'])


@app.get('/health')
async def health_check():
    return {
        'status': 'healthy',
        'model_loaded': model_service.model is not None,
        'model_version': model_service.model_version
    }


@app.get('/metrics')
async def metrics():
    return generate_latest(CONTENT_TYPE_LATEST)


@app.get('/model/status', response_model=ModelStatusResponse)
async def get_model_status():
    return ModelStatusResponse(
        loaded=model_service.model is not None,
        model_version=model_service.model_version,
        model_name=model_service.model_name,
        total_diseases=len(model_service.model.classes_) if hasattr(model_service.model, 'classes_') else 0,
        total_symptoms=len(model_service.encoder.categories_[0]) if hasattr(model_service.encoder, 'categories_') else 0,
        mlflow_uri=os.getenv('MLFLOW_TRACKING_URI', 'http://localhost:5000')
    )


@app.post('/predict', response_model=PredictResponse)
async def predict(request: PredictRequest):
    start_time = time.time()

    try:
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

        inference_result = model_service.predict(request.symptoms)
        precautions = get_precautions(inference_result['disease'])

        latency_ms = (time.time() - start_time) * 1000

        result_to_cache = {
            **inference_result,
            'precautions': precautions,
            'model_version': model_service.model_version
        }
        redis_client.setex(cache_key, 86400, json.dumps(result_to_cache))

        INFERENCE_REQUESTS.labels(
            status='success',
            model_version=model_service.model_version,
            cache_hit='false'
        ).inc()
        INFERENCE_LATENCY.labels(
            model_version=model_service.model_version
        ).observe(latency_ms / 1000)
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
    predictions = []
    for req in request.requests:
        pred = await predict(req)
        predictions.append(pred)

    return BatchPredictResponse(
        success=True,
        predictions=predictions
    )
