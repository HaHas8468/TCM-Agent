# 前后端分离：前端 Docker Compose 部署

这三套配置均不启动后端、数据库或 Agent 服务。构建时会将 `VITE_API_BASE_URL` 写入前端静态资源，因此它必须是浏览器可访问的后端公网地址。

## 部署

```bash
cd TCM_Agent/frontend
cp .env.example .env
# 编辑 .env，填写实际后端地址和需要暴露的端口
docker compose up -d --build
```

以上命令同时部署患者端和医生端，访问地址分别为 `http://前端服务器IP:PATIENT_PORT/` 与 `http://前端服务器IP:DOCTOR_PORT/`。健康检查路径为 `/healthz`。

如只部署患者端，在 `frontend/ChineseMedicine` 目录中复制 `.env.example` 为 `.env` 后执行 `docker compose up -d --build`。如只部署医生端，在 `frontend/DoctorBackgroundSystem` 目录执行同样操作。

## 更新与核验

每次修改后端地址或前端代码后重新构建：

```bash
docker compose up -d --build
docker compose ps
curl -fsS http://127.0.0.1:8080/healthz
curl -fsS http://127.0.0.1:3000/healthz
```

后端必须放行前端来源的 CORS，例如前端端口为默认值时：

```env
CORS_ORIGINS=http://前端服务器IP:8080,http://前端服务器IP:3000
```

如使用域名和 HTTPS，应将外层 Nginx、Caddy 或 Traefik 分别反向代理到这两个端口，并将 HTTPS 域名加入后端 `CORS_ORIGINS`。不要将 API 密钥、数据库密码等后端机密写入 `.env.frontend`。
