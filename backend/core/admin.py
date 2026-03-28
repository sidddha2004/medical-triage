from django.contrib import admin
from .models import Patient, TriageSession, Prediction, AgentMessage


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ['user', 'date_of_birth', 'gender', 'blood_type', 'created_at']
    list_filter = ['gender', 'blood_type', 'created_at']
    search_fields = ['user__email', 'user__username']
    raw_id_fields = ['user']


@admin.register(TriageSession)
class TriageSessionAdmin(admin.ModelAdmin):
    list_display = ['id', 'patient', 'status', 'triage_level', 'started_at', 'ended_at']
    list_filter = ['status', 'triage_level', 'started_at']
    search_fields = ['patient__user__email', 'notes']
    raw_id_fields = ['patient']
    readonly_fields = ['started_at']


@admin.register(Prediction)
class PredictionAdmin(admin.ModelAdmin):
    list_display = ['id', 'session', 'disease', 'confidence', 'model_version', 'created_at']
    list_filter = ['disease', 'model_version', 'created_at']
    search_fields = ['session__id', 'disease']
    raw_id_fields = ['session']
    readonly_fields = ['created_at']


@admin.register(AgentMessage)
class AgentMessageAdmin(admin.ModelAdmin):
    list_display = ['id', 'session', 'role', 'timestamp', 'content_preview']
    list_filter = ['role', 'timestamp']
    search_fields = ['session__id', 'content']
    raw_id_fields = ['session']
    readonly_fields = ['timestamp']

    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Content'
