# services/models.py
from django.db import models
from django.contrib.auth.models import Group
from authentication.models import Business  # importamos Business


class ServiceCategory(models.Model):

    # Cada categoría pertenece a un negocio
    # null=True para no romper los registros existentes
    business = models.ForeignKey(
        Business,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='service_categories',
        verbose_name="Negocio"
    )
    name = models.CharField(max_length=100, verbose_name="Nombre")
    description = models.TextField(blank=True, null=True, verbose_name="Descripción")
    is_active = models.BooleanField(default=True, verbose_name="Activo")

    class Meta:
        verbose_name = "Categoría de Servicio"
        verbose_name_plural = "Categorías de Servicios"
        ordering = ['name']

    def __str__(self):
        return self.name


class Service(models.Model):

    # Cada servicio pertenece a un negocio
    # null=True para no romper los registros existentes
    business = models.ForeignKey(
        Business,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='services',
        verbose_name="Negocio"
    )
    category = models.ForeignKey(
        ServiceCategory,
        on_delete=models.CASCADE,
        related_name='services',
        verbose_name="Categoría"
    )
    name = models.CharField(max_length=100, verbose_name="Nombre")
    description = models.TextField(blank=True, null=True, verbose_name="Descripción")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Precio")
    duration = models.PositiveIntegerField(verbose_name="Duración (minutos)")
    is_active = models.BooleanField(default=True, verbose_name="Activo")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de creación")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Fecha de actualización")

    class Meta:
        verbose_name = "Servicio"
        verbose_name_plural = "Servicios"
        ordering = ['category', 'name']

    def __str__(self):
        return f"{self.name} - ${self.price}"


class RoleCategoryPermission(models.Model):
    """
    Asocia un Rol (Grupo) con una Categoría de Servicio.
    Define qué categorías puede gestionar cada rol.
    """
    role = models.ForeignKey(
        Group,
        on_delete=models.CASCADE,
        related_name='allowed_categories',
        verbose_name="Rol"
    )
    category = models.ForeignKey(
        'ServiceCategory',
        on_delete=models.CASCADE,
        related_name='allowed_roles',
        verbose_name="Categoría"
    )

    class Meta:
        verbose_name = "Permiso de Categoría por Rol"
        verbose_name_plural = "Permisos de Categorías por Roles"
        unique_together = ('role', 'category')

    def __str__(self):
        return f"{self.role.name} - {self.category.name}"