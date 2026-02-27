# Dockerfile - CON MIGRACIONES AUTOMÁTICAS
FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

RUN python manage.py collectstatic --noinput || echo "Skipping collectstatic"

EXPOSE 8000

# EJECUTAR MIGRACIONES Y LUEGO INICIAR SERVIDOR
# CMD ["sh", "-c", "python manage.py migrate && python manage.py migrate --run-syncdb && gunicorn backend.wsgi:application --bind 0.0.0.0:8000"]
# CMD ["sh", "-c", "python manage.py migrate --noinput && gunicorn backend.wsgi:application --bind 0.0.0.0:$PORT --log-level debug"]
CMD ["sh", "-c", "python manage.py migrate --noinput && gunicorn backend.wsgi:application --bind 0.0.0.0:${PORT:-8000} --log-level debug"]