FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN addgroup --system visionx && adduser --system --ingroup visionx visionx

COPY --chown=visionx:visionx . .

USER visionx

EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:5000/health/live', timeout=3)"

CMD ["sh", "-c", "alembic upgrade head && gunicorn --bind 0.0.0.0:${PORT:-5000} --workers 2 --threads 4 'app:create_app()'"]
