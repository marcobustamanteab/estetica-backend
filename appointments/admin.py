# appointments/admin.py
from django.contrib import admin
from .models import Appointment

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'client', 'service', 'employee', 'date', 'start_time', 'end_time', 'status')
    list_filter = ('status', 'date', 'employee', 'service')
    search_fields = ('client__first_name', 'client__last_name', 'employee__username', 'notes')
    date_hierarchy = 'date'
    ordering = ('-date', 'start_time')