from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import ServiceCategory, Service, RoleCategoryPermission
from .serializers import ServiceCategorySerializer, ServiceSerializer, RoleCategoryPermissionSerializer
from django.contrib.auth.models import Group

class ServiceCategoryViewSet(viewsets.ModelViewSet):
    """
    API endpoint para categorías de servicios
    """
    queryset = ServiceCategory.objects.all()
    serializer_class = ServiceCategorySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = ServiceCategory.objects.all()
        is_active = self.request.query_params.get('is_active', None)
        employee_id = self.request.query_params.get('employee_id', None)
        
        if is_active is not None:
            is_active = is_active.lower() == 'true'
            queryset = queryset.filter(is_active=is_active)
        
        # Filtrar categorías por rol del empleado
        if employee_id:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            
            try:
                employee = User.objects.get(id=employee_id)
                # Si el empleado es staff, puede ver todas las categorías
                if not employee.is_staff:
                    # Obtener los roles del empleado
                    employee_roles = employee.groups.all()
                    # Filtrar categorías permitidas para esos roles
                    if employee_roles.exists():
                        from django.db.models import Q
                        role_filter = Q()
                        for role in employee_roles:
                            role_filter |= Q(allowed_roles__role=role)
                        queryset = queryset.filter(role_filter).distinct()
                    else:
                        # Si no tiene roles, no mostrar ninguna categoría
                        queryset = queryset.none()
            except User.DoesNotExist:
                # Si el empleado no existe, no mostrar ninguna categoría
                queryset = queryset.none()
            
        return queryset
    
    @action(detail=True, methods=['post'])
    def assign_roles(self, request, pk=None):
        """
        Endpoint para asignar roles a una categoría específica
        """
        category = self.get_object()
        role_ids = request.data.get('roles', [])
        
        if not role_ids:
            return Response({"error": "No se proporcionaron roles"}, status=400)
        
        # Eliminar roles existentes
        category.allowed_roles.all().delete()
        
        # Asignar nuevos roles
        for role_id in role_ids:
            try:
                role = Group.objects.get(id=role_id)
                RoleCategoryPermission.objects.create(
                    category=category,
                    role=role
                )
            except Group.DoesNotExist:
                pass  # Ignorar roles que no existen
        
        serializer = self.get_serializer(category)
        return Response(serializer.data)

class ServiceViewSet(viewsets.ModelViewSet):
    """
    API endpoint para servicios
    """
    queryset = Service.objects.all()
    serializer_class = ServiceSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = Service.objects.all()
        is_active = self.request.query_params.get('is_active', None)
        category = self.request.query_params.get('category', None)
        
        if is_active is not None:
            is_active = is_active.lower() == 'true'
            
            if is_active:
                queryset = queryset.filter(
                    is_active=True,
                    category__is_active=True 
                )
            else:
                queryset = queryset.filter(is_active=False)
            
        if category is not None:
            queryset = queryset.filter(category_id=category)
            
        queryset = queryset.order_by('-category__is_active', 'category__name', 'name')
            
        return queryset

    @action(detail=False, methods=['get'])
    def available_for_appointments(self, request):
        """
        Endpoint especial para obtener solo servicios disponibles para citas
        Requiere que tanto el servicio como su categoría estén activos
        """
        queryset = Service.objects.filter(
            is_active=True,
            category__is_active=True
        ).order_by('category__name', 'name')
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

class RoleCategoryPermissionViewSet(viewsets.ModelViewSet):
    """
    API endpoint para asignar categorías a roles
    """
    queryset = RoleCategoryPermission.objects.all()
    serializer_class = RoleCategoryPermissionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = RoleCategoryPermission.objects.all()
        role_id = self.request.query_params.get('role', None)
        category_id = self.request.query_params.get('category', None)
        
        if role_id:
            queryset = queryset.filter(role_id=role_id)
        if category_id:
            queryset = queryset.filter(category_id=category_id)
            
        return queryset