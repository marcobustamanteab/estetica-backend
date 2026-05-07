from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    CustomTokenObtainPairView,
    RegisterView,
    UserProfileView,
    UserListCreateView,
    UserRetrieveUpdateDestroyView,
    WorkScheduleView,
    WorkScheduleViewSet,
    public_employee_schedules,
)
from .views_roles import GroupListCreateView, GroupRetrieveUpdateDestroyView, PermissionListView, GroupPermissionsUpdateView
from .views_business import BusinessListView, BusinessDetailView

router = DefaultRouter()
router.register(r'schedules', WorkScheduleViewSet, basename='schedule')

urlpatterns = [
    # Autenticación JWT
    path('token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # Usuario
    path('register/', RegisterView.as_view(), name='register'),
    path('profile/', UserProfileView.as_view(), name='user_profile'),
    path('users/', UserListCreateView.as_view(), name='user-list-create'),
    path('users/<int:pk>/', UserRetrieveUpdateDestroyView.as_view(), name='user-detail'),

    path('businesses/', BusinessListView.as_view(), name='businesses'),
    path('businesses/me/', BusinessDetailView.as_view(), name='business-me'),
    path('businesses/<int:pk>/', BusinessDetailView.as_view(), name='business-detail'),

    # Horarios — GET legacy (usado por AppointmentFormModal)
    path('work-schedules/', WorkScheduleView.as_view(), name='work-schedules'),

    # Horarios — CRUD completo
    path('', include(router.urls)),

    # Grupos y permisos
    path('groups/', GroupListCreateView.as_view(), name='group-list-create'),
    path('groups/<int:pk>/', GroupRetrieveUpdateDestroyView.as_view(), name='group-detail'),
    path('permissions/', PermissionListView.as_view(), name='permission-list'),
    path('groups/<int:pk>/permissions/', GroupPermissionsUpdateView.as_view(), name='group-permissions-update'),

    # Endpoint público horarios empleado
    path('employees/<int:employee_id>/schedules/', public_employee_schedules, name='public-employee-schedules'),
]