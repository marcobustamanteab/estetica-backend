FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /app

RUN apt-get update && apt-get install -y gcc postgresql-client libpq-dev && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

COPY . .
COPY migrate.sh .
RUN chmod +x migrate.sh

RUN python manage.py collectstatic --noinput || echo "Skipping collectstatic"

EXPOSE 8000
CMD ["./migrate.sh"]