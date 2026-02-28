# appointments/public_views.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from datetime import datetime, timedelta
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
        'services': list(services),
        'employees': list(employees),
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def public_available_times(request, slug):
    """Retorna horarios disponibles para una fecha, servicio y empleado"""
    business = get_object_or_404(Business, slug=slug)
    
    date_str = request.query_params.get('date')
    employee_id = request.query_params.get('employee_id')
    
    if not date_str:
        return Response({'error': 'Se requiere date'}, status=400)
    
    try:
        date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return Response({'error': 'Formato de fecha inválido'}, status=400)
    
    # Horario de atención: 9:00 - 18:00 cada 30 min
    all_times = []
    start = datetime.strptime('09:00', '%H:%M')
    end = datetime.strptime('18:00', '%H:%M')
    while start < end:
        all_times.append(start.strftime('%H:%M'))
        start += timedelta(minutes=30)
    
    # Filtrar horarios ocupados
    busy_qs = Appointment.objects.filter(
        business=business,
        date=date,
        status__in=['pending', 'confirmed']
    )
    if employee_id:
        busy_qs = busy_qs.filter(employee_id=employee_id)
    
    busy_times = set(busy_qs.values_list('start_time', flat=True))
    busy_times_str = {t.strftime('%H:%M') if hasattr(t, 'strftime') else str(t)[:5] for t in busy_times}
    
    available = [t for t in all_times if t not in busy_times_str]
    
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