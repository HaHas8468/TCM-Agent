#!/bin/sh
set -eu

template_dir=/opt/tcm-nginx-templates
target=/etc/nginx/templates/default.conf.template

if [ "${TLS_ENABLED:-0}" = "1" ] \
  && [ -n "${APP_DOMAIN:-}" ] \
  && [ -f "/etc/letsencrypt/live/${APP_DOMAIN}/fullchain.pem" ] \
  && [ -f "/etc/letsencrypt/live/${APP_DOMAIN}/privkey.pem" ]; then
  cp "$template_dir/https.conf.template" "$target"
  echo "edge: HTTPS configuration enabled"
else
  cp "$template_dir/http.conf.template" "$target"
  echo "edge: HTTP bootstrap configuration enabled"
fi
