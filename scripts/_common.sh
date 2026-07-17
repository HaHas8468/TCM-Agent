#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
REPO_ROOT=$(cd -- "$SCRIPT_DIR/.." && pwd)
COMPOSE_FILE="$REPO_ROOT/compose.yaml"
ENV_FILE="$REPO_ROOT/.env"

log() { printf '[tcm-ops] %s\n' "$*"; }
die() { printf '[tcm-ops] 错误：%s\n' "$*" >&2; exit 1; }

compose() {
  TCM_ENV_FILE=.env docker compose --project-directory "$REPO_ROOT" --env-file "$ENV_FILE" -f "$COMPOSE_FILE" "$@"
}

require_commands() {
  local command_name
  for command_name in "$@"; do
    command -v "$command_name" >/dev/null 2>&1 || die "缺少命令：$command_name"
  done
}

require_env_file() {
  [ -f "$ENV_FILE" ] || die "未找到 $ENV_FILE；请先执行 cp .env.example .env 并填写真实配置。"
}

env_value() {
  local key=$1
  awk -v key="$key" 'index($0, key "=") == 1 { sub("^[^=]*=", ""); print; exit }' "$ENV_FILE"
}

set_env_value() {
  local key=$1 value=$2
  if grep -q "^${key}=" "$ENV_FILE"; then
    sed -i "s|^${key}=.*|${key}=${value}|" "$ENV_FILE"
  else
    printf '\n%s=%s\n' "$key" "$value" >> "$ENV_FILE"
  fi
}

is_placeholder() {
  local value=${1:-}
  [ -z "$value" ] || [[ "$value" == *replace-with* ]] || [[ "$value" == *example.com* ]]
}

require_production_config() {
  require_env_file
  local key value
  for key in APP_DOMAIN LETSENCRYPT_EMAIL MYSQL_PASSWORD MYSQL_ROOT_PASSWORD NEO4J_PASSWORD AGENT_API_KEY DASHSCOPE_API_KEY; do
    value=$(env_value "$key")
    is_placeholder "$value" && die "$key 未配置真实值。"
  done
  [[ $(env_value APP_DOMAIN) =~ ^[A-Za-z0-9.-]+$ ]] || die "APP_DOMAIN 格式不合法。"
  [[ $(env_value LETSENCRYPT_EMAIL) == *"@"* ]] || die "LETSENCRYPT_EMAIL 格式不合法。"
  [[ ",$(env_value CORS_ORIGINS)," == *",https://$(env_value APP_DOMAIN),"* ]] \
    || die "CORS_ORIGINS 必须包含 https://APP_DOMAIN。"
}

require_docker() {
  require_commands docker
  docker info >/dev/null 2>&1 || die "无法连接 Docker daemon；请检查 Docker 服务和当前用户权限。"
  docker compose version >/dev/null 2>&1 || die "未安装 Docker Compose v2。"
}

validate_compose() {
  compose config --quiet || die "Compose 或 .env 配置校验失败。"
}

service_id() { compose ps -q "$1"; }

wait_for_service() {
  local service=$1 timeout=${2:-180} elapsed=0 id state
  while [ "$elapsed" -lt "$timeout" ]; do
    id=$(service_id "$service")
    if [ -n "$id" ]; then
      state=$(docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' "$id" 2>/dev/null || true)
      if [ "$state" = "healthy" ] || { [ "$state" = "running" ] && [ "$service" = "certbot" ]; }; then
        return 0
      fi
    fi
    sleep 3
    elapsed=$((elapsed + 3))
  done
  die "服务 $service 未能在 ${timeout}s 内变为健康状态。请执行 ./scripts/logs.sh $service 排查。"
}

memory_total_kb() {
  awk '/MemTotal:/ { print $2; exit }' /proc/meminfo 2>/dev/null || true
}

require_minimum_memory() {
  local total_kb
  total_kb=$(memory_total_kb)
  [ -n "$total_kb" ] || { log "无法读取系统内存，跳过内存检测。"; return; }
  [ "$total_kb" -ge 7340032 ] || die "服务器内存不足 8GB；请升级服务器或明确调整资源方案后再部署。"
}

backup_root() {
  local configured root
  configured=$(env_value BACKUP_DIR)
  configured=${configured:-./backups}
  if [[ "$configured" = /* ]]; then
    root=$(realpath -m "$configured")
  else
    root=$(realpath -m "$REPO_ROOT/${configured#./}")
  fi
  [ "$root" != "/" ] && [ "$root" != "$REPO_ROOT" ] || die "BACKUP_DIR 不能指向仓库根目录或 / 。"
  printf '%s\n' "$root"
}

assert_backup_path() {
  local path=$1 root
  root=$(backup_root)
  path=$(realpath -m "$path")
  [[ "$path" == "$root"/* ]] || die "备份路径必须位于 $root 内。"
  printf '%s\n' "$path"
}
