from rest_framework import serializers
from .models import Appointment
from authentication.models import User
from clients.models import Client
from services.models import Service

class AppointmentSerializer(serializers.ModelSerializer):
    client_name = serializers.ReadOnlyField(source='client.get_full_name')
    service_name = serializers.ReadOnlyField(source='service.name')
    employee_name = serializers.ReadOnlyField(source='employee.get_full_name')
    service_duration = serializers.ReadOnlyField(source='service.duration')
    
    class Meta:
        model = Appointment
        fields = '__all__'
    
    def validate(self, data):
        """
        Realizar validaciones personalizadas:
        - Verificar que la hora de inicio sea anterior a la hora de fin
        - Verificar que no haya citas solapadas para el mismo empleado
        """
        if 'start_time' in data and 'end_time' in data:
            if data['start_time'] >= data['end_time']:
                raise serializers.ValidationError({"end_time": "La hora de fin debe ser posterior a la hora de inicio"})
        
        # Verificar solapamiento de citas
        employee = data.get('employee')
        date = data.get('date')
        start_time = data.get('start_time')
        end_time = data.get('end_time')
        
        if employee and date and start_time and end_time:
            # Excluir la cita actual en caso de actualización
            appointment_id = self.instance.id if self.instance else None
            
            overlapping_appointments = Appointment.objects.filter(
                employee=employee,
                date=date,
                status__in=['pending', 'confirmed']  # Solo verificar citas pendientes o confirmadas
            ).exclude(id=appointment_id)
            
            # Verificar si hay solapamiento con otras citas
            for appointment in overlapping_appointments:
                if (start_time < appointment.end_time and end_time > appointment.start_time):
                    raise serializers.ValidationError({
                        "non_field_errors": [
                            f"Esta cita se solapa con otra existente para {employee} de {appointment.start_time} a {appointment.end_time}"
                        ]
                    })
        
        return data

# Serializer para el calendario
class CalendarAppointmentSerializer(serializers.ModelSerializer):
    client_name = serializers.ReadOnlyField(source='client.get_full_name')
    service_name = serializers.ReadOnlyField(source='service.name')
    employee_name = serializers.ReadOnlyField(source='employee.get_full_name')
    
    class Meta:
        model = Appointment
        fields = ('id', 'client', 'client_name', 'service', 'service_name', 
                  'employee', 'employee_name', 'date', 'start_time', 'end_time', 'status')