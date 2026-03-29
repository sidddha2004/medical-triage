from django.urls import path, include
from rest_framework.routers import DefaultRouter
from api.views import PatientViewSet, TriageSessionViewSet, PredictionViewSet, SymptomAssessmentViewSet
from api.auth_views import RegisterView, LoginView

router = DefaultRouter()
router.register(r'patients', PatientViewSet, basename='patient')
router.register(r'sessions', TriageSessionViewSet, basename='session')
router.register(r'predictions', PredictionViewSet, basename='prediction')
router.register(r'symptom-assessment', SymptomAssessmentViewSet, basename='symptom-assessment')

urlpatterns = [
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('auth/login/', LoginView.as_view(), name='login'),
    path('', include(router.urls)),
]
