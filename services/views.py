# services/views.py
import logging
from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import ServiceCategory, Service, RoleCategoryPermission
from .serializers import ServiceCategorySerializer, ServiceSerializer, RoleCategoryPermissionSerializer
from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model
from authentication.models import User

try:
    from authentication.serializers import UserSerializer
except ImportError:
    from rest_framework import serializers
    User = get_user_model()

    class UserSerializer(serializers.ModelSerializer):
        groups = serializers.SerializerMethodField()

        class Meta:
            model = User
            fields = ('id', 'username', 'email', 'first_name', 'last_name', 'is_active', 'groups')

        def get_groups(self, obj):
            return [{'id': group.id, 'name': group.name} for group in obj.groups.all()]

User = get_user_model()
logger = logging.getLogger(__name__)


class ServiceCategoryViewSet(viewsets.ModelViewSet):
    """
    API endpoint para categorías de servicios.
    Cada usuario solo ve las categorías de su propio negocio.
    """
    queryset = ServiceCategory.objects.all()
    serializer_class = ServiceCategorySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        if user.is_superuser:
            queryset = ServiceCategory.objects.all()
        elif not user.business:
            return ServiceCategory.objects.none()
        else:
            queryset = ServiceCategory.objects.filter(business=user.business)

        is_active = self.request.query_params.get('is_active', None)
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')

        employee_id = self.request.query_params.get('employee_id', None)
        if employee_id:
            try:
                employee = User.objects.get(id=employee_id)
                if not employee.is_staff:
                    employee_roles = employee.groups.all()
                    if employee_roles.exists():
                        if RoleCategoryPermission.objects.exists():
                            from django.db.models import Q
                            role_filter = Q()
                            for role in employee_roles:
                                role_filter |= Q(allowed_roles__role=role)
                            queryset = queryset.filter(role_filter).distinct()
                    else:
                        queryset = queryset.none()
            except User.DoesNotExist:
                queryset = queryset.none()
            except Exception as e:
                logger.error(f"Error al filtrar categorías por empleado: {str(e)}")

        return queryset

    def perform_create(self, serializer):
        business = self.request.user.business
        if not business:
            from rest_framework.exceptions import ValidationError
            raise ValidationError("Tu usuario no tiene un negocio asignado. Contacta al administrador.")
        serializer.save(business=business)

    @action(detail=True, methods=['post'])
    def assign_roles(self, request, pk=None):
        """
        Asigna roles a una categoría específica
        """
        try:
            category = ServiceCategory.objects.get(pk=pk)
            logger.info(f"Asignando roles a categoría: {category.id} - {category.name}")

            role_ids = request.data.get('roles', [])
            if not role_ids:
                return Response({"error": "No se proporcionaron roles"}, status=400)

            # Eliminar roles existentes
            RoleCategoryPermission.objects.filter(category=category).delete()

            # Asignar nuevos roles
            successful_assignments = []
            failed_assignments = []

            for role_id in role_ids:
                try:
                    role = Group.objects.get(id=role_id)
                    RoleCategoryPermission.objects.create(category=category, role=role)
                    successful_assignments.append(role.name)
                except Group.DoesNotExist:
                    failed_assignments.append(f"Rol ID {role_id} no existe")
                except Exception as e:
                    failed_assignments.append(f"Error en rol {role_id}: {str(e)}")

            try:
                serializer = self.get_serializer(category)
                response_data = serializer.data
                response_data['assigned_roles'] = successful_assignments
                if failed_assignments:
                    response_data['failed_assignments'] = failed_assignments
                return Response(response_data)
            except Exception as e:
                logger.error(f"Error al serializar respuesta: {str(e)}")
                return Response({
                    "id": category.id,
                    "name": category.name,
                    "assigned_roles": successful_assignments
                })

        except Exception as e:
            logger.error(f"Error general en assign_roles: {str(e)}")
            return Response({"error": f"Error interno del servidor: {str(e)}"}, status=500)


class ServiceViewSet(viewsets.ModelViewSet):
    """
    API endpoint para servicios.
    Cada usuario solo ve los servicios de su propio negocio.
    """
    queryset = Service.objects.all()
    serializer_class = ServiceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        if user.is_superuser:
            queryset = Service.objects.all()
        elif not user.business:
            return Service.objects.none()
        else:
            queryset = Service.objects.filter(business=user.business)

        is_active = self.request.query_params.get('is_active', None)
        if is_active is not None:
            is_active = is_active.lower() == 'true'
            if is_active:
                queryset = queryset.filter(is_active=True, category__is_active=True)
            else:
                queryset = queryset.filter(is_active=False)

        category = self.request.query_params.get('category', None)
        if category is not None:
            queryset = queryset.filter(category_id=category)

        return queryset.order_by('-category__is_active', 'category__name', 'name')

    def perform_create(self, serializer):
        business = self.request.user.business
        if not business:
            from rest_framework.exceptions import ValidationError
            raise ValidationError("Tu usuario no tiene un negocio asignado.")
        serializer.save(business=business)

    @action(detail=False, methods=['get'])
    def available_for_appointments(self, request):
        user = request.user

        if user.is_superuser:
            queryset = Service.objects.filter(
                is_active=True,
                category__is_active=True
            )
        elif not user.business:
            return Response([])
        else:
            queryset = Service.objects.filter(
                business=user.business,
                is_active=True,
                category__is_active=True
            )

        queryset = queryset.order_by('category__name', 'name')
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def employees(self, request, pk=None):
        """
        Empleados del mismo negocio que pueden realizar este servicio
        """
        try:
            service = self.get_object()
            category = service.category

            allowed_roles = RoleCategoryPermission.objects.filter(
                category=category
            ).values_list('role_id', flat=True)

            if not allowed_roles:
                # Sin restricción de roles: todos los empleados activos del negocio
                users_with_roles = User.objects.filter(
                    business=request.user.business,
                    is_active=True
                )
            else:
                # Solo empleados con los roles permitidos, del mismo negocio
                users_with_roles = User.objects.filter(
                    business=request.user.business,
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
    API endpoint para permisos de categorías por rol
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