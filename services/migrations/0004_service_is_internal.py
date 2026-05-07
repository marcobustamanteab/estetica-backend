from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('services', '0003_service_business_servicecategory_business'),
    ]

    operations = [
        migrations.AddField(
            model_name='service',
            name='is_internal',
            field=models.BooleanField(default=False, verbose_name='Solo uso interno'),
        ),
    ]
