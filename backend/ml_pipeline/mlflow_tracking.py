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
            latest_version = self.get_latest_model_version(model_name)
            if latest_version:
                model_uri = f'models:/{model_name}/{latest_version}'
            else:
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
