from rest_framework import serializers
from .models import ProductCategory, Product, StockMovement


class ProductCategorySerializer(serializers.ModelSerializer):
    product_count = serializers.SerializerMethodField()

    class Meta:
        model = ProductCategory
        fields = ['id', 'name', 'description', 'is_active', 'product_count']

    def get_product_count(self, obj):
        return obj.products.filter(is_active=True).count()


class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.ReadOnlyField(source='category.name')
    current_stock = serializers.ReadOnlyField()
    is_low_stock = serializers.ReadOnlyField()

    class Meta:
        model = Product
        fields = [
            'id', 'business', 'category', 'category_name',
            'name', 'description', 'sale_price', 'cost_price',
            'min_stock', 'current_stock', 'is_low_stock',
            'is_active', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'business', 'created_at', 'updated_at']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['sale_price'] = float(instance.sale_price)
        if instance.cost_price is not None:
            data['cost_price'] = float(instance.cost_price)
        return data


class StockMovementSerializer(serializers.ModelSerializer):
    product_name = serializers.ReadOnlyField(source='product.name')
    performed_by_name = serializers.SerializerMethodField()
    movement_type_display = serializers.ReadOnlyField(source='get_movement_type_display')

    class Meta:
        model = StockMovement
        fields = [
            'id', 'product', 'product_name',
            'quantity', 'movement_type', 'movement_type_display',
            'unit_price', 'performed_by', 'performed_by_name',
            'appointment', 'notes', 'created_at',
        ]
        read_only_fields = ['id', 'performed_by', 'created_at']

    def get_performed_by_name(self, obj):
        if obj.performed_by:
            return f"{obj.performed_by.first_name} {obj.performed_by.last_name}".strip() or obj.performed_by.username
        return None

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if instance.unit_price is not None:
            data['unit_price'] = float(instance.unit_price)
        return data
