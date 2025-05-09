# Usar Python 3.10
FROM python:3.10-slim

# Establecer variables de entorno
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Establecer el directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema necesarias para psycopg2
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements.txt e instalar dependencias de Python
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copiar el proyecto
COPY . .

# Ejecutar migraciones antes de iniciar la aplicación
RUN python manage.py collectstatic --noinput || echo "Skipping collectstatic"

# AÑADIR ESTE BLOQUE DE CÓDIGO PARA EJECUTAR MIGRACIONES
# Ejecutar migraciones durante la construcción (este enfoque funciona solo si la BD está accesible durante el build)
# Si no, usa el script de inicio de la Opción 1
RUN python manage.py migrate || echo "Migrations will be run at startup"

# Exponer el puerto en el que se ejecutará Django
EXPOSE 8000

# Comando para ejecutar la aplicación
CMD ["gunicorn", "backend.wsgi:application", "--bind", "0.0.0.0:8000"]