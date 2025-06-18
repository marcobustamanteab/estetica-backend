# appointments/signals.py

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import Appointment
from services.google_calendar_service import GoogleCalendarService
import logging
import requests
from django.conf import settings
import json
import os
from datetime import datetime
import locale
    

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
        
        # NUEVO: Verificar y crear calendario automáticamente si no existe
        if not appointment.employee.google_calendar_id:
            logger.info(f"⚠️ Empleado {appointment.employee.username} no tiene calendar_id, creando automáticamente...")
            
            # Crear calendario automáticamente
            calendar_service = GoogleCalendarService()
            calendar_id = calendar_service.create_employee_calendar(
                appointment.employee.get_full_name(),
                appointment.employee.email
            )
            
            if calendar_id:
                appointment.employee.google_calendar_id = calendar_id
                appointment.employee.save(update_fields=['google_calendar_id'])
                logger.info(f"✅ Calendario creado automáticamente para {appointment.employee.get_full_name()}")
            else:
                logger.error(f"❌ No se pudo crear calendario automáticamente")
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
        
        send_zapier_webhook_new_appointment(appointment)
            
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
            

# Whatsapp Zapier
def send_zapier_webhook_new_appointment(appointment):
    """
    Enviar webhook a Zapier cuando se crea nueva cita
    """
    import os
    
    # Usar os.environ en lugar de settings
    webhook_url = os.environ.get('ZAPIER_NEW_APPOINTMENT_WEBHOOK')
    
    print(f"🔍 DEBUGGING:")
    print(f"   webhook_url encontrada: {webhook_url is not None}")
    
    if not webhook_url:
        print("❌ ZAPIER_NEW_APPOINTMENT_WEBHOOK no configurado")
        return
    
    # Formatear teléfono para WhatsApp (agregar código país si no lo tiene)
    client_phone = appointment.client.phone or ""
    clean_phone = ''.join(filter(str.isdigit, client_phone))
    
    # Agregar código de Chile (+56) si no lo tiene
    if clean_phone and not clean_phone.startswith('56'):
        clean_phone = '56' + clean_phone
    
    # Datos para Zapier
    payload = {
        'event': 'nueva_cita',
        'appointment_id': appointment.id,
        
        # Datos del cliente
        'client': {
            'name': appointment.client.get_full_name(),
            'first_name': appointment.client.first_name,
            'email': appointment.client.email,
            'phone': clean_phone,
            'phone_display': appointment.client.phone,
        },
        
        # Datos del servicio
        'service': {
            'name': appointment.service.name,
            'price': float(appointment.service.price),
            'duration': appointment.service.duration,
            'category': appointment.service.category.name if appointment.service.category else 'Sin categoría',
        },
        
        # Datos del empleado
        'employee': {
            'name': appointment.employee.get_full_name(),
            'first_name': appointment.employee.first_name,
            'email': appointment.employee.email,
        },
        
        # Datos de la cita
        'appointment': {
            'date': appointment.date.strftime('%Y-%m-%d'),
            'date_formatted': appointment.date.strftime('%A, %d de %B de %Y'),
            'start_time': appointment.start_time.strftime('%H:%M'),
            'start_time_formatted': appointment.start_time.strftime('%I:%M %p'),
            'end_time': appointment.end_time.strftime('%H:%M'),
            'status': appointment.status,
            'status_display': appointment.get_status_display(),
            'notes': appointment.notes or '',
        },
        
        # Mensaje pre-formateado para WhatsApp (opcional)
        'whatsapp_message_client': generate_client_whatsapp_message(appointment),
        'whatsapp_message_admin': generate_admin_whatsapp_message(appointment),
        'whatsapp_message_reminder': generate_reminder_message(appointment),
        
        # Metadatos
        'timestamp': appointment.created_at.isoformat(),
        'source': 'admin_panel',  # vs 'public_link' en el futuro
    }
    
    try:
        response = requests.post(
            webhook_url,
            json=payload,
            timeout=10,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            logger.info(f"✅ Webhook enviado exitosamente a Zapier")
        else:
            logger.warning(f"⚠️ Webhook enviado pero respuesta: {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Error enviando webhook a Zapier: {e}")

def generate_client_whatsapp_message(appointment):
    """Generar mensaje de WhatsApp para el cliente"""
    # Variables personalizables
    business_name = os.environ.get('BUSINESS_NAME', 'Centro de Estética')
    arrival_time = os.environ.get('ARRIVAL_TIME', '10 minutos antes')
    cancellation_policy = os.environ.get('CANCELLATION_POLICY', '24 horas de anticipación')
    
    # FORMATEAR FECHA EN ESPAÑOL
    dias_semana = {
        'Monday': 'Lunes',
        'Tuesday': 'Martes', 
        'Wednesday': 'Miércoles',
        'Thursday': 'Jueves',
        'Friday': 'Viernes',
        'Saturday': 'Sábado',
        'Sunday': 'Domingo'
    }
    
    meses = {
        'January': 'Enero', 'February': 'Febrero', 'March': 'Marzo',
        'April': 'Abril', 'May': 'Mayo', 'June': 'Junio',
        'July': 'Julio', 'August': 'Agosto', 'September': 'Septiembre',
        'October': 'Octubre', 'November': 'Noviembre', 'December': 'Diciembre'
    }
    
    # Obtener día de la semana y mes en inglés
    dia_ingles = appointment.date.strftime('%A')
    mes_ingles = appointment.date.strftime('%B')
    
    # Convertir a español
    dia_esp = dias_semana.get(dia_ingles, dia_ingles)
    mes_esp = meses.get(mes_ingles, mes_ingles)
    
    # Formatear fecha completa en español
    fecha_esp = f"{dia_esp}, {appointment.date.day} de {mes_esp} de {appointment.date.year}"
    hora_esp = appointment.start_time.strftime('%I:%M %p')
    
    message = f"""🌟 ¡Hola {appointment.client.first_name}!

✅ Tu cita ha sido confirmada en {business_name}.

📋 DETALLES DE TU CITA:

📅 Fecha: {fecha_esp}
🕐 Hora: {hora_esp}
💅 Servicio: {appointment.service.name}
👩‍💼 Especialista: {appointment.employee.get_full_name()}
💰 Precio: ${appointment.service.price}

💡 RECORDATORIOS:
- Llega {arrival_time}
- Cancelaciones con {cancellation_policy}

¿Preguntas? ¡Responde a este mensaje!

¡Te esperamos! ✨"""
    
    return message

def generate_admin_whatsapp_message(appointment):
    """Generar mensaje de WhatsApp para el administrador"""
    
    message = f"""🔔 NUEVA CITA AGENDADA

👤 Cliente: {appointment.client.get_full_name()}
📱 Teléfono: {appointment.client.phone or 'No especificado'}
📧 Email: {appointment.client.email}

📅 Fecha: {appointment.date.strftime('%d/%m/%Y')}
🕐 Hora: {appointment.start_time.strftime('%H:%M')} - {appointment.end_time.strftime('%H:%M')}
💅 Servicio: {appointment.service.name} (${appointment.service.price})
👩‍💼 Especialista: {appointment.employee.get_full_name()}

📝 Notas: {appointment.notes or 'Sin notas'}

⏰ Agendada: {appointment.created_at.strftime('%d/%m/%Y %H:%M')}

💻 Ver en sistema: https://devsign.cl/"""
    
    return message

# Para manejar cambios de estado también
def handle_appointment_updated(appointment):
    """Manejar actualizaciones de cita"""
    
    # Si cambió el estado, enviar webhook de cambio
    if hasattr(appointment, '_old_status') and appointment._old_status != appointment.status:
        send_zapier_webhook_status_changed(appointment)

def send_zapier_webhook_status_changed(appointment):
    """Enviar webhook cuando cambia el estado de una cita"""
    
    webhook_url = getattr(settings, 'ZAPIER_STATUS_CHANGE_WEBHOOK', None)
    
    if not webhook_url:
        return
    
    # Solo para cambios importantes
    important_statuses = ['confirmed', 'cancelled', 'completed']
    if appointment.status not in important_statuses:
        return
    
    payload = {
        'event': 'cambio_estado_cita',
        'appointment_id': appointment.id,
        'client': {
            'name': appointment.client.get_full_name(),
            'first_name': appointment.client.first_name,
            'phone': appointment.client.phone,
        },
        'appointment': {
            'date_formatted': appointment.date.strftime('%d/%m/%Y'),
            'start_time_formatted': appointment.start_time.strftime('%I:%M %p'),
            'service_name': appointment.service.name,
            'employee_name': appointment.employee.get_full_name(),
            'new_status': appointment.status,
            'new_status_display': appointment.get_status_display(),
            'old_status': getattr(appointment, '_old_status', None),
        },
        'whatsapp_message': generate_status_change_message(appointment),
        'timestamp': appointment.updated_at.isoformat()
    }
    
    try:
        requests.post(webhook_url, json=payload, timeout=10)
        logger.info(f"✅ Webhook de cambio de estado enviado")
    except:
        logger.error(f"❌ Error enviando webhook de cambio de estado")

def generate_status_change_message(appointment):
    """Generar mensaje para cambio de estado"""
    
    status_emojis = {
        'confirmed': '✅',
        'cancelled': '❌',
        'completed': '🎉'
    }
    
    status_messages = {
        'confirmed': 'Tu cita ha sido CONFIRMADA',
        'cancelled': 'Tu cita ha sido CANCELADA',
        'completed': '¡Tu cita ha sido COMPLETADA!'
    }
    
    emoji = status_emojis.get(appointment.status, '📝')
    status_text = status_messages.get(appointment.status, f'Estado actualizado: {appointment.get_status_display()}')
    
    message = f"""{emoji} ¡Hola {appointment.client.first_name}!

{status_text}

📋 Detalles:
📅 Fecha: {appointment.date.strftime('%d/%m/%Y')}
🕐 Hora: {appointment.start_time.strftime('%I:%M %p')}
💅 Servicio: {appointment.service.name}

¡Gracias por preferirnos! ✨"""
    
    return message

def generate_reminder_message(appointment):
    """Generar mensaje de recordatorio para el día de la cita"""
    import os
    
    # Variables personalizables
    business_name = os.environ.get('BUSINESS_NAME', 'Centro de Estética')
    arrival_time = os.environ.get('ARRIVAL_TIME', '10 minutos antes')
    business_phone = os.environ.get('BUSINESS_PHONE', '+56 9 1234 5678')
    
    # FORMATEAR FECHA EN ESPAÑOL
    dias_semana = {
        'Monday': 'Lunes', 'Tuesday': 'Martes', 'Wednesday': 'Miércoles',
        'Thursday': 'Jueves', 'Friday': 'Viernes', 'Saturday': 'Sábado', 'Sunday': 'Domingo'
    }
    
    meses = {
        'January': 'Enero', 'February': 'Febrero', 'March': 'Marzo',
        'April': 'Abril', 'May': 'Mayo', 'June': 'Junio',
        'July': 'Julio', 'August': 'Agosto', 'September': 'Septiembre',
        'October': 'Octubre', 'November': 'Noviembre', 'December': 'Diciembre'
    }
    
    # Convertir fecha
    dia_ingles = appointment.date.strftime('%A')
    mes_ingles = appointment.date.strftime('%B')
    dia_esp = dias_semana.get(dia_ingles, dia_ingles)
    mes_esp = meses.get(mes_ingles, mes_ingles)
    
    fecha_esp = f"{dia_esp}, {appointment.date.day} de {mes_esp} de {appointment.date.year}"
    hora_esp = appointment.start_time.strftime('%I:%M %p')
    
    message = f"""🔔 ¡Hola {appointment.client.first_name}!

📅 RECORDATORIO: Tu cita es HOY

🕐 Hora: {hora_esp} - {fecha_esp}
💅 Servicio: {appointment.service.name}
👩‍💼 Con: {appointment.employee.get_full_name()}
📍 En: {business_name}

💡 RECORDATORIOS IMPORTANTES:
- Llega {arrival_time}
- Trae tu identificación
- Si tienes algún inconveniente, llámanos: {business_phone}

¡Te esperamos! ✨"""
    
    return message