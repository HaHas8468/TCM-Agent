from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import FormulaViewSet

router = DefaultRouter()
router.register(r'formulas', FormulaViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
