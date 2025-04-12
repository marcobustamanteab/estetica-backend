from rest_framework import serializers
from .models import ServiceCategory, Service

class ServiceCategorySerializer(serializers.ModelSerializer):
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