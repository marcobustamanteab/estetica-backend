from rest_framework import serializers
from .models import ServiceCategory, Service, RoleCategoryPermission

class ServiceCategorySerializer(serializers.ModelSerializer):
    allowed_roles = serializers.SerializerMethodField()
    
    class Meta:
        model = ServiceCategory
        fields = ['id', 'name', 'description', 'is_active', 'allowed_roles']
    
    def get_allowed_roles(self, obj):
        # Obtener todos los permisos de rol para esta categoría
        role_permissions = RoleCategoryPermission.objects.filter(category=obj)
        
        # Registrar para depuración
        print(f"Roles para categoría {obj.name}: {[rp.role.name for rp in role_permissions]}")
        
        # Devolver la lista de roles
        return [
            {'id': rp.role.id, 'name': rp.role.name}
            for rp in role_permissions
        ]

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