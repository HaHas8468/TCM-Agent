#!/usr/bin/env bash
set -euo pipefail
source "$(cd -- "$(dirname -- "$0")" && pwd)/_common.sh"

require_docker
require_env_file
validate_compose
compose ps

domain=$(env_value APP_DOMAIN)
if [ "$(env_value TLS_ENABLED)" = "1" ] && [ -n "$domain" ]; then
  curl -kfsS --max-time 10 --resolve "${domain}:443:127.0.0.1" "https://${domain}/healthz" || true
else
  curl -fsS --max-time 10 http://127.0.0.1/healthz || true
fi
