"""
ML Pipeline API - Symptom Prediction

Provides REST endpoints for disease prediction using trained ML model.
"""

import os
import json
from rest_framework import serializers, permissions, status, views
from rest_framework.response import Response

from .trainer import SymptomClassifier


class ModelService:
    """Singleton service for ML model."""

    _instance = None
    _model = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def get_model(self):
        """Load and return the trained model."""
        if self._model is None:
            self._model = SymptomClassifier()
            model_dir = os.path.join(os.path.dirname(__file__), '..', 'models')
            try:
                self._model.load(model_dir)
            except FileNotFoundError:
                raise RuntimeError("Model not found. Please train the model first.")
        return self._model

    def predict(self, symptoms: list):
        """Predict disease from symptoms."""
        model = self.get_model()
        return model.predict(symptoms)


model_service = ModelService()


class PredictionRequest(serializers.Serializer):
    """Serializer for prediction requests."""

    symptoms = serializers.ListField(
        child=serializers.CharField(),
        required=True,
        help_text="List of symptoms (e.g., ['itching', 'skin_rash', 'fever'])"
    )
    patient_age = serializers.IntegerField(required=False, allow_null=True)
    patient_gender = serializers.CharField(required=False, allow_null=True)


class SymptomPredictionView(views.APIView):
    """
    Predict disease from symptoms.

    POST /api/ml/predict/
    {
        "symptoms": ["itching", "skin_rash", "fever"]
    }

    Returns:
    {
        "disease": "Disease Name",
        "confidence": 0.95,
        "matched_symptoms": ["itching", "skin_rash"],
        "precautions": ["precaution 1", "precaution 2"]
    }
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = PredictionRequest(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        symptoms = serializer.validated_data['symptoms']

        try:
            result = model_service.predict(symptoms)

            # Determine triage level based on disease severity
            triage_level = self._get_triage_level(result['disease'])

            return Response({
                'disease': result['disease'],
                'confidence': result['confidence'],
                'matched_symptoms': result['matched_symptoms'],
                'precautions': result['precautions'],
                'triage_level': triage_level,
            })

        except RuntimeError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        except Exception as e:
            return Response(
                {'error': f'Prediction failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _get_triage_level(self, disease: str) -> str:
        """Determine triage level based on disease."""

        emergency_diseases = {
            'heart attack', 'stroke', 'seizure', 'unconscious',
            'chest pain', 'difficulty breathing'
        }

        urgent_diseases = {
            'pneumonia', 'appendicitis', 'fracture', 'high fever',
            'severe dehydration', 'kidney infection'
        }

        disease_lower = disease.lower()

        for emergency in emergency_diseases:
            if emergency in disease_lower:
                return 'emergency'

        for urgent in urgent_diseases:
            if urgent in disease_lower:
                return 'urgent_care'

        return 'self_care'


class ModelStatusView(views.APIView):
    """
    Check ML model status.

    GET /api/ml/status/

    Returns model metadata including:
    - Number of diseases
    - Number of symptoms
    - Model accuracy
    """

    permission_classes = [permissions.AllowAny]

    def get(self, request):
        model_dir = os.path.join(os.path.dirname(__file__), '..', 'models')
        metadata_path = os.path.join(model_dir, 'metadata.json')

        if not os.path.exists(metadata_path):
            return Response({
                'status': 'not_trained',
                'message': 'Model not found. Please train the model first.'
            })

        try:
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)

            return Response({
                'status': 'ready',
                'num_diseases': len(metadata.get('label_classes', [])),
                'num_symptoms': len(metadata.get('all_symptoms', [])),
            })

        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            })


class SymptomListApiView(views.APIView):
    """
    Get list of all known symptoms.

    GET /api/ml/symptoms/

    Returns list of symptoms the model recognizes.
    """

    permission_classes = [permissions.AllowAny]

    def get(self, request):
        model_dir = os.path.join(os.path.dirname(__file__), '..', 'models')
        metadata_path = os.path.join(model_dir, 'metadata.json')

        if not os.path.exists(metadata_path):
            return Response({
                'symptoms': [],
                'message': 'Model not trained yet'
            })

        try:
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)

            return Response({
                'symptoms': sorted(metadata.get('all_symptoms', []))
            })

        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DiseaseListApiView(views.APIView):
    """
    Get list of all known diseases.

    GET /api/ml/diseases/

    Returns list of diseases the model can predict.
    """

    permission_classes = [permissions.AllowAny]

    def get(self, request):
        model_dir = os.path.join(os.path.dirname(__file__), '..', 'models')
        metadata_path = os.path.join(model_dir, 'metadata.json')

        if not os.path.exists(metadata_path):
            return Response({
                'diseases': [],
                'message': 'Model not trained yet'
            })

        try:
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)

            return Response({
                'diseases': sorted(metadata.get('label_classes', []))
            })

        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
