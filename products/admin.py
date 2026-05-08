from django.contrib import admin
from .models import ProductCategory, Product, StockMovement


@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'business', 'is_active']
    list_filter = ['is_active', 'business']
    search_fields = ['name']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'sale_price', 'current_stock', 'min_stock', 'is_active']
    list_filter = ['is_active', 'category', 'business']
    search_fields = ['name']
    readonly_fields = ['current_stock', 'is_low_stock', 'created_at', 'updated_at']


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = ['product', 'quantity', 'movement_type', 'performed_by', 'created_at']
    list_filter = ['movement_type', 'created_at']
    search_fields = ['product__name', 'performed_by__username']
    readonly_fields = ['created_at']
