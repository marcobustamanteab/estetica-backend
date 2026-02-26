# appointments/management/commands/send_appointment_reminders.py

from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings
from datetime import date, timedelta
import os
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Enviar recordatorios por email a clientes con citas mañana'

    def handle(self, *args, **options):
        from appointments.models import Appointment

        tomorrow = date.today() + timedelta(days=1)
        
        appointments = Appointment.objects.filter(
            date=tomorrow,
            status__in=['pending', 'confirmed']
        ).select_related('client', 'service', 'employee')

        self.stdout.write(f"📅 Citas para mañana ({tomorrow}): {appointments.count()}")

        sent = 0
        errors = 0

        for appointment in appointments:
            try:
                client_email = appointment.client.email
                if not client_email:
                    self.stdout.write(f"⚠️ Cliente {appointment.client.get_full_name()} sin email")
                    continue

                business_name = os.environ.get('BUSINESS_NAME', 'BeautyCare')
                
                # Formatear fecha en español
                dias = {
                    'Monday': 'Lunes', 'Tuesday': 'Martes', 'Wednesday': 'Miércoles',
                    'Thursday': 'Jueves', 'Friday': 'Viernes', 'Saturday': 'Sábado', 'Sunday': 'Domingo'
                }
                meses = {
                    'January': 'Enero', 'February': 'Febrero', 'March': 'Marzo',
                    'April': 'Abril', 'May': 'Mayo', 'June': 'Junio',
                    'July': 'Julio', 'August': 'Agosto', 'September': 'Septiembre',
                    'October': 'Octubre', 'November': 'Noviembre', 'December': 'Diciembre'
                }
                dia_esp = dias.get(appointment.date.strftime('%A'), appointment.date.strftime('%A'))
                mes_esp = meses.get(appointment.date.strftime('%B'), appointment.date.strftime('%B'))
                fecha_esp = f"{dia_esp}, {appointment.date.day} de {mes_esp} de {appointment.date.year}"
                hora_esp = appointment.start_time.strftime('%H:%M')

                precio_int = int(float(appointment.service.price))
                precio_fmt = f"${precio_int:,}".replace(',', '.')

                subject = f"🔔 Recordatorio: Tu cita es mañana en {business_name}"

                message = f"""Hola {appointment.client.first_name},

Te recordamos que tienes una cita mañana en {business_name}.

DETALLES DE TU CITA:
📅 Fecha: {fecha_esp}
🕐 Hora: {hora_esp}
💅 Servicio: {appointment.service.name}
👩‍💼 Especialista: {appointment.employee.get_full_name()}
💰 Precio: {precio_fmt}

Recuerda llegar 10 minutos antes.
Si necesitas cancelar, hazlo con anticipación.

¡Te esperamos!
{business_name}
"""

                html_message = f"""
<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f9fafb;">
    <div style="background-color: #0d9488; padding: 20px; border-radius: 8px 8px 0 0; text-align: center;">
        <h1 style="color: white; margin: 0; font-size: 24px;">{business_name}</h1>
    </div>
    
    <div style="background-color: white; padding: 30px; border-radius: 0 0 8px 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
        <h2 style="color: #0d9488; margin-top: 0;">🔔 Recordatorio de tu cita</h2>
        <p style="color: #374151;">Hola <strong>{appointment.client.first_name}</strong>,</p>
        <p style="color: #374151;">Te recordamos que tienes una cita <strong>mañana</strong>:</p>
        
        <div style="background-color: #f0fdfa; border-left: 4px solid #0d9488; padding: 16px; border-radius: 4px; margin: 20px 0;">
            <table style="width: 100%; border-collapse: collapse;">
                <tr>
                    <td style="padding: 6px 0; color: #6b7280; width: 140px;">📅 Fecha</td>
                    <td style="padding: 6px 0; color: #111827; font-weight: bold;">{fecha_esp}</td>
                </tr>
                <tr>
                    <td style="padding: 6px 0; color: #6b7280;">🕐 Hora</td>
                    <td style="padding: 6px 0; color: #111827; font-weight: bold;">{hora_esp}</td>
                </tr>
                <tr>
                    <td style="padding: 6px 0; color: #6b7280;">💅 Servicio</td>
                    <td style="padding: 6px 0; color: #111827; font-weight: bold;">{appointment.service.name}</td>
                </tr>
                <tr>
                    <td style="padding: 6px 0; color: #6b7280;">👩‍💼 Especialista</td>
                    <td style="padding: 6px 0; color: #111827; font-weight: bold;">{appointment.employee.get_full_name()}</td>
                </tr>
                <tr>
                    <td style="padding: 6px 0; color: #6b7280;">💰 Precio</td>
                    <td style="padding: 6px 0; color: #111827; font-weight: bold;">{precio_fmt}</td>
                </tr>
            </table>
        </div>
        
        <div style="background-color: #fefce8; border: 1px solid #fde68a; padding: 12px 16px; border-radius: 4px; margin: 16px 0;">
            <p style="margin: 0; color: #92400e; font-size: 14px;">
                💡 Recuerda llegar <strong>10 minutos antes</strong> de tu cita.<br>
                Si necesitas cancelar, por favor avisa con anticipación.
            </p>
        </div>
        
        <p style="color: #6b7280; font-size: 14px; margin-top: 24px;">
            ¡Te esperamos! ✨<br>
            <strong>{business_name}</strong>
        </p>
    </div>
</div>
"""

                send_mail(
                    subject=subject,
                    message=message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[client_email],
                    html_message=html_message,
                    fail_silently=False,
                )

                sent += 1
                self.stdout.write(self.style.SUCCESS(f"✅ Recordatorio enviado a {client_email}"))

            except Exception as e:
                errors += 1
                self.stdout.write(self.style.ERROR(f"❌ Error con cita {appointment.id}: {e}"))
                logger.error(f"Error enviando recordatorio cita {appointment.id}: {e}")

        self.stdout.write(f"\n📊 Resumen: {sent} enviados, {errors} errores")