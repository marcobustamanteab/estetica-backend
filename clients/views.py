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

        if user.is_superuser:
            queryset = Client.objects.all()
            # Superadmin puede filtrar por negocio via query param
            business_id = self.request.query_params.get('business', None)
            if business_id:
                queryset = queryset.filter(business_id=business_id)
        elif not user.business:
            return Client.objects.none()
        else:
            queryset = Client.objects.filter(business=user.business)

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