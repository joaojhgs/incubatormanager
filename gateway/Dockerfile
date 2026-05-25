# syntax=docker/dockerfile:1
FROM nginx:1.26.3-alpine

COPY gateway/nginx.conf /etc/nginx/nginx.conf
COPY gateway/includes/ /etc/nginx/includes/
COPY gateway/docs-index.html /etc/nginx/html/docs-index.html

RUN rm -f /etc/nginx/conf.d/default.conf \
    && chown -R nginx:nginx /var/cache/nginx /var/log/nginx /etc/nginx \
    && touch /var/run/nginx.pid \
    && chown nginx:nginx /var/run/nginx.pid

USER nginx

EXPOSE 8080
