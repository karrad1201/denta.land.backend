FROM nginx:alpine
RUN apk add --no-cache gettext
COPY ./nginx/backend.conf /etc/nginx/templates/
CMD ["sh", "-c", "envsubst '$$DOMAIN_NAME' < /etc/nginx/templates/backend.conf > /etc/nginx/conf.d/default.conf && exec nginx -g 'daemon off;'"]