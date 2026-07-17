# 后端运行说明

业务运行时由 FastAPI 网关、独立 Agent 服务、常驻知识图谱服务、MySQL、Neo4j 与 Redis 组成。生产入口是仓库根目录的 `compose.yaml`，而不是 Django 开发服务器。

## 服务边界

- `gateway`：对外业务 API、鉴权、限流和 `/api` 路由。
- `agent`：仅内部访问的 AI 问诊服务。
- `kg`：仅内部访问的 Node 知识图谱查询服务。
- `mysql`、`neo4j`、`redis`：仅内部网络可访问的数据服务。
- `edge`：唯一暴露宿主机 `80/443` 的 Nginx，提供前端静态文件、HTTPS 和 API/SSE 反向代理。

## 生产部署

请使用[Linux Docker Compose 全栈部署指南](../deployment/linux-docker-compose.md)。根目录 `.env` 与 `.env.example` 是生产环境变量的唯一说明；不得将真实配置写进源码、脚本或 Git 历史。

## 本地后端开发

```bash
cd Backend/Medical_Agent
cp .env.example .env
docker compose up --build -d
docker compose ps
```

该 Compose 用于本地后端联调，保留 MySQL、Redis、Neo4j、Agent、图谱、网关和 Nginx。对外部署时改用仓库根目录的 `./scripts/deploy.sh`，避免前端、证书和环境变量出现两套配置。

## 验证

```bash
cd Backend/Medical_Agent
python -m pytest Unit_Test/test_security_regressions.py Unit_Test/test_stability_regressions.py -q
```

检查容器化生产配置：

```bash
cd ../..
TCM_ENV_FILE=.env.example docker compose --env-file .env.example -f compose.yaml config --quiet
```
