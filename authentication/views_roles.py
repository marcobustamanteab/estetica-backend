# authentication/views_roles.py
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from django.contrib.auth.models import Group, Permission
from .serializers_roles import GroupSerializer, PermissionSerializer


class IsSuperAdmin(permissions.BasePermission):
    """
    Permiso personalizado: solo el superadmin puede crear/editar/eliminar roles.
    Los demás usuarios autenticados solo pueden leerlos (GET).
    """
    def has_permission(self, request, view):
        # Cualquier usuario autenticado puede leer (GET, HEAD, OPTIONS)
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated
        # Solo el superadmin puede crear/editar/eliminar
        return request.user and request.user.is_superuser


class GroupListCreateView(generics.ListCreateAPIView):
    """
    GET  → cualquier usuario autenticado puede ver los roles
    POST → solo el superadmin puede crear roles
    """
    queryset = Group.objects.prefetch_related('permissions').all()
    serializer_class = GroupSerializer
    permission_classes = [IsSuperAdmin]


class GroupRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    → cualquier usuario autenticado puede ver un rol
    PUT/PATCH/DELETE → solo el superadmin puede modificar/eliminar roles
    """
    queryset = Group.objects.prefetch_related('permissions').all()
    serializer_class = GroupSerializer
    permission_classes = [IsSuperAdmin]


class PermissionListView(generics.ListAPIView):
    """
    Solo el superadmin puede ver los permisos disponibles
    """
    queryset = Permission.objects.select_related('content_type').all()
    serializer_class = PermissionSerializer
    permission_classes = [permissions.IsAdminUser]


class GroupPermissionsUpdateView(generics.UpdateAPIView):
    """
    Solo el superadmin puede actualizar los permisos de un grupo
    """
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    permission_classes = [IsSuperAdmin]

    def update(self, request, *args, **kwargs):
        group = self.get_object()
        permission_ids = request.data.get('permissions', [])

        group.permissions.clear()

        if permission_ids:
            perms = Permission.objects.filter(id__in=permission_ids)
            group.permissions.add(*perms)

        return Response({'status': 'permissions updated'})