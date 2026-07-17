from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SymptomViewSet, TongueSignViewSet, PulseSignViewSet, \
    ZhengTypeViewSet, DiagnosisQuestionViewSet, DiagnosisViewSet

router = DefaultRouter()
router.register(r'symptoms', SymptomViewSet)
router.register(r'tongue-signs', TongueSignViewSet)
router.register(r'pulse-signs', PulseSignViewSet)
router.register(r'zheng-types', ZhengTypeViewSet)
router.register(r'questions', DiagnosisQuestionViewSet)
router.register(r'diagnosis', DiagnosisViewSet, basename='diagnosis')

urlpatterns = [
    path('', include(router.urls)),
]
