from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MedicalRecordViewSet, DiseaseViewSet

router = DefaultRouter()
router.register(r'records', MedicalRecordViewSet)
router.register(r'diseases', DiseaseViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
