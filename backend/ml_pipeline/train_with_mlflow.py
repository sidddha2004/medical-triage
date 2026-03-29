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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ml_pipeline.mlflow_tracking import get_mlflow_client, log_training_run

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_data(data_path: str = 'data/Disease_symptom_and_patient_profile_dataset.csv'):
    logger.info(f'Loading data from {data_path}')
    df = pd.read_csv(data_path)
    symptom_columns = [col for col in df.columns if col.startswith('Symptom_')]
    X = df[symptom_columns]
    y = df['Disease']
    logger.info(f'Data shape: {X.shape}, Classes: {y.nunique()}')
    return X, y


def train_model(X, y, params: dict = None):
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    logger.info(f'Train: {len(X_train)}, Test: {len(X_test)}')

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

    model = xgb.XGBClassifier(**params)
    model.fit(X_train, y_train)

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
    logger.info('Starting training with MLflow tracking')

    data_path = os.getenv('DATA_PATH', 'data/Disease_symptom_and_patient_profile_dataset.csv')
    X, y = load_data(data_path)

    params = {
        'n_estimators': int(os.getenv('N_ESTIMATORS', '100')),
        'max_depth': int(os.getenv('MAX_DEPTH', '6')),
        'learning_rate': float(os.getenv('LEARNING_RATE', '0.1')),
    }

    model, metrics = train_model(X, y, params)

    run_id = log_training_run(
        model=model,
        metrics=metrics,
        params=params,
        model_name='health-triage-classifier',
        run_name=f'training-{pd.Timestamp.now().strftime("%Y%m%d-%H%M%S")}'
    )

    logger.info(f'Training complete! MLflow Run ID: {run_id}')

    import joblib
    os.makedirs('models', exist_ok=True)
    joblib.dump(model, 'models/classifier.joblib')
    logger.info('Model saved to models/classifier.joblib')


if __name__ == '__main__':
    main()
