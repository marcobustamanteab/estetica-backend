# services/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ServiceCategoryViewSet, ServiceViewSet, RoleCategoryPermissionViewSet

router = DefaultRouter()
router.register(r'categories', ServiceCategoryViewSet)
router.register(r'role-categories', RoleCategoryPermissionViewSet)
router.register(r'', ServiceViewSet)

urlpatterns = [
    path('', include(router.urls)),
]