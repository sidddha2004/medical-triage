from django.urls import path, include
from rest_framework.routers import DefaultRouter
from api.views import PatientViewSet, TriageSessionViewSet, PredictionViewSet
from api.auth_views import RegisterView, LoginView

router = DefaultRouter()
router.register(r'patients', PatientViewSet, basename='patient')
router.register(r'sessions', TriageSessionViewSet, basename='session')
router.register(r'predictions', PredictionViewSet, basename='prediction')

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('', include(router.urls)),
]
