# appointments/public_views.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from datetime import datetime, timedelta
import pytz
from authentication.models import Business
from .models import Appointment
import threading


@api_view(['GET'])
@permission_classes([AllowAny])
def public_business_info(request, slug):
    """Retorna info del negocio, sus servicios y empleados"""
    business = get_object_or_404(Business, slug=slug)
    
    services = business.services.filter(is_active=True).values(
        'id', 'name', 'duration', 'price', 'description'
    )
    
    employees = business.users.filter(
        is_active=True, is_staff=False
    ).values('id', 'first_name', 'last_name')
    
    return Response({
        'id': business.id,
        'name': business.name,
        'slug': business.slug,
        'logo_url': business.logo_url,
        'services': list(services),
        'employees': list(employees),
        'working_days': business.working_days,
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def public_available_times(request, slug):
    """Retorna horarios disponibles para una fecha y empleado"""
    business = get_object_or_404(Business, slug=slug)
    
    date_str = request.query_params.get('date')
    employee_id = request.query_params.get('employee_id')
    service_id = request.query_params.get('service_id')
    
    if not date_str:
        return Response({'error': 'Se requiere date'}, status=400)
    
    try:
        date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return Response({'error': 'Formato de fecha inválido'}, status=400)
    
    # Bloquear días no hábiles del negocio
    if date.weekday() not in business.working_days:
        return Response({'available_times': [], 'closed': True, 'reason': 'El negocio no atiende este día'})
    
    # Obtener duración del servicio seleccionado (fallback 30 min)
    slot_duration = 30
    if service_id:
        try:
            from services.models import Service
            service = Service.objects.get(id=service_id, business=business)
            slot_duration = service.duration
        except Exception:
            pass
    
    # Obtener horario del empleado para ese día
    work_start = '09:00'
    work_end = '18:00'
    
    if employee_id:
        from authentication.models import WorkSchedule
        try:
            schedule = WorkSchedule.objects.get(
                employee_id=employee_id,
                day_of_week=date.weekday(),
                is_active=True
            )
            work_start = schedule.start_time.strftime('%H:%M')
            work_end = schedule.end_time.strftime('%H:%M')
        except WorkSchedule.DoesNotExist:
            return Response({'available_times': [], 'closed': True, 'reason': 'El especialista no trabaja este día'})
    
    # Generar todos los slots de 30 min según horario del empleado
    all_times = []
    start = datetime.strptime(work_start, '%H:%M')
    end = datetime.strptime(work_end, '%H:%M')
    while start < end:
        all_times.append(start.strftime('%H:%M'))
        start += timedelta(minutes=30)
    
    # Obtener citas ocupadas con sus rangos
    busy_qs = Appointment.objects.filter(
        business=business,
        date=date,
        status__in=['pending', 'confirmed']
    )
    if employee_id:
        busy_qs = busy_qs.filter(employee_id=employee_id)
    
    def time_to_min(t):
        return t.hour * 60 + t.minute
    
    busy_ranges = [(time_to_min(a.start_time), time_to_min(a.end_time)) for a in busy_qs]
    
    # Filtrar slots que se solapan considerando duración del servicio
    available = []
    for t in all_times:
        h, m = map(int, t.split(':'))
        slot_start = h * 60 + m
        slot_end = slot_start + slot_duration
        # También verificar que el slot no exceda el horario de cierre
        end_min = int(work_end.split(':')[0]) * 60 + int(work_end.split(':')[1])
        if slot_end > end_min:
            continue
        overlaps = any(slot_start < r_end and slot_end > r_start for r_start, r_end in busy_ranges)
        if not overlaps:
            available.append(t)
        
    # Filtrar horarios pasados si la fecha es hoy (zona horaria Chile)
    chile_tz = pytz.timezone('America/Santiago')
    now_chile = datetime.now(chile_tz)
    today_chile = now_chile.date()

    if date == today_chile:
        current_minutes = now_chile.hour * 60 + now_chile.minute
        available = [t for t in available if (int(t.split(':')[0]) * 60 + int(t.split(':')[1])) > current_minutes]

    return Response({'available_times': available})


@api_view(['POST'])
@permission_classes([AllowAny])
def public_create_appointment(request, slug):
    """Crea una cita pública sin autenticación"""
    business = get_object_or_404(Business, slug=slug)
    
    data = request.data
    required = ['service_id', 'employee_id', 'date', 'start_time', 'client_name', 'client_email', 'client_phone']
    for field in required:
        if not data.get(field):
            return Response({'error': f'Campo requerido: {field}'}, status=400)
    
    try:
        from services.models import Service
        from clients.models import Client
        from authentication.models import User
        
        service = get_object_or_404(Service, id=data['service_id'], business=business)
        employee = get_object_or_404(User, id=data['employee_id'], business=business)
        
        # Buscar o crear cliente
        client, _ = Client.objects.get_or_create(
            email=data['client_email'],
            business=business,
            defaults={
                'first_name': data['client_name'].split()[0],
                'last_name': ' '.join(data['client_name'].split()[1:]) or '-',
                'phone': data['client_phone'],
            }
        )
        
        # Calcular hora de fin
        start = datetime.strptime(data['start_time'], '%H:%M')
        end = start + timedelta(minutes=service.duration)
        
        appointment = Appointment.objects.create(
            business=business,
            client=client,
            service=service,
            employee=employee,
            date=data['date'],
            start_time=data['start_time'],
            end_time=end.strftime('%H:%M'),
            notes=data.get('notes', ''),
            status='pending',
        )
        
        # Email en background
        def send_email():
            from appointments.signals import send_confirmation_email
            send_confirmation_email(appointment)
        
        threading.Thread(target=send_email, daemon=True).start()
        
        return Response({'id': appointment.id, 'status': 'ok'}, status=201)
    
    except Exception as e:
        return Response({'error': str(e)}, status=400)