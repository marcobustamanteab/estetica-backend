# authentication/views.py
from rest_framework import generics, permissions, status, viewsets
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.permissions import IsAdminUser, IsAuthenticated, AllowAny
from rest_framework.exceptions import ValidationError
from rest_framework.decorators import api_view, permission_classes

from django.contrib.auth import get_user_model
from .serializers import UserSerializer, RegisterSerializer, CustomTokenObtainPairSerializer, AdminUserSerializer, WorkScheduleSerializer
from rest_framework.generics import ListAPIView
from .models import WorkSchedule


User = get_user_model()


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = [permissions.AllowAny]
    serializer_class = RegisterSerializer


class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


class UserListCreateView(generics.ListCreateAPIView):
    serializer_class = AdminUserSerializer
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return User.objects.all()
        if not user.business:
            return User.objects.none()
        return User.objects.filter(business=user.business)

    def perform_create(self, serializer):
        user = self.request.user
        if user.is_superuser:
            serializer.save()
        else:
            business = user.business
            if not business:
                raise ValidationError("Tu usuario no tiene un negocio asignado.")
            data = {'is_staff': False, 'is_superuser': False}
            serializer.save(business=business, **data)


class UserRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = AdminUserSerializer
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return User.objects.all()
        if not user.business:
            return User.objects.none()
        return User.objects.filter(business=user.business)

    def perform_update(self, serializer):
        old_email = serializer.instance.email

        if not self.request.user.is_superuser:
            extra = {'is_superuser': False}
            if not serializer.instance.is_staff:
                extra['is_staff'] = False
            if serializer.instance == self.request.user:
                extra['is_active'] = True
            serializer.save(**extra)
        else:
            serializer.save()

        new_email = serializer.instance.email
        if old_email != new_email and not serializer.instance.is_superuser:
            try:
                from authentication.signals import _reshare_calendar_on_email_change, _run_in_thread
                _run_in_thread(_reshare_calendar_on_email_change, serializer.instance.id, old_email, new_email)
            except Exception:
                pass

    def perform_destroy(self, instance):
        # Soft-delete: desactiva el usuario en vez de eliminarlo.
        # Preserva todas las citas, ventas y registros históricos asociados.
        instance.is_active = False
        instance.save(update_fields=['is_active'])


class WorkScheduleView(ListAPIView):
    serializer_class = WorkScheduleSerializer

    def get_queryset(self):
        qs = WorkSchedule.objects.all()
        employee_id = self.request.query_params.get('employee')
        if employee_id:
            qs = qs.filter(employee_id=employee_id)
        return qs


class WorkScheduleViewSet(viewsets.ModelViewSet):
    serializer_class = WorkScheduleSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        employee_id = self.request.query_params.get('employee')

        if user.is_superuser:
            qs = WorkSchedule.objects.all()
        elif user.is_staff:
            if not user.business:
                return WorkSchedule.objects.none()
            qs = WorkSchedule.objects.filter(employee__business=user.business)
        else:
            qs = WorkSchedule.objects.filter(employee=user)

        if employee_id:
            qs = qs.filter(employee_id=employee_id)

        return qs.order_by('employee', 'day_of_week')

    def perform_create(self, serializer):
        user = self.request.user
        employee = serializer.validated_data.get('employee')
        if not user.is_superuser and user.is_staff:
            if not user.business or employee.business != user.business:
                raise ValidationError("No tienes permiso para asignar horarios a este empleado.")
        serializer.save()

    def perform_update(self, serializer):
        user = self.request.user
        employee = serializer.instance.employee
        if not user.is_superuser and user.is_staff:
            if not user.business or employee.business != user.business:
                raise ValidationError("No tienes permiso para modificar horarios de este empleado.")
        serializer.save()


@api_view(['GET'])
@permission_classes([AllowAny])
def public_employee_schedules(request, employee_id):
    schedules = WorkSchedule.objects.filter(employee_id=employee_id, is_active=True)
    active_days = list(schedules.values_list('day_of_week', flat=True))
    
    # Obtener rango horario (min start, max end entre todos los días activos)
    hours = schedules.values('start_time', 'end_time')
    time_range = None
    if hours:
        starts = [h['start_time'].strftime('%H:%M') for h in hours]
        ends = [h['end_time'].strftime('%H:%M') for h in hours]
        time_range = {'from': min(starts), 'to': max(ends)}

    return Response({
        'working_days': active_days,
        'time_range': time_range
    })