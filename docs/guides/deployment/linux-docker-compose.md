# Linux Docker Compose 全栈部署指南

## 部署目标

根目录 `compose.yaml` 会启动患者端、医生端、Nginx、FastAPI 网关、Agent、知识图谱服务、MySQL、Neo4j 和 Redis。只有 Nginx 映射宿主机端口：

| 地址 | 内容 |
| --- | --- |
| `http://服务器IP:<PATIENT_PORT>/` | 患者端 H5 与同源 API |
| `http://服务器IP:<DOCTOR_PORT>/` | 医生端与同源 API |
| `http://服务器IP:<PATIENT_PORT>/healthz` | 患者端边缘健康检查 |
| `http://服务器IP:<DOCTOR_PORT>/healthz` | 医生端边缘健康检查 |

## 前置条件

- Ubuntu 22.04+、Docker Engine 与 Docker Compose v2；当前用户必须能执行 `docker info`。
- 至少 8GB 内存、20GB 可用磁盘。低于此规格时不要通过删除服务来规避问题，应先调整资源规划。
- 云安全组与防火墙放行 `PATIENT_PORT`（默认 8080）和 `DOCTOR_PORT`（默认 3000）；如仅供外层反向代理访问，应限制为代理服务器或本机可访问。
- 项目不占用 `80/443`，可与宿主机 Nginx、Caddy、Traefik 等反向代理共存；域名、HTTPS 证书由部署者自行维护。

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

编辑 `.env`，至少填写：`PATIENT_PORT`、`DOCTOR_PORT`、`MYSQL_PASSWORD`、`MYSQL_ROOT_PASSWORD`、`NEO4J_PASSWORD`、`AGENT_API_KEY`、`DASHSCOPE_API_KEY`。同源反向代理无需额外 CORS 配置；只有前端与 API 跨域时，才需要将实际前端来源加入 `CORS_ORIGINS`。

然后执行：

```bash
./scripts/deploy.sh
./scripts/status.sh
```

部署脚本会检查端口占用、启动服务，并分别验证两个边缘入口。若需域名、HTTPS 或统一入口，请由部署者在外层反向代理中将患者端、医生端分别转发至 `PATIENT_PORT`、`DOCTOR_PORT`；不要把数据库密码或模型密钥贴到日志和工单中。

## 端口访问与外层反向代理

本机或局域网测试不需要证书。完成 `.env` 的数据库、Neo4j、Agent 和模型配置后，直接执行：

```bash
docker compose up --build -d
docker compose ps
```

访问 `http://服务器IP:8080/` 打开患者端，访问 `http://服务器IP:3000/` 打开医生端；端口可通过 `.env` 调整。两个端口均将同源 `/api` 反向代理至内部网关，因此前端无需另配 API 地址。

外层反向代理可按部署者自身方案设置域名与 HTTPS：患者站点转发至 `http://127.0.0.1:<PATIENT_PORT>`，医生站点转发至 `http://127.0.0.1:<DOCTOR_PORT>`。请保留 `/api/` 的流式响应，关闭响应缓冲并设置至少 120 秒读取超时。

## 日常运维

```bash
./scripts/status.sh                 # 服务与边缘健康状态
./scripts/logs.sh gateway agent     # 跟踪指定服务日志
./scripts/backup.sh                 # 数据备份，Neo4j 会有短暂停机
./scripts/restore.sh --from backups/20260717-120000 --confirm
./scripts/update.sh                 # 拉取 origin/main、部署并在失败时回滚
```

`backup.sh` 产生 `mysql.sql.gz`、`redis.rdb`、`neo4j.dump`、校验和与清单，默认保留 7 天。备份包含医疗数据：备份目录默认权限为仅属主可读写；应将其加密后转存到受控的异地存储。`restore.sh` 会覆盖现有三类数据库，必须人工核实备份时间后显式传入 `--confirm`。


## 变更与回滚

发布前确保工作区干净并等待 GitHub Actions 的 `verify` 工作流通过。`update.sh` 仅允许在 `main` 分支运行，使用 fast-forward 更新；新版本健康检查失败时会恢复部署前 Git revision 并再次部署。手工排障时不要使用 `docker compose down -v`，该命令会删除命名卷中的业务数据。

## 资源与故障排查

各服务内存上限位于 `.env` 的 `*_MEMORY_LIMIT`。Neo4j 默认总额为 1536MB，其中堆 768MB、页缓存 512MB；Agent 默认 1536MB。内存不足时先查看 `docker stats` 与 `./scripts/logs.sh`，再在维护窗口调整配置并重新执行部署。

若前端接口失败，先确认浏览器请求为同源 `/api/...`，再运行 `./scripts/status.sh`。SSE 响应由边缘 Nginx 关闭缓冲并保留 120 秒读取超时；不要在外层 CDN 或反向代理重新启用响应缓冲。
