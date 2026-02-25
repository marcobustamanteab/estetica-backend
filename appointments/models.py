# appointments/models.py
from django.db import models
from authentication.models import User, Business  # agregamos Business
from clients.models import Client
from services.models import Service


class Appointment(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pendiente'),
        ('confirmed', 'Confirmada'),
        ('cancelled', 'Cancelada'),
        ('completed', 'Completada'),
    )

    # Cada cita pertenece a un negocio
    # null=True para no romper los registros existentes
    business = models.ForeignKey(
        Business,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='appointments',
        verbose_name="Negocio"
    )

    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name='appointments',
        verbose_name="Cliente"
    )
    service = models.ForeignKey(
        Service,
        on_delete=models.CASCADE,
        related_name='appointments',
        verbose_name="Servicio"
    )
    employee = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='appointments',
        verbose_name="Empleado"
    )
    date = models.DateField(verbose_name="Fecha")
    start_time = models.TimeField(verbose_name="Hora de inicio")
    end_time = models.TimeField(verbose_name="Hora de fin")
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name="Estado"
    )
    notes = models.TextField(blank=True, null=True, verbose_name="Notas")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de creación")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Fecha de actualización")

    google_calendar_event_id = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text="ID del evento en Google Calendar"
    )

    class Meta:
        verbose_name = "Cita"
        verbose_name_plural = "Citas"
        ordering = ['date', 'start_time']
        constraints = [
            models.UniqueConstraint(
                fields=['employee', 'date', 'start_time'],
                name='unique_appointment'
            )
        ]

    def __str__(self):
        return f"Cita de {self.client} con {self.employee} - {self.date} {self.start_time}"

    def save(self, *args, **kwargs):
        # Calcula end_time automáticamente si no se proporciona
        if not self.end_time and self.service and self.start_time:
            from datetime import datetime, timedelta
            start_datetime = datetime.combine(datetime.today(), self.start_time)
            end_datetime = start_datetime + timedelta(minutes=self.service.duration)
            self.end_time = end_datetime.time()
        super().save(*args, **kwargs)