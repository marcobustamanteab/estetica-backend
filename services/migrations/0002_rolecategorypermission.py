# Generated by Django 4.2.10 on 2025-05-03 23:18

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
        ('services', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='RoleCategoryPermission',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='allowed_roles', to='services.servicecategory', verbose_name='Categoría')),
                ('role', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='allowed_categories', to='auth.group', verbose_name='Rol')),
            ],
            options={
                'verbose_name': 'Permiso de Categoría por Rol',
                'verbose_name_plural': 'Permisos de Categorías por Roles',
                'unique_together': {('role', 'category')},
            },
        ),
    ]
