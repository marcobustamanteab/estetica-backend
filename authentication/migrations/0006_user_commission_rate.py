from django.db import migrations, models


class Migration(migrations.Migration):
    """
    commission_rate ya existe en la DB de producción.
    Esta migración solo registra el estado en Django sin tocar la DB.
    """

    dependencies = [
        ('authentication', '0005_business_branding'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[],   # No toca la DB (columna ya existe)
            state_operations=[
                migrations.AddField(
                    model_name='user',
                    name='commission_rate',
                    field=models.DecimalField(
                        decimal_places=2,
                        default=50.0,
                        max_digits=5,
                        verbose_name='Porcentaje de comisión (%)',
                    ),
                ),
            ],
        ),
    ]
