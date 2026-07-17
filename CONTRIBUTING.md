# 协作与交付约定

## 分支与提交

- `main` 仅保留通过 CI 的可部署版本；功能开发使用 `feature/<topic>`，修复使用 `fix/<topic>`，运维调整使用 `ops/<topic>`。
- 每个合并请求应只解决一个可验证的问题，提交信息使用 `feat:`、`fix:`、`docs:`、`ops:` 或 `test:` 前缀。
- 合并前先同步 `main`，由提交者解决冲突并完成本地验证；禁止用强制推送覆盖他人分支。

## 合并请求检查单

- 不提交 `.env`、密钥、令牌、数据库导出、`node_modules`、虚拟环境或构建缓存。
- API 变更同步更新 `docs/api/API接口规范.md` 和对应前后端联调说明。
- 后端变更运行安全/稳定性回归；患者端变更运行 `npm run test:sse` 与 H5 构建；医生端变更运行构建。
- 修改 Compose、Dockerfile、Nginx 或脚本后，运行 `docker compose --env-file .env -f compose.yaml config --quiet`。

## 发布责任

发布人仅从干净的 `main` 执行 `./scripts/update.sh` 或 `./scripts/deploy.sh`。生产密钥由服务器 `.env` 管理；任何疑似泄露的数据库、Neo4j、Agent 或模型密钥必须先轮换，再继续发布。
