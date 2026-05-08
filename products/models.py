from django.db import models
from django.db.models import Sum
from authentication.models import Business, User


class ProductCategory(models.Model):
    business = models.ForeignKey(
        Business,
        on_delete=models.CASCADE,
        related_name='product_categories',
        verbose_name="Negocio"
    )
    name = models.CharField(max_length=100, verbose_name="Nombre")
    description = models.TextField(blank=True, null=True, verbose_name="Descripción")
    is_active = models.BooleanField(default=True, verbose_name="Activo")

    class Meta:
        verbose_name = "Categoría de Producto"
        verbose_name_plural = "Categorías de Productos"
        ordering = ['name']

    def __str__(self):
        return self.name


class Product(models.Model):
    business = models.ForeignKey(
        Business,
        on_delete=models.CASCADE,
        related_name='products',
        verbose_name="Negocio"
    )
    category = models.ForeignKey(
        ProductCategory,
        on_delete=models.CASCADE,
        related_name='products',
        verbose_name="Categoría"
    )
    name = models.CharField(max_length=150, verbose_name="Nombre")
    description = models.TextField(blank=True, null=True, verbose_name="Descripción")
    sale_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Precio de venta")
    cost_price = models.DecimalField(
        max_digits=10, decimal_places=2,
        blank=True, null=True,
        verbose_name="Costo"
    )
    min_stock = models.PositiveIntegerField(
        default=0,
        verbose_name="Stock mínimo (alerta)"
    )
    is_active = models.BooleanField(default=True, verbose_name="Activo")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Producto"
        verbose_name_plural = "Productos"
        ordering = ['category', 'name']

    def __str__(self):
        return self.name

    @property
    def current_stock(self):
        result = self.movements.aggregate(total=Sum('quantity'))
        return result['total'] or 0

    @property
    def is_low_stock(self):
        return self.current_stock <= self.min_stock


class StockMovement(models.Model):
    MOVEMENT_TYPES = [
        ('in', 'Entrada'),
        ('out', 'Salida'),
        ('sale', 'Venta'),
        ('adjustment', 'Ajuste'),
        ('return', 'Devolución'),
    ]

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='movements',
        verbose_name="Producto"
    )
    # quantity es positivo para entradas/devoluciones, negativo para salidas/ventas
    quantity = models.IntegerField(verbose_name="Cantidad (+ entrada / - salida)")
    movement_type = models.CharField(
        max_length=20,
        choices=MOVEMENT_TYPES,
        verbose_name="Tipo de movimiento"
    )
    unit_price = models.DecimalField(
        max_digits=10, decimal_places=2,
        blank=True, null=True,
        verbose_name="Precio unitario al momento"
    )
    performed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='stock_movements',
        verbose_name="Realizado por"
    )
    appointment = models.ForeignKey(
        'appointments.Appointment',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='product_movements',
        verbose_name="Cita relacionada"
    )
    notes = models.TextField(blank=True, null=True, verbose_name="Notas")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha")

    class Meta:
        verbose_name = "Movimiento de Stock"
        verbose_name_plural = "Movimientos de Stock"
        ordering = ['-created_at']

    def __str__(self):
        direction = "+" if self.quantity > 0 else ""
        return f"{self.product.name} {direction}{self.quantity} ({self.get_movement_type_display()})"
