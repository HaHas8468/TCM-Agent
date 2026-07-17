#!/usr/bin/env bash
set -euo pipefail
source "$(cd -- "$(dirname -- "$0")" && pwd)/_common.sh"

usage() { echo "用法：$0 --from backups/时间戳 --confirm"; }
backup_input=""
confirmed=0
while [ "$#" -gt 0 ]; do
  case "$1" in
    --from) backup_input=${2:-}; shift 2 ;;
    --confirm) confirmed=1; shift ;;
    *) usage; exit 2 ;;
  esac
done
[ -n "$backup_input" ] || { usage; exit 2; }
[ "$confirmed" = "1" ] || die "恢复会覆盖现有 MySQL、Redis 和 Neo4j 数据，必须显式传入 --confirm。"

require_docker
require_env_file
validate_compose
require_commands gzip sha256sum realpath
backup_dir=$(assert_backup_path "$backup_input")
[ -f "$backup_dir/checksums.sha256" ] || die "备份目录缺少校验清单。"
(cd "$backup_dir" && sha256sum -c checksums.sha256)

log "停止服务并恢复数据。"
compose stop edge gateway agent kg neo4j redis mysql >/dev/null

log "恢复 MySQL。"
compose up -d mysql >/dev/null
wait_for_service mysql 180
compose exec -T mysql sh -c 'MYSQL_PWD="$MYSQL_ROOT_PASSWORD" mysql -uroot -e "DROP DATABASE IF EXISTS \`$MYSQL_DB\`; CREATE DATABASE \`$MYSQL_DB\`;"'
gzip -dc "$backup_dir/mysql.sql.gz" | compose exec -T mysql sh -c 'MYSQL_PWD="$MYSQL_ROOT_PASSWORD" exec mysql -uroot "$MYSQL_DB"'
compose stop mysql >/dev/null

log "恢复 Redis。"
docker run --rm -v tcm_agent_redis-data:/data -v "$backup_dir:/backup:ro" alpine:3.20 \
  sh -c 'rm -f /data/dump.rdb && cp /backup/redis.rdb /data/dump.rdb && chmod 660 /data/dump.rdb'

log "恢复 Neo4j。"
docker run --rm -v tcm_agent_neo4j-data:/data alpine:3.20 \
  sh -c 'rm -rf /data/databases/neo4j /data/transactions/neo4j'
docker run --rm --entrypoint neo4j-admin \
  -v tcm_agent_neo4j-data:/data \
  -v "$backup_dir:/backups:ro" \
  neo4j:5-community database load neo4j --from-path=/backups --overwrite-destination=true

compose up -d
for service in mysql neo4j redis kg agent gateway edge; do
  wait_for_service "$service" 240
done
log "数据恢复完成。"
