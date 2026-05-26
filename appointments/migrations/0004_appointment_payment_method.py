from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('appointments', '0003_appointment_business'),
    ]

    operations = [
        migrations.AddField(
            model_name='appointment',
            name='payment_method',
            field=models.CharField(
                blank=True,
                choices=[('efectivo', 'Efectivo'), ('transferencia', 'Transferencia'), ('pos', 'POS')],
                max_length=20,
                null=True,
                verbose_name='Medio de pago',
            ),
        ),
    ]
