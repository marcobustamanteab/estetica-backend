# authentication/views.py
from rest_framework import generics, permissions, status
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
        if not self.request.user.is_superuser:
            extra = {'is_superuser': False}
            if not serializer.instance.is_staff:
                extra['is_staff'] = False
            if serializer.instance == self.request.user:
                extra['is_active'] = True
            serializer.save(**extra)
        else:
            serializer.save()


class WorkScheduleView(ListAPIView):
    serializer_class = WorkScheduleSerializer

    def get_queryset(self):
        qs = WorkSchedule.objects.all()
        employee_id = self.request.query_params.get('employee')
        if employee_id:
            qs = qs.filter(employee_id=employee_id)
        return qs


@api_view(['GET'])
@permission_classes([AllowAny])
def public_employee_schedules(request, employee_id):
    active_days = list(
        WorkSchedule.objects.filter(employee_id=employee_id, is_active=True)
        .values_list('day_of_week', flat=True)
    )
    return Response({'working_days': active_days})