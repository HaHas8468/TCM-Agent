#!/usr/bin/env bash
set -euo pipefail
source "$(cd -- "$(dirname -- "$0")" && pwd)/_common.sh"

require_docker
require_production_config
require_minimum_memory
validate_compose

patient_port=$(env_value PATIENT_PORT)
doctor_port=$(env_value DOCTOR_PORT)
chmod 600 "$ENV_FILE"

existing_edge=$(service_id edge)
if [ -z "$existing_edge" ] && command -v ss >/dev/null 2>&1; then
  for port in "$patient_port" "$doctor_port"; do
    if ss -ltn "sport = :$port" | grep -q LISTEN; then
      die "宿主机端口 $port 已被占用，请释放端口后重试。"
    fi
  done
fi

log "构建并启动全栈服务。域名、TLS 与外层反向代理由部署者自行配置。"
compose up --build -d
for service in mysql neo4j redis kg agent gateway edge; do
  wait_for_service "$service" 240
done

curl -fsS --max-time 10 "http://127.0.0.1:${patient_port}/healthz" >/dev/null || die "患者端边缘服务健康检查失败。"
curl -fsS --max-time 10 "http://127.0.0.1:${doctor_port}/healthz" >/dev/null || die "医生端边缘服务健康检查失败。"

log "部署完成：患者端 http://服务器IP:${patient_port}/ ，医生端 http://服务器IP:${doctor_port}/ 。"
