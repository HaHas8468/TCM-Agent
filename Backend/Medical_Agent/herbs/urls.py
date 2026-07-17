from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import HerbViewSet, MeridianViewSet

router = DefaultRouter()
router.register(r'herbs', HerbViewSet)
router.register(r'meridians', MeridianViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
