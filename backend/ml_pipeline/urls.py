from django.urls import path
from ml_pipeline.api import SymptomPredictionView, ModelStatusView, SymptomListApiView, DiseaseListApiView

urlpatterns = [
    path('predict/', SymptomPredictionView.as_view(), name='predict'),
    path('status/', ModelStatusView.as_view(), name='model-status'),
    path('symptoms/', SymptomListApiView.as_view(), name='symptom-list'),
    path('diseases/', DiseaseListApiView.as_view(), name='disease-list'),
]
