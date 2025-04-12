# clients/admin.py
from django.contrib import admin
from .models import Client

@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('id', 'first_name', 'last_name', 'email', 'phone', 'is_active')
    list_filter = ('is_active', 'gender')
    search_fields = ('first_name', 'last_name', 'email', 'phone')
    date_hierarchy = 'created_at'