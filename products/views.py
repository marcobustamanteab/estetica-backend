from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from django.db.models import Sum

from .models import ProductCategory, Product, StockMovement
from .serializers import ProductCategorySerializer, ProductSerializer, StockMovementSerializer


class ProductCategoryViewSet(viewsets.ModelViewSet):
    serializer_class = ProductCategorySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            qs = ProductCategory.objects.all()
            business_id = self.request.query_params.get('business')
            if business_id:
                qs = qs.filter(business_id=business_id)
        elif not user.business:
            return ProductCategory.objects.none()
        else:
            qs = ProductCategory.objects.filter(business=user.business)

        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            qs = qs.filter(is_active=is_active.lower() == 'true')

        return qs

    def perform_create(self, serializer):
        business = self.request.user.business
        if not business:
            raise ValidationError("Tu usuario no tiene un negocio asignado.")
        serializer.save(business=business)


class ProductViewSet(viewsets.ModelViewSet):
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            qs = Product.objects.select_related('category').all()
            business_id = self.request.query_params.get('business')
            if business_id:
                qs = qs.filter(business_id=business_id)
        elif not user.business:
            return Product.objects.none()
        else:
            qs = Product.objects.select_related('category').filter(business=user.business)

        category_id = self.request.query_params.get('category')
        if category_id:
            qs = qs.filter(category_id=category_id)

        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            qs = qs.filter(is_active=is_active.lower() == 'true')

        low_stock = self.request.query_params.get('low_stock')
        if low_stock == 'true':
            # Filtrar productos cuyo stock actual <= min_stock
            # Calculado via anotación para poder filtrar
            from django.db.models import Value, IntegerField
            qs = qs.annotate(
                stock_total=Sum('movements__quantity')
            ).filter(
                stock_total__lte=models_min_stock_ref()
            )

        return qs.order_by('category__name', 'name')

    def perform_create(self, serializer):
        business = self.request.user.business
        if not business:
            raise ValidationError("Tu usuario no tiene un negocio asignado.")
        serializer.save(business=business)

    @action(detail=True, methods=['get'])
    def movements(self, request, pk=None):
        product = self.get_object()
        qs = product.movements.select_related('performed_by').all()
        serializer = StockMovementSerializer(qs, many=True)
        return Response(serializer.data)


def models_min_stock_ref():
    from django.db.models import F
    return F('min_stock')


class StockMovementViewSet(viewsets.ModelViewSet):
    serializer_class = StockMovementSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ['get', 'post', 'head', 'options']  # sin PUT/PATCH/DELETE — los movimientos son inmutables

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            qs = StockMovement.objects.select_related('product', 'performed_by').all()
            business_id = self.request.query_params.get('business')
            if business_id:
                qs = qs.filter(product__business_id=business_id)
        elif not user.business:
            return StockMovement.objects.none()
        else:
            qs = StockMovement.objects.select_related('product', 'performed_by').filter(
                product__business=user.business
            )

        product_id = self.request.query_params.get('product')
        if product_id:
            qs = qs.filter(product_id=product_id)

        movement_type = self.request.query_params.get('movement_type')
        if movement_type:
            qs = qs.filter(movement_type=movement_type)

        performed_by = self.request.query_params.get('performed_by')
        if performed_by:
            qs = qs.filter(performed_by_id=performed_by)

        date_from = self.request.query_params.get('date_from')
        if date_from:
            qs = qs.filter(created_at__date__gte=date_from)

        date_to = self.request.query_params.get('date_to')
        if date_to:
            qs = qs.filter(created_at__date__lte=date_to)

        return qs

    def perform_create(self, serializer):
        user = self.request.user
        product = serializer.validated_data.get('product')

        # Verificar que el producto pertenece al mismo negocio
        if not user.is_superuser and product.business != user.business:
            raise ValidationError("No tienes permiso para registrar movimientos en este producto.")

        # Capturar precio unitario del producto si no se envió
        unit_price = serializer.validated_data.get('unit_price')
        if unit_price is None:
            movement_type = serializer.validated_data.get('movement_type')
            if movement_type == 'sale':
                unit_price = product.sale_price
            elif movement_type in ('in', 'return'):
                unit_price = product.cost_price

        serializer.save(performed_by=user, unit_price=unit_price)
