# 前后端分离：前端 Docker Compose 部署

这三套配置均不启动后端、数据库或 Agent 服务。构建时会将 `VITE_API_BASE_URL` 写入前端静态资源，因此它必须是浏览器可访问的后端公网地址。

## Compose 入口

| 部署目标 | Compose 文件 | 工作目录 |
| --- | --- | --- |
| 同时部署患者端和医生端 | `frontend/compose.yaml` | `TCM_Agent/frontend` |
| 仅部署患者端 | `frontend/ChineseMedicine/compose.yaml` | `TCM_Agent/frontend/ChineseMedicine` |
| 仅部署医生端 | `frontend/DoctorBackgroundSystem/compose.yaml` | `TCM_Agent/frontend/DoctorBackgroundSystem` |

根目录 `TCM_Agent/compose.yaml` 为前后端全栈入口；`TCM_Agent/Backend/Medical_Agent/docker-compose.yml` 为后端独立入口。不要将它们与本指南的前端独立入口混用。

## 同时部署两个前端

```bash
cd TCM_Agent/frontend
cp .env.example .env
# 编辑 .env，填写实际后端地址和需要暴露的端口
docker compose up -d --build
```

以上命令同时部署患者端和医生端，默认访问地址分别为 `http://前端服务器IP:8080/` 与 `http://前端服务器IP:3000/`；端口可在 `.env` 的 `PATIENT_PORT`、`DOCTOR_PORT` 修改。健康检查路径为 `/healthz`。

## 单独部署一个前端

患者端：

```bash
cd TCM_Agent/frontend/ChineseMedicine
cp .env.example .env
# 编辑 .env 后执行
docker compose up -d --build
```

医生端：

```bash
cd TCM_Agent/frontend/DoctorBackgroundSystem
cp .env.example .env
# 编辑 .env 后执行
docker compose up -d --build
```

患者端默认暴露 `8080`，医生端默认暴露 `3000`。

## 后端地址与 CORS

`.env` 中的 `VITE_API_BASE_URL` 必须填写后端对浏览器开放的完整根地址，例如：

```env
VITE_API_BASE_URL=https://bcwfapi.hahalololos.top
```

不要填写 `/api`，也不要保留末尾 `/`。该变量在镜像构建阶段写入静态文件；修改后必须重新执行 `docker compose up -d --build`。

后端的 `CORS_ORIGINS` 必须包含前端页面的实际来源，而不是后端 API 地址：

```env
CORS_ORIGINS=http://前端服务器IP:8080,http://前端服务器IP:3000
```

使用域名与 HTTPS 时，替换为完整域名，例如 `https://patient.example.com,https://doctor.example.com`。CORS 值不可包含 `/api`、路径或末尾 `/`。后端独立 Compose 部署时编辑 `Backend/Medical_Agent/.env`，然后执行 `docker compose up -d --force-recreate gateway` 使配置生效。

## 更新与核验

每次修改后端地址或前端代码后重新构建：

```bash
docker compose up -d --build
docker compose ps
curl -fsS http://127.0.0.1:8080/healthz
curl -fsS http://127.0.0.1:3000/healthz
```

如使用域名和 HTTPS，应将外层 Nginx、Caddy 或 Traefik 分别反向代理到这两个端口，并将 HTTPS 域名加入后端 `CORS_ORIGINS`。不要将 API 密钥、数据库密码等后端机密写入前端目录的 `.env`。
