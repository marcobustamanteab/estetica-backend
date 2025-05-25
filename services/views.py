from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import ServiceCategory, Service, RoleCategoryPermission
from .serializers import ServiceCategorySerializer, ServiceSerializer, RoleCategoryPermissionSerializer
from django.contrib.auth.models import Group
from authentication.serializers import UserSerializer
from authentication.models import User
from django.contrib.auth import get_user_model

try:
    from authentication.serializers import UserSerializer
except ImportError:
    # Si no existe, crear uno básico
    from rest_framework import serializers
    
    User = get_user_model()
    
    class UserSerializer(serializers.ModelSerializer):
        groups = serializers.SerializerMethodField()
        
        class Meta:
            model = User
            fields = ('id', 'username', 'email', 'first_name', 'last_name', 'is_active', 'groups')
        
        def get_groups(self, obj):
            return [
                {'id': group.id, 'name': group.name}
                for group in obj.groups.all()
            ]

User = get_user_model()

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
            try:
                from django.contrib.auth import get_user_model
                User = get_user_model()
                
                try:
                    employee = User.objects.get(id=employee_id)
                    # Si el empleado es staff, puede ver todas las categorías
                    if not employee.is_staff:
                        # Obtener los roles del empleado
                        employee_roles = employee.groups.all()
                        
                        if employee_roles.exists():
                            # Verificar si hay permisos de categoría asignados
                            from django.db.models import Q
                            
                            # Primero verificar si hay alguna asignación en RoleCategoryPermission
                            if RoleCategoryPermission.objects.exists():
                                role_filter = Q()
                                for role in employee_roles:
                                    role_filter |= Q(allowed_roles__role=role)
                                queryset = queryset.filter(role_filter).distinct()
                            else:
                                # Si no hay asignaciones, mostrar todas las categorías (fallback)
                                # O decidir no mostrar ninguna, según tu lógica de negocio
                                pass
                        else:
                            # Si no tiene roles, no mostrar ninguna categoría
                            queryset = queryset.none()
                except User.DoesNotExist:
                    # Si el empleado no existe, no mostrar ninguna categoría
                    queryset = queryset.none()
            except Exception as e:
                # Log del error para depuración (usar logger, no print)
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error al filtrar categorías por empleado: {str(e)}")
                # Devolver todas las categorías como fallback
                pass
            
        return queryset
    
    @action(detail=True, methods=['post'])
    def assign_roles(self, request, pk=None):
        """
        Endpoint para asignar roles a una categoría específica
        """
        import logging
        logger = logging.getLogger(__name__)

        try:
            # Paso 1: Obtener la categoría
            category = self.get_object()
            logger.info(f"Asignando roles a categoría: {category.id} - {category.name}")
            
            # Paso 2: Obtener los IDs de rol proporcionados
            role_ids = request.data.get('roles', [])
            logger.info(f"Roles recibidos: {role_ids}")
            
            if not role_ids:
                return Response({"error": "No se proporcionaron roles"}, status=400)
            
            # Paso 3: Eliminar roles existentes de manera segura
            try:
                # En lugar de usar la relación, usar el modelo directamente
                existing_permissions = RoleCategoryPermission.objects.filter(category=category)
                logger.info(f"Eliminando {existing_permissions.count()} permisos existentes")
                existing_permissions.delete()
            except Exception as e:
                logger.error(f"Error al eliminar roles existentes: {str(e)}")
                return Response({"error": f"Error al eliminar roles existentes: {str(e)}"}, status=500)
            
            # Paso 4: Asignar nuevos roles
            successful_assignments = []
            failed_assignments = []
            
            for role_id in role_ids:
                try:
                    role = Group.objects.get(id=role_id)
                    logger.info(f"Asignando rol {role.id} - {role.name}")
                    
                    permission = RoleCategoryPermission.objects.create(
                        category=category,
                        role=role
                    )
                    successful_assignments.append(role.name)
                except Group.DoesNotExist:
                    logger.warning(f"El rol con ID {role_id} no existe")
                    failed_assignments.append(f"Rol ID {role_id} no existe")
                except Exception as e:
                    logger.error(f"Error al asignar rol {role_id}: {str(e)}")
                    failed_assignments.append(f"Error en rol {role_id}: {str(e)}")
            
            # Paso 5: Generar respuesta
            try:
                serializer = self.get_serializer(category)
                response_data = serializer.data
                
                # Añadir información sobre los roles asignados
                response_data['assigned_roles'] = successful_assignments
                if failed_assignments:
                    response_data['failed_assignments'] = failed_assignments
                
                return Response(response_data)
            except Exception as e:
                logger.error(f"Error al serializar respuesta: {str(e)}")
                
                # Devolver una respuesta básica en caso de error de serialización
                basic_response = {
                    "id": category.id,
                    "name": category.name,
                    "assigned_roles": successful_assignments
                }
                if failed_assignments:
                    basic_response['failed_assignments'] = failed_assignments
                    
                return Response(basic_response)
                
        except Exception as e:
            logger.error(f"Error general en assign_roles: {str(e)}")
            return Response({"error": f"Error interno del servidor: {str(e)}"}, status=500)

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

    @action(detail=True, methods=['get'])
    def employees(self, request, pk=None):
        """
        Obtener empleados que pueden realizar este servicio específico
        """
        try:
            service = self.get_object()
            category = service.category
            
            # Obtener roles permitidos para esta categoría
            allowed_roles = RoleCategoryPermission.objects.filter(
                category=category
            ).values_list('role_id', flat=True)
            
            if not allowed_roles:
                # Si no hay roles específicos asignados, devolver todos los usuarios activos
                users_with_roles = User.objects.filter(is_active=True)
            else:
                # Obtener empleados que tengan al menos uno de esos roles
                users_with_roles = User.objects.filter(
                    groups__in=allowed_roles, 
                    is_active=True
                ).distinct()
            
            serializer = UserSerializer(users_with_roles, many=True)
            return Response(serializer.data)
            
        except Service.DoesNotExist:
            return Response({'error': 'Servicio no encontrado'}, status=404)
        except Exception as e:
            return Response({'error': str(e)}, status=500)

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