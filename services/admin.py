from django.contrib import admin
from .models import ServiceCategory, Service, RoleCategoryPermission

@admin.register(ServiceCategory)
class ServiceCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active')
    search_fields = ('name',)
    list_filter = ('is_active',)

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'duration', 'is_active')
    list_filter = ('category', 'is_active')
    search_fields = ('name', 'description')
    list_editable = ('price', 'is_active')

@admin.register(RoleCategoryPermission)
class RoleCategoryPermissionAdmin(admin.ModelAdmin):
    list_display = ('category', 'role')
    list_filter = ('category', 'role')
    search_fields = ('category__name', 'role__name')