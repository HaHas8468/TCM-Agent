#!/usr/bin/env bash
set -euo pipefail
source "$(cd -- "$(dirname -- "$0")" && pwd)/_common.sh"

require_docker
require_production_config
validate_compose

compose --profile ops run --rm certbot renew --webroot --webroot-path /var/www/certbot
compose exec -T edge nginx -s reload
log "证书续期检查完成，Nginx 已重载。"
