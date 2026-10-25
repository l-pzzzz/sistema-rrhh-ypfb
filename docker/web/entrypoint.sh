#!/bin/sh
set -e

# Solo el servicio web migra y recolecta estáticos; worker y beat usan la misma imagen.
if [ "$1" = "gunicorn" ]; then
    python manage.py migrate --noinput
    python manage.py collectstatic --noinput
fi

exec "$@"
