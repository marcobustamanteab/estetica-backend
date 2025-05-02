from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    CustomTokenObtainPairView, 
    RegisterView, 
    UserProfileView,
    UserListCreateView,
    UserRetrieveUpdateDestroyView
)
from .views_roles import GroupListCreateView, GroupRetrieveUpdateDestroyView, PermissionListView, GroupPermissionsUpdateView


urlpatterns = [
    # Endpoints de autenticación JWT
    path('token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # Endpoints de usuario
    path('register/', RegisterView.as_view(), name='register'),
    path('profile/', UserProfileView.as_view(), name='user_profile'),
    
    # Endpoints para gestión de usuarios
    path('users/', UserListCreateView.as_view(), name='user-list-create'),
    path('users/<int:pk>/', UserRetrieveUpdateDestroyView.as_view(), name='user-detail'),
    
    # Endpoints para gestión de grupos y permisos
    path('groups/', GroupListCreateView.as_view(), name='group-list-create'),
    path('groups/<int:pk>/', GroupRetrieveUpdateDestroyView.as_view(), name='group-detail'),
    path('permissions/', PermissionListView.as_view(), name='permission-list'),
    path('groups/<int:pk>/permissions/', GroupPermissionsUpdateView.as_view(), name='group-permissions-update'),
]

urlpatterns += [
    
]