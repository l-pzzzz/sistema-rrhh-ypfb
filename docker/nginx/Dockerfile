FROM nginx:1.27-alpine

RUN apk add --no-cache openssl
COPY 10-certificado.sh /docker-entrypoint.d/10-certificado.sh
# La imagen oficial procesa /etc/nginx/templates con envsubst y deja el resultado en conf.d.
COPY templates/ /etc/nginx/templates/
ENV HTTPS_PORT=443
RUN chmod +x /docker-entrypoint.d/10-certificado.sh
