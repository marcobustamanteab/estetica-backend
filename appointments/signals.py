# appointments/signals.py

import threading
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
from django.core.mail import send_mail
from django.template.loader import render_to_string
    

# Configurar logging
logger = logging.getLogger(__name__)

@receiver(post_save, sender=Appointment)
def handle_appointment_created_updated(sender, instance, created, **kwargs):
    if created:
        logger.info(f"🔔 Signal: Nueva cita creada - ID: {instance.id}")
        # Ejecutar en background para no bloquear el request
        thread = threading.Thread(
            target=run_background_tasks,
            args=(instance,),
            daemon=True
        )
        thread.start()
    else:
        logger.info(f"🔔 Signal: Cita actualizada - ID: {instance.id}")
        update_google_calendar_event(instance)

def run_background_tasks(appointment):
    """Ejecutar tareas lentas en background"""
    create_google_calendar_event(appointment)
    send_confirmation_email(appointment)

def format_chilean_price(price):
    """Formatear precio al estilo chileno"""
    try:
        price_int = int(float(price))
        formatted = f"{price_int:,}".replace(',', '.')
        return f"${formatted}"
    except:
        return f"${price}"

def format_date_spanish(date):
    """Formatear fecha en español"""
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
    dia_esp = dias_semana.get(date.strftime('%A'), date.strftime('%A'))
    mes_esp = meses.get(date.strftime('%B'), date.strftime('%B'))
    return f"{dia_esp}, {date.day} de {mes_esp} de {date.year}"


def send_confirmation_email(appointment):
    """
    Enviar email de confirmación al cliente cuando se agenda una cita
    """
    try:
        import resend
        client_email = appointment.client.email
        if not client_email:
            logger.warning(f"⚠️ Cliente {appointment.client.get_full_name()} no tiene email")
            return

        resend.api_key = os.environ.get('RESEND_API_KEY')
        business_name = appointment.business.name if appointment.business else os.environ.get('BUSINESS_NAME', 'BeautyCare')
        precio_formateado = format_chilean_price(appointment.service.price)
        fecha_esp = format_date_spanish(appointment.date)
        hora_esp = appointment.start_time.strftime('%H:%M')
        cancellation_policy = os.environ.get('CANCELLATION_POLICY', '24 horas de anticipación')

        subject = f"✅ Confirmación de tu cita en {business_name}"

        html_message = f"""
<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f9fafb;">
    <div style="background-color: #0d9488; padding: 20px; border-radius: 8px 8px 0 0; text-align: center;">
        <h1 style="color: white; margin: 0; font-size: 24px;">{business_name}</h1>
    </div>
    <div style="background-color: white; padding: 30px; border-radius: 0 0 8px 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
        <h2 style="color: #0d9488; margin-top: 0;">✅ ¡Tu cita está confirmada!</h2>
        <p style="color: #374151;">Hola <strong>{appointment.client.first_name}</strong>,</p>
        <p style="color: #374151;">Tu cita ha sido agendada exitosamente. Aquí están los detalles:</p>
        <div style="background-color: #f0fdfa; border-left: 4px solid #0d9488; padding: 16px; border-radius: 4px; margin: 20px 0;">
            <table style="width: 100%; border-collapse: collapse;">
                <tr><td style="padding: 6px 0; color: #6b7280; width: 140px;">📅 Fecha</td><td style="padding: 6px 0; color: #111827; font-weight: bold;">{fecha_esp}</td></tr>
                <tr><td style="padding: 6px 0; color: #6b7280;">🕐 Hora</td><td style="padding: 6px 0; color: #111827; font-weight: bold;">{hora_esp}</td></tr>
                <tr><td style="padding: 6px 0; color: #6b7280;">✂️ Servicio</td><td style="padding: 6px 0; color: #111827; font-weight: bold;">{appointment.service.name}</td></tr>
                <tr><td style="padding: 6px 0; color: #6b7280;">👩‍💼 Barbero/a</td><td style="padding: 6px 0; color: #111827; font-weight: bold;">{appointment.employee.get_full_name()}</td></tr>
                <tr><td style="padding: 6px 0; color: #6b7280;">💰 Precio</td><td style="padding: 6px 0; color: #111827; font-weight: bold;">{precio_formateado}</td></tr>
            </table>
        </div>
        <div style="background-color: #fefce8; border: 1px solid #fde68a; padding: 12px 16px; border-radius: 4px; margin: 16px 0;">
            <p style="margin: 0; color: #92400e; font-size: 14px;">
                💡 <strong>Recordatorios:</strong><br>
                • Llega 10 minutos antes de tu cita<br>
                • Cancelaciones con {cancellation_policy}
            </p>
        </div>
        <p style="color: #6b7280; font-size: 14px; margin-top: 24px;">
            ¡Te esperamos! ✨<br>
            <strong>{business_name}</strong>
        </p>
    </div>
</div>
"""

        params = {
            "from": f"{business_name} <no-reply@devsign.cl>",
            "to": [client_email],
            "subject": subject,
            "html": html_message,
        }

        resend.Emails.send(params)
        logger.info(f"✅ Email de confirmación enviado a {client_email}")

    except Exception as e:
        logger.error(f"❌ Error enviando email de confirmación: {e}")
        import traceback
        logger.error(traceback.format_exc())


