from rest_framework import serializers
from .models import ServiceCategory, Service, RoleCategoryPermission

class ServiceCategorySerializer(serializers.ModelSerializer):
    allowed_roles = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    
    class Meta:
        model = ServiceCategory
        fields = '__all__'

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