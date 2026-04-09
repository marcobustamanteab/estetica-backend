import authentication.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0003_alter_user_groups_alter_user_user_permissions_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='business',
            name='working_days',
            field=models.JSONField(default=authentication.models.default_working_days, verbose_name='Días hábiles'),
        ),
    ]