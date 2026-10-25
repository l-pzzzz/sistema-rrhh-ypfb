FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# mysqlclient (compilación), mysqldump para los respaldos (RF-25) y Pango para WeasyPrint (PDF).
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential pkg-config default-libmysqlclient-dev default-mysql-client \
        libpango-1.0-0 libpangoft2-1.0-0 libharfbuzz0b fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
RUN chmod +x docker/web/entrypoint.sh \
    && useradd --create-home --uid 1000 rrhh \
    && mkdir -p /app/staticfiles /app/media \
    && chown -R rrhh:rrhh /app
USER rrhh

EXPOSE 8000
ENTRYPOINT ["docker/web/entrypoint.sh"]
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "4", "--access-logfile", "-"]
