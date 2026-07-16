from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import serializers, status
from django.utils.text import slugify
from .models import Business
import cloudinary.uploader

ALLOWED_IMAGE_TYPES = {'image/jpeg', 'image/png', 'image/webp', 'image/gif'}
MAX_LOGO_SIZE = 2 * 1024 * 1024  # 2 MB


class BusinessSerializer(serializers.ModelSerializer):
    class Meta:
        model = Business
        fields = ['id', 'name', 'slug', 'logo_url', 'working_days', 'primary_color', 'employee_label', 'booking_tagline']
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
        instance.primary_color = validated_data.get('primary_color', instance.primary_color)
        instance.employee_label = validated_data.get('employee_label', instance.employee_label)
        instance.booking_tagline = validated_data.get('booking_tagline', instance.booking_tagline)
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

        # Manejo de upload de logo
        logo_file = request.FILES.get('logo_file')
        if logo_file:
            if logo_file.content_type not in ALLOWED_IMAGE_TYPES:
                return Response({'error': 'Solo se permiten imágenes JPG, PNG o WebP.'}, status=400)
            if logo_file.size > MAX_LOGO_SIZE:
                return Response({'error': 'La imagen no puede superar 2 MB.'}, status=400)
            result = cloudinary.uploader.upload(
                logo_file,
                folder='business_logos',
                public_id=f'business_{business.id}',
                overwrite=True,
            )
            business.logo_url = result['secure_url']
            business.save(update_fields=['logo_url'])

        # working_days viene como string JSON cuando se envía por FormData
        data = request.data.copy()
        if 'working_days' in data and isinstance(data.get('working_days'), str):
            import json
            try:
                data['working_days'] = json.loads(data['working_days'])
            except (ValueError, TypeError):
                pass

        serializer = BusinessSerializer(business, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
