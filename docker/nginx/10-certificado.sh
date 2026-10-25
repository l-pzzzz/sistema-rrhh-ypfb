#!/bin/sh
# Certificado autofirmado para desarrollo (RNF-05). En producción se montan el certificado y la
# clave reales en /etc/nginx/certs y este script no hace nada.
set -e

CERTS=/etc/nginx/certs
if [ ! -f "$CERTS/rrhh.crt" ] || [ ! -f "$CERTS/rrhh.key" ]; then
    mkdir -p "$CERTS"
    openssl req -x509 -nodes -newkey rsa:2048 -days 365 \
        -keyout "$CERTS/rrhh.key" -out "$CERTS/rrhh.crt" \
        -subj "/C=BO/O=YPFB-Andina/CN=localhost" \
        -addext "subjectAltName=DNS:localhost,IP:127.0.0.1"
    echo "Certificado autofirmado generado en $CERTS"
fi