def create_google_calendar_event(appointment):
    """
    Crear evento en Google Calendar para nueva cita
    """
    try:
        logger.info(f"📅 Intentando crear evento en Google Calendar para cita ID: {appointment.id}")
        
        if not appointment.employee.google_calendar_id:
            logger.info(f"⚠️ Empleado {appointment.employee.username} no tiene calendar_id, creando automáticamente...")
            
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
        
        calendar_service = GoogleCalendarService()
        event_id = calendar_service.create_appointment_event(appointment)
        
        if event_id:
            appointment.google_calendar_event_id = event_id
            appointment.save(update_fields=['google_calendar_event_id'])
            logger.info(f"✅ Evento creado exitosamente en Google Calendar")
        else:
            logger.error(f"❌ No se pudo crear evento en Google Calendar")
        
        send_zapier_webhook_new_appointment(appointment)
            
    except Exception as e:
        logger.error(f"❌ Error creando evento en Google Calendar: {e}")
        import traceback
        logger.error(traceback.format_exc())

def update_google_calendar_event(appointment):
    """
    Actualizar evento en Google Calendar cuando cambia la cita
    """
    try:
        if not appointment.google_calendar_event_id:
            logger.info(f"ℹ️ Cita ID: {appointment.id} no tiene evento en Google Calendar")
            return
        
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
    
    webhook_url = os.environ.get('ZAPIER_NEW_APPOINTMENT_WEBHOOK')
    
    print(f"🔍 DEBUGGING:")
    print(f"   webhook_url encontrada: {webhook_url is not None}")
    
    if not webhook_url:
        print("❌ ZAPIER_NEW_APPOINTMENT_WEBHOOK no configurado")
        return
    
    client_phone = appointment.client.phone or ""
    clean_phone = ''.join(filter(str.isdigit, client_phone))
    
    if clean_phone and not clean_phone.startswith('56'):
        clean_phone = '56' + clean_phone
    
    payload = {
        'event': 'nueva_cita',
        'appointment_id': appointment.id,
        'client': {
            'name': appointment.client.get_full_name(),
            'first_name': appointment.client.first_name,
            'email': appointment.client.email,
            'phone': clean_phone,
            'phone_display': appointment.client.phone,
        },
        'service': {
            'name': appointment.service.name,
            'price': float(appointment.service.price),
            'duration': appointment.service.duration,
            'category': appointment.service.category.name if appointment.service.category else 'Sin categoría',
        },
        'employee': {
            'name': appointment.employee.get_full_name(),
            'first_name': appointment.employee.first_name,
            'email': appointment.employee.email,
        },
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
        'whatsapp_message_client': generate_client_whatsapp_message(appointment),
        'whatsapp_message_admin': generate_admin_whatsapp_message(appointment),
        'whatsapp_message_reminder': generate_reminder_message(appointment),
        'timestamp': appointment.created_at.isoformat(),
        'source': 'admin_panel',
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
    precio_formateado = format_chilean_price(appointment.service.price)
    business_name = os.environ.get('BUSINESS_NAME', 'Centro de Estética')
    arrival_time = os.environ.get('ARRIVAL_TIME', '10 minutos antes')
    cancellation_policy = os.environ.get('CANCELLATION_POLICY', '24 horas de anticipación')
    
    fecha_esp = format_date_spanish(appointment.date)
    hora_esp = appointment.start_time.strftime('%I:%M %p')
    
    message = f"""🌟 ¡Hola {appointment.client.first_name}!

✅ Tu cita ha sido confirmada en {business_name}.

📋 DETALLES DE TU CITA:

📅 Fecha: {fecha_esp}
🕐 Hora: {hora_esp}
💅 Servicio: {appointment.service.name}
👩‍💼 Especialista: {appointment.employee.get_full_name()}
💰 Precio: {precio_formateado}

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

def handle_appointment_updated(appointment):
    """Manejar actualizaciones de cita"""
    if hasattr(appointment, '_old_status') and appointment._old_status != appointment.status:
        send_zapier_webhook_status_changed(appointment)

def send_zapier_webhook_status_changed(appointment):
    """Enviar webhook cuando cambia el estado de una cita"""
    
    webhook_url = getattr(settings, 'ZAPIER_STATUS_CHANGE_WEBHOOK', None)
    
    if not webhook_url:
        return
    
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
    
    business_name = os.environ.get('BUSINESS_NAME', 'Centro de Estética')
    arrival_time = os.environ.get('ARRIVAL_TIME', '10 minutos antes')
    business_phone = os.environ.get('BUSINESS_PHONE', '+56 9 1234 5678')
    
    fecha_esp = format_date_spanish(appointment.date)
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