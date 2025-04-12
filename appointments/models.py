from django.db import models
from authentication.models import User
from clients.models import Client
from services.models import Service

class Appointment(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pendiente'),
        ('confirmed', 'Confirmada'),
        ('cancelled', 'Cancelada'),
        ('completed', 'Completada'),
    )
    
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='appointments', verbose_name="Cliente")
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='appointments', verbose_name="Servicio")
    employee = models.ForeignKey(User, on_delete=models.CASCADE, related_name='appointments', verbose_name="Empleado")
    date = models.DateField(verbose_name="Fecha")
    start_time = models.TimeField(verbose_name="Hora de inicio")
    end_time = models.TimeField(verbose_name="Hora de fin")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="Estado")
    notes = models.TextField(blank=True, null=True, verbose_name="Notas")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de creación")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Fecha de actualización")
    
    class Meta:
        verbose_name = "Cita"
        verbose_name_plural = "Citas"
        ordering = ['date', 'start_time']
        # Asegurar que no se solapen las citas para un mismo empleado
        constraints = [
            models.UniqueConstraint(
                fields=['employee', 'date', 'start_time'],
                name='unique_appointment'
            )
        ]
    
    def __str__(self):
        return f"Cita de {self.client} con {self.employee} - {self.date} {self.start_time}"
    
    def save(self, *args, **kwargs):
        # Puedes implementar lógica adicional aquí
        # Por ejemplo, calcular end_time basado en la duración del servicio si no se proporciona
        if not self.end_time and self.service and self.start_time:
            # Convertir start_time a datetime para poder sumar
            from datetime import datetime, timedelta
            start_datetime = datetime.combine(datetime.today(), self.start_time)
            # Sumar la duración del servicio
            end_datetime = start_datetime + timedelta(minutes=self.service.duration)
            # Obtener solo el tiempo
            self.end_time = end_datetime.time()
        
        super().save(*args, **kwargs)