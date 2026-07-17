#!/usr/bin/env bash
set -euo pipefail
source "$(cd -- "$(dirname -- "$0")" && pwd)/_common.sh"

require_docker
require_production_config
require_minimum_memory
validate_compose

domain=$(env_value APP_DOMAIN)
email=$(env_value LETSENCRYPT_EMAIL)
chmod 600 "$ENV_FILE"

existing_edge=$(service_id edge)
if [ -z "$existing_edge" ] && command -v ss >/dev/null 2>&1; then
  for port in 80 443; do
    if ss -ltn "sport = :$port" | grep -q LISTEN; then
      die "宿主机端口 $port 已被占用，请释放端口后重试。"
    fi
  done
fi

log "构建并启动全栈服务（首次部署将以 HTTP 完成证书验证）。"
compose up --build -d
for service in mysql neo4j redis kg agent gateway edge; do
  wait_for_service "$service" 240
done

curl -fsS --max-time 10 http://127.0.0.1/healthz >/dev/null || die "边缘服务 HTTP 健康检查失败。"

if ! compose exec -T edge test -f "/etc/letsencrypt/live/${domain}/fullchain.pem"; then
  log "正在为 ${domain} 申请 Let's Encrypt 证书。"
  compose --profile ops run --rm certbot certonly \
    --webroot --webroot-path /var/www/certbot \
    --email "$email" --agree-tos --no-eff-email --non-interactive \
    -d "$domain"
fi

set_env_value TLS_ENABLED 1
compose up -d --force-recreate edge
wait_for_service edge 90
curl -kfsS --max-time 15 --resolve "${domain}:443:127.0.0.1" "https://${domain}/healthz" >/dev/null \
  || die "HTTPS 健康检查失败；请检查域名解析、证书和 edge 日志。"

log "部署完成： https://${domain}/ （患者端），https://${domain}/doctor/ （医生端）。"
