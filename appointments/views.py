# appointments/views.py
from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from datetime import datetime, timedelta
from django.db import models
from .models import Appointment
from .serializers import AppointmentSerializer, CalendarAppointmentSerializer
from authentication.models import User


class AppointmentViewSet(viewsets.ModelViewSet):
    """
    API endpoint para citas.
    Cada usuario solo ve las citas de su propio negocio.
    """
    queryset = Appointment.objects.all()
    serializer_class = AppointmentSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['client', 'service', 'employee', 'date', 'status']
    search_fields = ['notes', 'client__first_name', 'client__last_name', 'employee__username']
    ordering_fields = ['date', 'start_time', 'created_at']

    def get_queryset(self):
        user = self.request.user

        if user.is_superuser:
            queryset = Appointment.objects.all()
        elif user.is_staff:
            # Admin ve todas las citas de su negocio
            if not user.business:
                return Appointment.objects.none()
            queryset = Appointment.objects.filter(business=user.business)
        elif user.business:
            # Trabajador ve solo sus propias citas
            queryset = Appointment.objects.filter(
                business=user.business,
                employee=user
            )
        else:
            return Appointment.objects.none()

        # Filtrando por fecha
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')

        if date_from:
            queryset = queryset.filter(date__gte=date_from)
        if date_to:
            queryset = queryset.filter(date__lte=date_to)

        # Filtrando por periodo
        period = self.request.query_params.get('period')
        today = datetime.now().date()

        if period == 'week':
            start_of_week = today - timedelta(days=today.weekday())
            end_of_week = start_of_week + timedelta(days=6)
            queryset = queryset.filter(date__range=[start_of_week, end_of_week])
        elif period == 'month':
            start_of_month = today.replace(day=1)
            if today.month == 12:
                end_of_month = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
            else:
                end_of_month = today.replace(month=today.month + 1, day=1) - timedelta(days=1)
            queryset = queryset.filter(date__range=[start_of_month, end_of_month])

        return queryset

    def perform_create(self, serializer):
        business = self.request.user.business
        if not business:
            from rest_framework.exceptions import ValidationError
            raise ValidationError("Tu usuario no tiene un negocio asignado.")
        serializer.save(business=business)

    def update(self, request, *args, **kwargs):
        """
        Impide editar citas que ya están completadas
        """
        partial = kwargs.pop('partial', False)
        instance = self.get_object()

        if instance.status == 'completed':
            return Response(
                {"error": "Las citas completadas no pueden ser editadas."},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return Response(serializer.data)

    def partial_update(self, request, *args, **kwargs):
        """
        Impide cambiar el estado de citas completadas
        """
        instance = self.get_object()

        if instance.status == 'completed' and 'status' in request.data:
            return Response(
                {"error": "Las citas completadas no pueden cambiar de estado."},
                status=status.HTTP_400_BAD_REQUEST
            )

        return super().partial_update(request, *args, **kwargs)

    @action(detail=False, methods=['get'])
    def calendar(self, request):
        """
        Retorna las citas en formato de calendario
        """
        queryset = self.get_queryset()
        serializer = CalendarAppointmentSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def employee_availability(self, request):
        """
        Verifica disponibilidad de empleados para una fecha y hora específicas.
        Solo busca entre los empleados del mismo negocio.
        """
        date = request.query_params.get('date')
        start_time = request.query_params.get('start_time')
        service_id = request.query_params.get('service_id')

        if not all([date, start_time, service_id]):
            return Response(
                {"error": "Se requieren los parámetros 'date', 'start_time' y 'service_id'"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            appointment_date = datetime.strptime(date, '%Y-%m-%d').date()
            appointment_start = datetime.strptime(start_time, '%H:%M').time()

            from services.models import Service
            try:
                service = Service.objects.get(id=service_id)
                duration = service.duration
            except Service.DoesNotExist:
                return Response(
                    {"error": "Servicio no encontrado"},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Calcular hora de fin
            start_datetime = datetime.combine(appointment_date, appointment_start)
            end_datetime = start_datetime + timedelta(minutes=duration)
            appointment_end = end_datetime.time()

            # Empleados ocupados en ese horario (solo del mismo negocio)
            busy_employees = Appointment.objects.filter(
                business=request.user.business,
                date=appointment_date,
                status__in=['pending', 'confirmed'],
            ).filter(
                models.Q(start_time__lt=appointment_end) &
                models.Q(end_time__gt=appointment_start)
            ).values_list('employee_id', flat=True)

            # Empleados disponibles del mismo negocio
            available_employees = User.objects.filter(
                business=request.user.business
            ).exclude(id__in=busy_employees)

            from authentication.serializers import UserSerializer
            serializer = UserSerializer(available_employees, many=True)
            return Response(serializer.data)

        except ValueError:
            return Response(
                {"error": "Formato de fecha u hora inválido"},
                status=status.HTTP_400_BAD_REQUEST
            )