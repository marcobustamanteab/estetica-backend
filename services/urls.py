# services/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ServiceCategoryViewSet, ServiceViewSet, RoleCategoryPermissionViewSet

router = DefaultRouter()
router.register(r'categories', ServiceCategoryViewSet)
router.register(r'', ServiceViewSet)
router.register(r'role-categories', RoleCategoryPermissionViewSet)

urlpatterns = [
    path('', include(router.urls)),
]