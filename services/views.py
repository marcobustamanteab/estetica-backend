from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import ServiceCategory, Service
from .serializers import ServiceCategorySerializer, ServiceSerializer

class ServiceCategoryViewSet(viewsets.ModelViewSet):
    """
    API endpoint para categorías de servicios
    """
    queryset = ServiceCategory.objects.all()
    serializer_class = ServiceCategorySerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = ServiceCategory.objects.all()
        is_active = self.request.query_params.get('is_active', None)
        
        if is_active is not None:
            is_active = is_active.lower() == 'true'
            queryset = queryset.filter(is_active=is_active)
            
        return queryset
    
    @action(detail=True, methods=['get'])
    def services(self, request, pk=None):
        """
        Obtener todos los servicios de una categoría
        """
        category = self.get_object()
        services = Service.objects.filter(category=category)
        serializer = ServiceSerializer(services, many=True)
        return Response(serializer.data)

class ServiceViewSet(viewsets.ModelViewSet):
    """
    API endpoint para servicios
    """
    queryset = Service.objects.all()
    serializer_class = ServiceSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = Service.objects.all()
        is_active = self.request.query_params.get('is_active', None)
        category = self.request.query_params.get('category', None)
        
        if is_active is not None:
            is_active = is_active.lower() == 'true'
            
            if is_active:
                queryset = queryset.filter(
                    is_active=True,
                    category__is_active=True 
                )
            else:
                queryset = queryset.filter(is_active=False)
            
        if category is not None:
            queryset = queryset.filter(category_id=category)
            
        queryset = queryset.order_by('-category__is_active', 'category__name', 'name')
            
        return queryset

    @action(detail=False, methods=['get'])
    def available_for_appointments(self, request):
        """
        Endpoint especial para obtener solo servicios disponibles para citas
        Requiere que tanto el servicio como su categoría estén activos
        """
        queryset = Service.objects.filter(
            is_active=True,
            category__is_active=True
        ).order_by('category__name', 'name')
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)