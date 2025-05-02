from rest_framework import generics, permissions, status
from rest_framework.response import Response
from django.contrib.auth.models import Group, Permission
from .serializers_roles import GroupSerializer, PermissionSerializer

class GroupListCreateView(generics.ListCreateAPIView):
    """
    Vista para listar todos los grupos y crear nuevos
    Accesible para usuarios autenticados
    """
    # Solo hacemos prefetch_related con 'permissions', eliminamos 'user_set'
    queryset = Group.objects.prefetch_related('permissions').all()
    serializer_class = GroupSerializer
    permission_classes = [permissions.IsAuthenticated]

class GroupRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    """
    Vista para ver, actualizar o eliminar grupos específicos
    Accesible para usuarios autenticados
    """
    # Solo hacemos prefetch_related con 'permissions', eliminamos 'user_set'
    queryset = Group.objects.prefetch_related('permissions').all()
    serializer_class = GroupSerializer
    permission_classes = [permissions.IsAuthenticated]

class PermissionListView(generics.ListAPIView):
    """
    Vista para listar todos los permisos disponibles
    Accesible para usuarios autenticados
    """
    queryset = Permission.objects.select_related('content_type').all()
    serializer_class = PermissionSerializer
    permission_classes = [permissions.IsAuthenticated]

class GroupPermissionsUpdateView(generics.UpdateAPIView):
    """
    Vista para actualizar los permisos de un grupo
    Accesible para usuarios autenticados
    """
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def update(self, request, *args, **kwargs):
        group = self.get_object()
        permission_ids = request.data.get('permissions', [])
        
        # Limpiar todos los permisos existentes
        group.permissions.clear()
        
        # Añadir los nuevos permisos
        if permission_ids:
            permissions = Permission.objects.filter(id__in=permission_ids)
            group.permissions.add(*permissions)
        
        return Response({'status': 'permissions updated'})