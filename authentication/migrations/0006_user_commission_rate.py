from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0005_business_branding'),
    ]

    operations = [
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
    ]
