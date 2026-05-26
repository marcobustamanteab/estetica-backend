from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0004_business_logo_url_business_slug_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='business',
            name='primary_color',
            field=models.CharField(
                default='#0d9488',
                max_length=7,
                verbose_name='Color primario (hex)',
            ),
        ),
        migrations.AddField(
            model_name='business',
            name='employee_label',
            field=models.CharField(
                default='Especialista',
                max_length=60,
                verbose_name='Etiqueta de empleados',
            ),
        ),
        migrations.AddField(
            model_name='business',
            name='booking_tagline',
            field=models.CharField(
                default='Elige tu servicio y agenda en minutos',
                max_length=120,
                verbose_name='Tagline de reservas',
            ),
        ),
    ]
