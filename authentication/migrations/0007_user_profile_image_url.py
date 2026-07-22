from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0006_user_commission_rate'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='profile_image',
            field=models.URLField(
                blank=True,
                max_length=500,
                null=True,
                verbose_name='Foto de perfil',
            ),
        ),
    ]
