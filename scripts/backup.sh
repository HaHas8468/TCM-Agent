#!/usr/bin/env bash
set -euo pipefail
source "$(cd -- "$(dirname -- "$0")" && pwd)/_common.sh"

require_docker
require_env_file
validate_compose
require_commands gzip sha256sum realpath

root=$(backup_root)
timestamp=$(date +%Y%m%d-%H%M%S)
backup_dir="$root/$timestamp"
umask 077
mkdir -p "$backup_dir"

log "正在导出 MySQL。"
compose exec -T mysql sh -c 'MYSQL_PWD="$MYSQL_ROOT_PASSWORD" exec mysqldump --single-transaction --routines --events --triggers -uroot "$MYSQL_DB"' \
  | gzip -c > "$backup_dir/mysql.sql.gz"

log "正在导出 Redis。"
compose exec -T redis redis-cli --rdb /data/tcm-backup.rdb >/dev/null
compose cp redis:/data/tcm-backup.rdb "$backup_dir/redis.rdb"
compose exec -T redis rm -f /data/tcm-backup.rdb >/dev/null

log "正在创建 Neo4j 冷备份；图谱相关服务将短暂停止。"
restart_services() {
  compose up -d neo4j kg agent gateway edge >/dev/null || true
}
trap restart_services EXIT
compose stop edge gateway agent kg neo4j >/dev/null
docker run --rm --entrypoint neo4j-admin \
  -v tcm_agent_neo4j-data:/data \
  -v "$backup_dir:/backups" \
  neo4j:5-community database dump neo4j --to-path=/backups
trap - EXIT
restart_services

[ -f "$backup_dir/neo4j.dump" ] || die "Neo4j 备份文件未生成。"
(cd "$backup_dir" && sha256sum mysql.sql.gz redis.rdb neo4j.dump > checksums.sha256)
printf '{"created_at":"%s","compose_revision":"%s"}\n' \
  "$(date -Iseconds)" "$(git -C "$REPO_ROOT" rev-parse --short HEAD)" > "$backup_dir/manifest.json"

retention=$(env_value BACKUP_RETENTION_DAYS)
retention=${retention:-7}
[[ "$retention" =~ ^[0-9]+$ ]] || die "BACKUP_RETENTION_DAYS 必须为非负整数。"
find "$root" -mindepth 1 -maxdepth 1 -type d -mtime "+$retention" -exec rm -rf -- {} +
log "备份完成：$backup_dir"
