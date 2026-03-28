from django.db import models
from django.contrib.auth.models import User


class Patient(models.Model):
    """Patient profile linked to Django User."""

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='patient_profile')
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(
        max_length=20,
        choices=[
            ('male', 'Male'),
            ('female', 'Female'),
            ('other', 'Other'),
            ('prefer_not_to_say', 'Prefer not to say'),
        ],
        default='prefer_not_to_say'
    )
    blood_type = models.CharField(
        max_length=3,
        choices=[
            ('A+', 'A+'), ('A-', 'A-'),
            ('B+', 'B+'), ('B-', 'B-'),
            ('AB+', 'AB+'), ('AB-', 'AB-'),
            ('O+', 'O+'), ('O-', 'O-'),
        ],
        null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Patient: {self.user.email}"


class TriageSession(models.Model):
    """A triage assessment session."""

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('escalated', 'Escalated'),
    ]

    TRIAGE_LEVEL_CHOICES = [
        ('self_care', 'Self Care'),
        ('gp_visit', 'GP Visit'),
        ('urgent_care', 'Urgent Care'),
        ('emergency', 'Emergency'),
    ]

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='triage_sessions')
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    triage_level = models.CharField(
        max_length=20,
        choices=TRIAGE_LEVEL_CHOICES,
        null=True, blank=True
    )
    primary_symptoms = models.JSONField(default=list)
    notes = models.TextField(blank=True, default='')

    class Meta:
        ordering = ['-started_at']

    def __str__(self):
        return f"Session {self.id} - {self.patient.user.email} ({self.status})"


class Prediction(models.Model):
    """ML prediction for a triage session."""

    session = models.ForeignKey(TriageSession, on_delete=models.CASCADE, related_name='predictions')
    disease = models.CharField(max_length=200)
    confidence = models.FloatField()
    symptoms_analyzed = models.JSONField(default=list)
    model_version = models.CharField(max_length=50, default='v1.0')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Prediction: {self.disease} ({self.confidence:.2%})"


class AgentMessage(models.Model):
    """Chat message from AI agent in a triage session."""

    ROLE_CHOICES = [
        ('user', 'User'),
        ('agent', 'Agent'),
        ('system', 'System'),
    ]

    session = models.ForeignKey(TriageSession, on_delete=models.CASCADE, related_name='messages')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    content = models.TextField()
    tool_calls = models.JSONField(default=list, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"{self.role}: {self.content[:50]}..."
