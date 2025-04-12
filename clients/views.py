# clients/views.py
from rest_framework import viewsets, permissions
from .models import Client
from .serializers import ClientSerializer

class ClientViewSet(viewsets.ModelViewSet):
    """
    API endpoint para gestionar clientes
    """
    queryset = Client.objects.all()
    serializer_class = ClientSerializer
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        """
        Permite filtrar por parámetros como is_active
        Ejemplo: /api/clients/?is_active=true
        """
        queryset = Client.objects.all()
        is_active = self.request.query_params.get('is_active', None)
        
        if is_active is not None:
            is_active = is_active.lower() == 'true'
            queryset = queryset.filter(is_active=is_active)
            
        return queryset