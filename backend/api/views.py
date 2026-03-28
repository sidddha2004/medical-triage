from rest_framework import viewsets, permissions, serializers, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth.models import User
from django.utils import timezone
from core.models import Patient, TriageSession, Prediction
from ml_pipeline.api import model_service


class PatientSerializer(serializers.ModelSerializer):
    """Serializer for Patient model."""

    email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = Patient
        fields = ['id', 'user', 'email', 'date_of_birth', 'gender', 'blood_type', 'created_at', 'updated_at']
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']


class PatientViewSet(viewsets.ModelViewSet):
    """ViewSet for Patient CRUD operations."""

    serializer_class = PatientSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Patient.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['get'])
    def me(self, request):
        """Get current user's patient profile."""
        try:
            patient = Patient.objects.get(user=request.user)
            serializer = self.get_serializer(patient)
            return Response(serializer.data)
        except Patient.DoesNotExist:
            return Response(
                {'detail': 'Patient profile not found. Create one first.'},
                status=status.HTTP_404_NOT_FOUND
            )


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

    @action(detail=True, methods=['post'])
    def end_session(self, request, pk=None):
        """End a triage session."""
        session = self.get_object()
        session.status = 'completed'
        session.ended_at = timezone.now()
        session.save()
        return Response({'status': 'session ended'})


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


class SymptomSubmissionSerializer(serializers.Serializer):
    """Serializer for symptom submission."""

    patient_id = serializers.IntegerField(required=False)
    symptoms = serializers.ListField(
        child=serializers.CharField(),
        required=True,
        help_text="List of symptoms (e.g., ['itching', 'fever', 'headache'])"
    )
    notes = serializers.CharField(required=False, allow_blank=True)


class SymptomAssessmentViewSet(viewsets.ViewSet):
    """
    ViewSet for symptom assessment.

    Combines symptom submission with ML prediction and creates
    a triage session with prediction.
    """

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = SymptomSubmissionSerializer

    def create(self, request):
        """
        Submit symptoms and get ML-based assessment.

        POST /api/symptom-assessment/
        {
            "patient_id": 1,  // optional, creates new if not provided
            "symptoms": ["itching", "skin_rash", "fever"],
            "notes": "Additional context"
        }

        Returns:
        {
            "session": {...},
            "prediction": {
                "disease": "Disease Name",
                "confidence": 0.95,
                "precautions": [...]
            },
            "triage_level": "self_care|urgent_care|emergency"
        }
        """
        serializer = SymptomSubmissionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        symptoms = serializer.validated_data['symptoms']
        notes = serializer.validated_data.get('notes', '')

        # Get or create patient
        patient_id = serializer.validated_data.get('patient_id')
        if patient_id:
            try:
                patient = Patient.objects.get(id=patient_id, user=request.user)
            except Patient.DoesNotExist:
                return Response(
                    {'error': 'Patient not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
        else:
            # Get or create patient profile for user
            patient, _ = Patient.objects.get_or_create(user=request.user)

        # Get ML prediction
        try:
            ml_result = model_service.predict(symptoms)
        except RuntimeError as e:
            return Response(
                {'error': 'ML model not available. Please train the model first.'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

        # Create triage session
        session = TriageSession.objects.create(
            patient=patient,
            status='completed',
            triage_level=self._get_triage_level(ml_result['disease']),
            primary_symptoms=symptoms,
            notes=notes
        )

        # Create prediction record
        prediction = Prediction.objects.create(
            session=session,
            disease=ml_result['disease'],
            confidence=ml_result['confidence'],
            symptoms_analyzed=ml_result['matched_symptoms'],
            model_version='v1.0'
        )

        return Response({
            'session': TriageSessionSerializer(session).data,
            'prediction': {
                'disease': ml_result['disease'],
                'confidence': ml_result['confidence'],
                'matched_symptoms': ml_result['matched_symptoms'],
                'precautions': ml_result['precautions'],
            },
            'triage_level': session.triage_level,
        })

    def _get_triage_level(self, disease: str) -> str:
        """Determine triage level based on disease."""

        emergency_keywords = ['hemorrhage', 'stroke', 'heart attack', 'paralysis']
        urgent_keywords = ['pneumonia', 'appendicitis', 'kidney', 'severe']

        disease_lower = disease.lower()

        for keyword in emergency_keywords:
            if keyword in disease_lower:
                return 'emergency'

        for keyword in urgent_keywords:
            if keyword in disease_lower:
                return 'urgent_care'

        return 'self_care'
