from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import Appointment
from services.google_calendar_service import GoogleCalendarService
import logging

# Configurar logging
logger = logging.getLogger(__name__)

@receiver(post_save, sender=Appointment)
def handle_appointment_created_updated(sender, instance, created, **kwargs):
    """
    Signal que se ejecuta cada vez que se guarda una cita
    """
    if created:
        # NUEVA CITA CREADA
        logger.info(f"🔔 Signal: Nueva cita creada - ID: {instance.id}")
        create_google_calendar_event(instance)
    else:
        # CITA ACTUALIZADA
        logger.info(f"🔔 Signal: Cita actualizada - ID: {instance.id}")
        update_google_calendar_event(instance)

def create_google_calendar_event(appointment):
    """
    Crear evento en Google Calendar para nueva cita
    """
    try:
        logger.info(f"📅 Intentando crear evento en Google Calendar para cita ID: {appointment.id}")
        
        # Verificar que el empleado tenga calendario configurado
        if not appointment.employee.google_calendar_id:
            logger.warning(f"⚠️ Empleado {appointment.employee.username} no tiene google_calendar_id")
            return
        
        # Crear servicio de Google Calendar
        calendar_service = GoogleCalendarService()
        
        # Crear evento
        event_id = calendar_service.create_appointment_event(appointment)
        
        if event_id:
            # Guardar el ID del evento en la cita
            appointment.google_calendar_event_id = event_id
            appointment.save(update_fields=['google_calendar_event_id'])
            
            logger.info(f"✅ Evento creado exitosamente en Google Calendar")
            logger.info(f"📅 Event ID: {event_id}")
            logger.info(f"👤 Empleado: {appointment.employee.get_full_name()}")
            logger.info(f"📧 Cliente: {appointment.client.get_full_name()}")
            
        else:
            logger.error(f"❌ No se pudo crear evento en Google Calendar")
            
    except Exception as e:
        logger.error(f"❌ Error creando evento en Google Calendar: {e}")
        # Imprimir traceback completo para debug
        import traceback
        logger.error(traceback.format_exc())

def update_google_calendar_event(appointment):
    """
    Actualizar evento en Google Calendar cuando cambia la cita
    """
    try:
        # Solo actualizar si ya tiene un evento creado
        if not appointment.google_calendar_event_id:
            logger.info(f"ℹ️ Cita ID: {appointment.id} no tiene evento en Google Calendar")
            return
        
        # Verificar si cambió el estado
        if hasattr(appointment, '_old_status') and appointment._old_status != appointment.status:
            logger.info(f"🔄 Estado cambió de {appointment._old_status} a {appointment.status}")
            
            calendar_service = GoogleCalendarService()
            
            success = calendar_service.update_appointment_event(
                appointment, 
                appointment.google_calendar_event_id
            )
            
            if success:
                logger.info(f"✅ Evento actualizado en Google Calendar")
            else:
                logger.error(f"❌ Error actualizando evento en Google Calendar")
                
    except Exception as e:
        logger.error(f"❌ Error actualizando evento: {e}")

@receiver(pre_save, sender=Appointment)
def store_old_status(sender, instance, **kwargs):
    """
    Guardar el estado anterior para detectar cambios
    """
    if instance.pk:
        try:
            old_instance = Appointment.objects.get(pk=instance.pk)
            instance._old_status = old_instance.status
        except Appointment.DoesNotExist:
            instance._old_status = None