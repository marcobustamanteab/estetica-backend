# authentication/views.py
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.exceptions import ValidationError

from django.contrib.auth import get_user_model
from .serializers import UserSerializer, RegisterSerializer, CustomTokenObtainPairSerializer, AdminUserSerializer

User = get_user_model()


class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Vista personalizada para obtener tokens JWT
    """
    serializer_class = CustomTokenObtainPairSerializer


class RegisterView(generics.CreateAPIView):
    """
    Vista para registrar nuevos usuarios
    """
    queryset = User.objects.all()
    permission_classes = [permissions.AllowAny]
    serializer_class = RegisterSerializer


class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    Vista para obtener y actualizar el perfil del usuario autenticado
    """
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


class UserListCreateView(generics.ListCreateAPIView):
    """
    Lista y crea usuarios.
    Cada admin solo ve y crea usuarios de su propio negocio.
    El superadmin ve todos los usuarios de todos los negocios.
    """
    serializer_class = AdminUserSerializer
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        user = self.request.user

        # Superadmin ve todos los usuarios de todos los negocios
        if user.is_superuser:
            return User.objects.all()

        # Admin de negocio ve solo los usuarios de su negocio
        if not user.business:
            return User.objects.none()

        return User.objects.filter(business=user.business)

    def perform_create(self, serializer):
        user = self.request.user
        
        if user.is_superuser:
            # Superadmin puede crear usuarios en cualquier negocio
            # El negocio viene en el request data
            serializer.save()
        else:
            business = user.business
            if not business:
                raise ValidationError("Tu usuario no tiene un negocio asignado.")
            
            data = {'is_staff': False, 'is_superuser': False}
            serializer.save(business=business, **data)


class UserRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    """
    Ver, actualizar o eliminar un usuario específico.
    Solo puede acceder a usuarios de su propio negocio.
    El superadmin puede acceder a cualquier usuario.
    """
    serializer_class = AdminUserSerializer
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        user = self.request.user

        # Superadmin ve todos los usuarios de todos los negocios
        if user.is_superuser:
            return User.objects.all()

        # Admin de negocio ve solo los usuarios de su negocio
        if not user.business:
            return User.objects.none()

        return User.objects.filter(business=user.business)

    def perform_update(self, serializer):
        if not self.request.user.is_superuser:
            extra = {'is_superuser': False}
            # Solo forzar is_staff=False si el usuario editado no era ya staff
            if not serializer.instance.is_staff:
                extra['is_staff'] = False
            if serializer.instance == self.request.user:
                extra['is_active'] = True
            serializer.save(**extra)
        else:
            serializer.save()