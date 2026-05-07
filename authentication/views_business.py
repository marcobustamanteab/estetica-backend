from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import serializers, status
from django.utils.text import slugify
from .models import Business


class BusinessSerializer(serializers.ModelSerializer):
    class Meta:
        model = Business
        fields = ['id', 'name', 'slug', 'logo_url', 'working_days']
        read_only_fields = ['id']

    def update(self, instance, validated_data):
        name = validated_data.get('name', instance.name)
        # Regenerar slug solo si cambió el nombre y el slug actual fue autogenerado
        if name != instance.name:
            new_slug = slugify(name)
            # Evitar colisión de slug con otros negocios
            if not Business.objects.exclude(pk=instance.pk).filter(slug=new_slug).exists():
                instance.slug = new_slug
        instance.name = name
        instance.logo_url = validated_data.get('logo_url', instance.logo_url)
        instance.working_days = validated_data.get('working_days', instance.working_days)
        instance.save()
        return instance


class BusinessListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            if not request.user.is_superuser:
                return Response([])
            businesses = list(Business.objects.all().values('id', 'name'))
            return Response(businesses)
        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response({'error': str(e)}, status=500)


class BusinessDetailView(APIView):
    """GET y PATCH del negocio propio (admin) o cualquiera (superadmin)."""
    permission_classes = [IsAuthenticated]

    def _get_business(self, request, pk=None):
        user = request.user
        if user.is_superuser:
            try:
                return Business.objects.get(pk=pk) if pk else None
            except Business.DoesNotExist:
                return None
        # Admin: solo su propio negocio
        if user.business:
            return user.business
        return None

    def get(self, request, pk=None):
        business = self._get_business(request, pk)
        if not business:
            return Response({'error': 'Negocio no encontrado'}, status=404)
        serializer = BusinessSerializer(business)
        return Response(serializer.data)

    def patch(self, request, pk=None):
        business = self._get_business(request, pk)
        if not business:
            return Response({'error': 'Negocio no encontrado'}, status=404)
        serializer = BusinessSerializer(business, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
