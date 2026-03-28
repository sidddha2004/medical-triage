from rest_framework import viewsets, permissions, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth.models import User
from core.models import Patient, TriageSession, Prediction


class PatientSerializer(serializers.ModelSerializer):
    """Serializer for Patient model."""

    class Meta:
        model = Patient
        fields = ['id', 'user', 'date_of_birth', 'gender', 'blood_type', 'created_at', 'updated_at']
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']


class PatientViewSet(viewsets.ModelViewSet):
    """ViewSet for Patient CRUD operations."""

    serializer_class = PatientSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Patient.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class TriageSessionSerializer(serializers.ModelSerializer):
    """Serializer for TriageSession model."""

    class Meta:
        model = TriageSession
        fields = [
            'id', 'patient', 'started_at', 'ended_at', 'status',
            'triage_level', 'primary_symptoms', 'notes'
        ]
        read_only_fields = ['id', 'started_at', 'ended_at']


class TriageSessionViewSet(viewsets.ModelViewSet):
    """ViewSet for TriageSession CRUD operations."""

    serializer_class = TriageSessionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        patient_id = self.request.query_params.get('patient_id')
        if patient_id:
            return TriageSession.objects.filter(patient_id=patient_id)
        return TriageSession.objects.filter(patient__user=self.request.user)

    def perform_create(self, serializer):
        serializer.save()


class PredictionSerializer(serializers.ModelSerializer):
    """Serializer for Prediction model."""

    class Meta:
        model = Prediction
        fields = [
            'id', 'session', 'disease', 'confidence',
            'symptoms_analyzed', 'model_version', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class PredictionViewSet(viewsets.ModelViewSet):
    """ViewSet for Prediction CRUD operations."""

    serializer_class = PredictionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        session_id = self.request.query_params.get('session_id')
        if session_id:
            return Prediction.objects.filter(session_id=session_id)
        return Prediction.objects.filter(session__patient__user=self.request.user)

    def perform_create(self, serializer):
        serializer.save()
