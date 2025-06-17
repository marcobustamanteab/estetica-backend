# migrate.sh
#!/bin/bash
echo "Ejecutando migraciones forzadas..."
python manage.py migrate --run-syncdb
python manage.py migrate
echo "Migraciones completadas"
exec gunicorn backend.wsgi:application --bind 0.0.0.0:8000