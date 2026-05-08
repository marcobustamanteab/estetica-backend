from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('authentication', '0001_initial'),
        ('appointments', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ProductCategory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='Nombre')),
                ('description', models.TextField(blank=True, null=True, verbose_name='Descripción')),
                ('is_active', models.BooleanField(default=True, verbose_name='Activo')),
                ('business', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='product_categories',
                    to='authentication.business',
                    verbose_name='Negocio',
                )),
            ],
            options={
                'verbose_name': 'Categoría de Producto',
                'verbose_name_plural': 'Categorías de Productos',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=150, verbose_name='Nombre')),
                ('description', models.TextField(blank=True, null=True, verbose_name='Descripción')),
                ('sale_price', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Precio de venta')),
                ('cost_price', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='Costo')),
                ('min_stock', models.PositiveIntegerField(default=0, verbose_name='Stock mínimo (alerta)')),
                ('is_active', models.BooleanField(default=True, verbose_name='Activo')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('business', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='products',
                    to='authentication.business',
                    verbose_name='Negocio',
                )),
                ('category', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='products',
                    to='products.productcategory',
                    verbose_name='Categoría',
                )),
            ],
            options={
                'verbose_name': 'Producto',
                'verbose_name_plural': 'Productos',
                'ordering': ['category', 'name'],
            },
        ),
        migrations.CreateModel(
            name='StockMovement',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity', models.IntegerField(verbose_name='Cantidad (+ entrada / - salida)')),
                ('movement_type', models.CharField(
                    choices=[
                        ('in', 'Entrada'),
                        ('out', 'Salida'),
                        ('sale', 'Venta'),
                        ('adjustment', 'Ajuste'),
                        ('return', 'Devolución'),
                    ],
                    max_length=20,
                    verbose_name='Tipo de movimiento',
                )),
                ('unit_price', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='Precio unitario al momento')),
                ('notes', models.TextField(blank=True, null=True, verbose_name='Notas')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Fecha')),
                ('appointment', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='product_movements',
                    to='appointments.appointment',
                    verbose_name='Cita relacionada',
                )),
                ('performed_by', models.ForeignKey(
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='stock_movements',
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='Realizado por',
                )),
                ('product', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='movements',
                    to='products.product',
                    verbose_name='Producto',
                )),
            ],
            options={
                'verbose_name': 'Movimiento de Stock',
                'verbose_name_plural': 'Movimientos de Stock',
                'ordering': ['-created_at'],
            },
        ),
    ]
