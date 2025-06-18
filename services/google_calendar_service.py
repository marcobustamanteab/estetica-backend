# services/google_calendar_service.py - VERSIÓN COMPLETA

import os
import json
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from django.conf import settings
from datetime import datetime, timedelta
import pytz

class GoogleCalendarService:
    def __init__(self):
        # Cargar credenciales desde variable de entorno
        credentials_json = os.environ.get('GOOGLE_CALENDAR_CREDENTIALS')
        if not credentials_json:
            raise Exception("GOOGLE_CALENDAR_CREDENTIALS no configurada")
        
        # Parsear JSON de credenciales
        credentials_info = json.loads(credentials_json)
        
        # Crear credenciales
        self.credentials = Credentials.from_service_account_info(
            credentials_info,
            scopes=['https://www.googleapis.com/auth/calendar']
        )
        
        # Crear servicio de Calendar API
        self.service = build('calendar', 'v3', credentials=self.credentials)
    
    def create_employee_calendar(self, employee_name, employee_email):
        """Crear un calendario personal para un empleado"""
        try:
            calendar = {
                'summary': f'Agenda - {employee_name}',
                'description': f'Calendario de citas para {employee_name}',
                'timeZone': 'America/Santiago'  # Zona horaria de Chile
            }
            
            created_calendar = self.service.calendars().insert(body=calendar).execute()
            calendar_id = created_calendar['id']
            
            # Compartir calendario con el empleado
            if employee_email:
                self.share_calendar_with_employee(calendar_id, employee_email)
            
            return calendar_id
            
        except Exception as e:
            print(f"Error creando calendario: {e}")
            return None
    
    def share_calendar_with_employee(self, calendar_id, employee_email):
        """Compartir calendario con el empleado"""
        try:
            rule = {
                'scope': {
                    'type': 'user',
                    'value': employee_email,
                },
                'role': 'owner'  # El empleado será dueño de su calendario
            }
            
            self.service.acl().insert(calendarId=calendar_id, body=rule).execute()
            print(f"✅ Calendario compartido con {employee_email}")
            
        except Exception as e:
            print(f"❌ Error compartiendo calendario: {e}")
    

    
    def create_appointment_event(self, appointment):
        """Crear evento en Google Calendar cuando se agenda una cita"""
        try:
            # Obtener ID del calendario del empleado
            employee = appointment.employee
            calendar_id = employee.google_calendar_id
            
            def format_chilean_price(price):
                try:
                    price_int = int(float(price))
                    formatted = f"{price_int:,}".replace(',', '.')
                    return f"${formatted}"
                except:
                    return f"${price}"
            
            if not calendar_id:
                print(f"❌ Empleado {employee.username} no tiene calendario configurado")
                return None
            
            # Crear fecha y hora completa
            start_datetime = datetime.combine(appointment.date, appointment.start_time)
            end_datetime = datetime.combine(appointment.date, appointment.end_time)
            
            # Convertir a zona horaria de Chile
            chile_tz = pytz.timezone('America/Santiago')
            start_datetime = chile_tz.localize(start_datetime)
            end_datetime = chile_tz.localize(end_datetime)
            precio_formateado = format_chilean_price(appointment.service.price)
            
            
            # Crear evento con estado visible y colores correctos
            event = {
                'summary': f'{self.get_status_emoji(appointment.status)} {appointment.service.name}',
                'description': f'''
👤 Cliente: {appointment.client.get_full_name()}
📱 Teléfono: {appointment.client.phone or 'No especificado'}
📧 Email: {appointment.client.email}
💅 Servicio: {appointment.service.name}
💰 Precio: {precio_formateado}
📍 Estado: {appointment.get_status_display()}
📝 Notas: {appointment.notes or 'Sin notas'}

⚠️ IMPORTANTE: 
- Este evento se sincroniza automáticamente

🌐 Sistema: {getattr(settings, 'FRONTEND_URL', 'Creado por: ' + 'https://devsign.cl')}
                '''.strip(),
                'start': {
                    'dateTime': start_datetime.isoformat(),
                    'timeZone': 'America/Santiago',
                },
                'end': {
                    'dateTime': end_datetime.isoformat(),
                    'timeZone': 'America/Santiago',
                },
                'reminders': {
                    'useDefault': False,
                    'overrides': [
                        {'method': 'email', 'minutes': 24 * 60},  # 24 horas antes
                        {'method': 'popup', 'minutes': 30},        # 30 minutos antes
                    ],
                },
                'colorId': self.get_color_by_status(appointment.status),
                'location': getattr(settings, 'BUSINESS_ADDRESS', 'Centro de Estética'),
            }
            
            # Insertar evento en calendario
            created_event = self.service.events().insert(
                calendarId=calendar_id, 
                body=event
            ).execute()
            
            event_link = created_event.get('htmlLink', 'No disponible')
            print(f"✅ Evento creado en Google Calendar")
            print(f"🔗 Link: {event_link}")
            print(f"🎨 Color: {self.get_color_name(appointment.status)}")
            
            return created_event.get('id')
            
        except Exception as e:
            print(f"❌ Error creando evento en Google Calendar: {e}")
            import traceback
            print(traceback.format_exc())
            return None
    
    def update_appointment_event(self, appointment, event_id):
        """Actualizar evento cuando cambia la cita"""
        try:
            calendar_id = appointment.employee.google_calendar_id
            
            if not calendar_id or not event_id:
                print(f"❌ Faltan datos: calendar_id={calendar_id}, event_id={event_id}")
                return False
            
            # Crear fecha y hora completa
            start_datetime = datetime.combine(appointment.date, appointment.start_time)
            end_datetime = datetime.combine(appointment.date, appointment.end_time)
            
            # Zona horaria de Chile
            chile_tz = pytz.timezone('America/Santiago')
            start_datetime = chile_tz.localize(start_datetime)
            end_datetime = chile_tz.localize(end_datetime)
            
            # Obtener evento actual para preservar campos que no cambiamos
            try:
                current_event = self.service.events().get(
                    calendarId=calendar_id, 
                    eventId=event_id
                ).execute()
            except:
                print(f"⚠️ No se pudo obtener evento actual, creando desde cero")
                current_event = {}
            
            updated_event = {
                'summary': f'{self.get_status_emoji(appointment.status)} {appointment.service.name}',
                'description': f'''
👤 Cliente: {appointment.client.get_full_name()}
📱 Teléfono: {appointment.client.phone or 'No especificado'}
📧 Email: {appointment.client.email}
💅 Servicio: {appointment.service.name}
💰 Precio: ${appointment.service.price}
📍 Estado: {appointment.get_status_display()}
📝 Notas: {appointment.notes or 'Sin notas'}

🔄 ESTADO ACTUALIZADO: {appointment.get_status_display().upper()}

🔄 CAMBIAR ESTADO (edita el emoji del título):
⏳ = Pendiente (Amarillo)
✅ = Confirmada (Verde)  
🎉 = Completada (Azul)
❌ = Cancelada (Rojo)

⏰ Última actualización: {datetime.now(chile_tz).strftime('%d/%m/%Y %H:%M')} (Chile)

🌐 Sistema: {getattr(settings, 'FRONTEND_URL', 'https://tu-sistema.com')}
                '''.strip(),
                'start': {
                    'dateTime': start_datetime.isoformat(),
                    'timeZone': 'America/Santiago',
                },
                'end': {
                    'dateTime': end_datetime.isoformat(),
                    'timeZone': 'America/Santiago',
                },
                'colorId': self.get_color_by_status(appointment.status),
                'location': getattr(settings, 'BUSINESS_ADDRESS', 'Centro de Estética'),
            }
            
            # Preservar recordatorios si existían
            if 'reminders' in current_event:
                updated_event['reminders'] = current_event['reminders']
            else:
                updated_event['reminders'] = {
                    'useDefault': False,
                    'overrides': [
                        {'method': 'email', 'minutes': 24 * 60},
                        {'method': 'popup', 'minutes': 30},
                    ],
                }
            
            self.service.events().update(
                calendarId=calendar_id, 
                eventId=event_id, 
                body=updated_event
            ).execute()
            
            print(f"✅ Evento actualizado en Google Calendar")
            print(f"🔄 Nuevo estado: {appointment.get_status_display()}")
            print(f"🎨 Nuevo color: {self.get_color_name(appointment.status)}")
            return True
            
        except Exception as e:
            print(f"❌ Error actualizando evento: {e}")
            import traceback
            print(traceback.format_exc())
            return False
    
    def delete_appointment_event(self, calendar_id, event_id):
        """Eliminar evento cuando se cancela la cita"""
        try:
            self.service.events().delete(
                calendarId=calendar_id, 
                eventId=event_id
            ).execute()
            
            print(f"✅ Evento eliminado de Google Calendar")
            return True
            
        except Exception as e:
            print(f"❌ Error eliminando evento: {e}")
            return False
    
    def get_status_emoji(self, status):
        """
        Obtener emoji según estado de la cita
        """
        emoji_mapping = {
            'pending': '⏳',     # Reloj de arena - Pendiente
            'confirmed': '✅',   # Check verde - Confirmada
            'completed': '🎉',   # Celebración - Completada
            'cancelled': '❌'    # X roja - Cancelada
        }
        return emoji_mapping.get(status, '⏳')

    def get_color_by_status(self, status):
        """
        Obtener color ID de Google Calendar según estado de la cita
        Coincide exactamente con los colores del sistema web
        """
        color_mapping = {
            'pending': '5',      # Amarillo (como en tu web)
            'confirmed': '10',   # Verde (como en tu web)  
            'completed': '1',    # Azul (como en tu web)
            'cancelled': '4',    # Rojo para canceladas
        }
        return color_mapping.get(status, '5')  # Default: amarillo (pendiente)
    
    def get_color_name(self, status):
        """
        Obtener nombre del color para logging/debug
        """
        color_names = {
            'pending': 'Amarillo (Pendiente)',
            'confirmed': 'Verde (Confirmada)',  
            'completed': 'Azul (Completada)',
            'cancelled': 'Rojo (Cancelada)'
        }
        return color_names.get(status, 'Amarillo (Default)')
    
    def sync_all_appointments_colors(self):
        """
        Método de utilidad para sincronizar colores de todas las citas existentes
        Útil para ejecutar una sola vez después de implementar los colores
        """
        try:
            from .models import Appointment
            
            appointments_with_events = Appointment.objects.exclude(
                google_calendar_event_id__isnull=True
            ).exclude(
                google_calendar_event_id=''
            )
            
            print(f"🔄 Sincronizando colores de {appointments_with_events.count()} citas...")
            
            success_count = 0
            error_count = 0
            
            for appointment in appointments_with_events:
                try:
                    success = self.update_appointment_event(
                        appointment, 
                        appointment.google_calendar_event_id
                    )
                    
                    if success:
                        success_count += 1
                        print(f"✅ Cita {appointment.id} sincronizada")
                    else:
                        error_count += 1
                        print(f"❌ Error en cita {appointment.id}")
                        
                except Exception as e:
                    error_count += 1
                    print(f"❌ Error procesando cita {appointment.id}: {e}")
            
            print(f"\n📊 RESUMEN SINCRONIZACIÓN:")
            print(f"✅ Exitosas: {success_count}")
            print(f"❌ Con errores: {error_count}")
            print(f"📱 Total procesadas: {success_count + error_count}")
            
            return {
                'success': success_count,
                'errors': error_count,
                'total': success_count + error_count
            }
            
        except Exception as e:
            print(f"❌ Error en sincronización masiva: {e}")
            return None