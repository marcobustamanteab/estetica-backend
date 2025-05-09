from rest_framework import serializers
from .models import ServiceCategory, Service, RoleCategoryPermission

class ServiceCategorySerializer(serializers.ModelSerializer):
    allowed_roles = serializers.SerializerMethodField()
    roles = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False
    )
    
    class Meta:
        model = ServiceCategory
        fields = ['id', 'name', 'description', 'is_active', 'allowed_roles', 'roles']
    
    def get_allowed_roles(self, obj):
        try:
            role_permissions = RoleCategoryPermission.objects.filter(category=obj)
            return [{'id': rp.role.id, 'name': rp.role.name} for rp in role_permissions]
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error al obtener roles para categoría {obj.id}: {str(e)}")
            return []
    
    def create(self, validated_data):
        # Extraer los roles antes de crear la categoría
        roles = validated_data.pop('roles', [])
        
        # Crear la categoría
        category = super().create(validated_data)
        
        # Asignar roles si se proporcionaron
        if roles:
            self._assign_roles(category, roles)
        
        return category
    
    def update(self, instance, validated_data):
        # Extraer los roles antes de actualizar la categoría
        roles = validated_data.pop('roles', [])
        
        # Actualizar la categoría
        category = super().update(instance, validated_data)
        
        # Asignar roles si se proporcionaron
        if roles:
            self._assign_roles(category, roles)
        
        return category
    
    def _assign_roles(self, category, role_ids):
        try:
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"Asignando roles {role_ids} a categoría {category.id}")
            
            # Eliminar roles existentes
            RoleCategoryPermission.objects.filter(category=category).delete()
            
            # Asignar nuevos roles
            for role_id in role_ids:
                try:
                    from django.contrib.auth.models import Group
                    role = Group.objects.get(id=role_id)
                    RoleCategoryPermission.objects.create(
                        category=category,
                        role=role
                    )
                    logger.info(f"Rol {role.id} asignado correctamente")
                except Group.DoesNotExist:
                    logger.warning(f"Rol {role_id} no existe")
                except Exception as e:
                    logger.error(f"Error al asignar rol {role_id}: {str(e)}")
        except Exception as e:
            logger.error(f"Error general al asignar roles: {str(e)}")

class ServiceSerializer(serializers.ModelSerializer):
    category_name = serializers.ReadOnlyField(source='category.name')
    
    class Meta:
        model = Service
        fields = '__all__'
        
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        # Formatear el precio para mostrar 2 decimales
        representation['price'] = float(instance.price)
        return representation

class RoleCategoryPermissionSerializer(serializers.ModelSerializer):
    role_name = serializers.ReadOnlyField(source='role.name')
    category_name = serializers.ReadOnlyField(source='category.name')
    
    class Meta:
        model = RoleCategoryPermission
        fields = ['id', 'role', 'role_name', 'category', 'category_name']