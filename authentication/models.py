# authentication/models.py

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
from django.utils.text import slugify


def default_working_days():
    return [0, 1, 2, 3, 4, 5, 6]

class Business(models.Model):
    """
    Representa un negocio/centro de estética.
    Cada administrador tendrá su propio Business.
    Todo (usuarios, clientes, citas, servicios) quedará asociado a un Business.
    """
    name = models.CharField(max_length=200, verbose_name="Nombre del negocio")
    slug = models.SlugField(max_length=200, unique=True, blank=True, null=True)
    owner = models.OneToOneField(
        'User',
        on_delete=models.CASCADE,
        related_name='owned_business',
        verbose_name="Propietario",
        null=True,
        blank=True
    )
    logo_url = models.URLField(max_length=500, blank=True, null=True, verbose_name="URL del logo")

    working_days = models.JSONField(
        default=default_working_days,
        verbose_name="Días hábiles"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Negocio"
        verbose_name_plural = "Negocios"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class User(AbstractUser):
    """
    Usuario del sistema. Puede ser administrador (is_staff=True) o empleado.
    El campo 'business' indica a qué negocio pertenece este usuario.
    Un administrador pertenece a su propio negocio.
    Un empleado pertenece al negocio del admin que lo creó.
    """
    email = models.EmailField(_('email address'), unique=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    profile_image = models.ImageField(upload_to='profile_images/', blank=True, null=True)

    google_calendar_id = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text="ID del calendario de Google del empleado"
    )

    # Cada usuario pertenece a un negocio
    business = models.ForeignKey(
        Business,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='users',
        verbose_name="Negocio"
    )

    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name=_('groups'),
        blank=True,
        related_name='authentication_user_set',
        related_query_name='user',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name=_('user permissions'),
        blank=True,
        related_name='authentication_user_set',
        related_query_name='user',
    )
    
    commission_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=50.00,
        verbose_name="Porcentaje de comisión (%)"
    )

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')

    def __str__(self):
        return self.email

class WorkSchedule(models.Model):
    DAYS_OF_WEEK = [
        (0, 'Lunes'),
        (1, 'Martes'),
        (2, 'Miércoles'),
        (3, 'Jueves'),
        (4, 'Viernes'),
        (5, 'Sábado'),
        (6, 'Domingo'),
    ]

    employee = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='work_schedules',
        verbose_name="Empleado"
    )
    day_of_week = models.IntegerField(choices=DAYS_OF_WEEK, verbose_name="Día de la semana")
    start_time = models.TimeField(verbose_name="Hora de entrada")
    end_time = models.TimeField(verbose_name="Hora de salida")
    is_active = models.BooleanField(default=True, verbose_name="Activo")

    class Meta:
        verbose_name = "Horario de trabajo"
        verbose_name_plural = "Horarios de trabajo"
        unique_together = [['employee', 'day_of_week']]

    def __str__(self):
        return f"{self.employee.get_full_name()} - {self.get_day_of_week_display()}"