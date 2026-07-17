# Linux Docker Compose 全栈部署指南

## 部署目标

根目录 `compose.yaml` 会启动患者端、医生端、Nginx、FastAPI 网关、Agent、知识图谱服务、MySQL、Neo4j 和 Redis。只有 Nginx 映射宿主机端口：

| 地址 | 内容 |
| --- | --- |
| `https://<APP_DOMAIN>/` | 患者端 H5 |
| `https://<APP_DOMAIN>/doctor/` | 医生端 |
| `https://<APP_DOMAIN>/api/` | 统一业务 API |
| `https://<APP_DOMAIN>/healthz` | 边缘健康检查 |

## 前置条件

- Ubuntu 22.04+、Docker Engine 与 Docker Compose v2；当前用户必须能执行 `docker info`。
- 至少 8GB 内存、20GB 可用磁盘。低于此规格时不要通过删除服务来规避问题，应先调整资源规划。
- 域名 A/AAAA 记录已指向服务器公网 IP，云安全组与防火墙放行 TCP `80/443`。Certbot HTTP-01 验证依赖端口 80。
- 不要在同一服务器使用宿主机 Nginx、Apache 或其他程序占用 `80/443`。

Ubuntu 示例：

```bash
sudo apt-get update
sudo apt-get install -y ca-certificates curl git
# 按 Docker 官方文档安装 Docker Engine 与 docker-compose-plugin
sudo usermod -aG docker "$USER"
# 重新登录后确认
docker compose version
```

## 首次部署

```bash
git clone <repository-url> TCM_Agent
cd TCM_Agent
cp .env.example .env
chmod 600 .env
```

编辑 `.env`，至少填写：`APP_DOMAIN`、`LETSENCRYPT_EMAIL`、`MYSQL_PASSWORD`、`MYSQL_ROOT_PASSWORD`、`NEO4J_PASSWORD`、`AGENT_API_KEY`、`DASHSCOPE_API_KEY`。将 `CORS_ORIGINS` 设置为 `https://<APP_DOMAIN>`，不要保留 `example.com` 或 `replace-with-*`。

然后执行：

```bash
./scripts/deploy.sh
./scripts/status.sh
./scripts/install-renew-timer.sh
```

部署脚本先启动 HTTP 验证站点，使用共享 webroot 申请证书，然后自动切换为 HTTPS。若申请失败，检查 DNS 是否已生效、80 端口是否可从公网访问，以及 `./scripts/logs.sh edge` 的输出；不要把数据库密码或模型密钥贴到日志和工单中。

## 日常运维

```bash
./scripts/status.sh                 # 服务与边缘健康状态
./scripts/logs.sh gateway agent     # 跟踪指定服务日志
./scripts/renew-certs.sh            # 证书续期并 reload Nginx
./scripts/backup.sh                 # 数据备份，Neo4j 会有短暂停机
./scripts/restore.sh --from backups/20260717-120000 --confirm
./scripts/update.sh                 # 拉取 origin/main、部署并在失败时回滚
```

`backup.sh` 产生 `mysql.sql.gz`、`redis.rdb`、`neo4j.dump`、校验和与清单，默认保留 7 天。备份包含医疗数据：备份目录默认权限为仅属主可读写；应将其加密后转存到受控的异地存储。`restore.sh` 会覆盖现有三类数据库，必须人工核实备份时间后显式传入 `--confirm`。

`install-renew-timer.sh` 会安装每日执行的 systemd timer；可用 `systemctl list-timers tcm-agent-cert-renew.timer` 确认。首次部署不执行该命令也不影响当前证书，但需要自行安排 `renew-certs.sh` 的定时运行。

## 变更与回滚

发布前确保工作区干净并等待 GitHub Actions 的 `verify` 工作流通过。`update.sh` 仅允许在 `main` 分支运行，使用 fast-forward 更新；新版本健康检查失败时会恢复部署前 Git revision 并再次部署。手工排障时不要使用 `docker compose down -v`，该命令会删除命名卷中的业务数据。

## 资源与故障排查

各服务内存上限位于 `.env` 的 `*_MEMORY_LIMIT`。Neo4j 默认总额为 1536MB，其中堆 768MB、页缓存 512MB；Agent 默认 1536MB。内存不足时先查看 `docker stats` 与 `./scripts/logs.sh`，再在维护窗口调整配置并重新执行部署。

若前端接口失败，先确认浏览器请求为同源 `https://<APP_DOMAIN>/api/...`，再运行 `./scripts/status.sh`。SSE 响应由边缘 Nginx 关闭缓冲并保留 120 秒读取超时；不要在外层 CDN 或反向代理重新启用响应缓冲。
