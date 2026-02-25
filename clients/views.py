# clients/views.py
from rest_framework import viewsets, permissions
from .models import Client
from .serializers import ClientSerializer


class ClientViewSet(viewsets.ModelViewSet):
    """
    API endpoint para gestionar clientes.
    Cada usuario solo ve los clientes de su propio negocio.
    """
    queryset = Client.objects.all()
    serializer_class = ClientSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        # Si el usuario no tiene negocio asignado, no devuelve nada
        if not user.business:
            return Client.objects.none()

        queryset = Client.objects.filter(business=user.business)

        # Filtro opcional por estado activo/inactivo
        is_active = self.request.query_params.get('is_active', None)
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')

        return queryset

    def perform_create(self, serializer):
        business = self.request.user.business
        if not business:
            from rest_framework.exceptions import ValidationError
            raise ValidationError("Tu usuario no tiene un negocio asignado.")
        serializer.save(business=business)