FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc cron \
    && rm -rf /var/lib/apt/lists/*

RUN useradd -m -u 1000 appuser

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=appuser:appuser . .

RUN python manage.py collectstatic --noinput

RUN chown -R appuser:appuser /app/staticfiles

USER appuser

EXPOSE 8000

CMD ["gunicorn", "un_site.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]
