# TCM-Agent

> 基于知识图谱与智能体的中医药两级诊疗辅助系统，连接患者端预问诊、医生端接诊工作台与中医药知识图谱。

TCM-Agent 面向“线上预问诊 + 线下医生确认”的业务流程：患者可完成建档、症状采集和预约；医生可在工作台补全四诊信息、查询知识图谱并查看辅助诊疗建议。系统由患者端、医生端、业务后端和 Agent 内核组成。

## 核心能力

- 患者端：注册建档、智能预问诊、导诊挂号、诊疗历史和中药材科普。
- 医生端：登录、候诊队列、接诊工作台、病历管理、知识查询与 AI 辅助。
- 后端服务：患者、医生、预约、病历等业务 API，以及统一的 Agent 调用入口。
- Agent 与知识图谱：症状提取、辨证辅助、方剂/药材检索、医案检索和科室推荐。

## 架构

```text
患者端（Uni-app / Vue 3） ─┐
                           ├─ 后端（FastAPI / Django） ─ MySQL
医生端（Vue 3 / Vite）    ─┘              │
                                          └─ Agent（LangGraph） ─ Neo4j
```

## 仓库结构

```text
TCM_Agent/
├── compose.yaml                          # 前后端全栈部署入口
├── Backend/Medical_Agent/              # Django、FastAPI 与 Agent 服务
│   └── docker-compose.yml               # 后端独立部署入口
├── frontend/                            # 前端部署入口（同时部署两端）
│   ├── compose.yaml
│   ├── ChineseMedicine/                 # 患者端 Uni-app（Vue 3），可独立部署
│   └── DoctorBackgroundSystem/          # 医生端 Vue 3 工作台，可独立部署
└── docs/                               # 项目统一文档入口
```

## 快速开始

### 1. 全栈端口部署（推荐）

部署只需要 Docker Compose；项目不绑定域名、不签发证书。根目录 `.env` 是唯一生产配置来源：

```bash
cp .env.example .env
# 编辑 .env：填写端口、数据库/Neo4j/Agent/模型密钥
./scripts/deploy.sh
```

部署后，患者端为 `http://服务器IP:<PATIENT_PORT>/`，医生端为 `http://服务器IP:<DOCTOR_PORT>/`，两端 API 均为各自同源路径 `/api/`。如需绑定域名、HTTPS 或统一入口，请由部署者的 Nginx、Caddy、Traefik 等外层反向代理转发至对应端口。完整前置条件、备份、恢复和回滚见[Linux 全栈部署指南](docs/guides/deployment/linux-docker-compose.md)。

### 2. 前后端分离：仅部署前端

当前端与后端部署在不同服务器时，前端必须配置浏览器可访问的后端地址，并在后端的 `CORS_ORIGINS` 中放行前端访问地址。

| 目标 | 目录 | 命令 |
| --- | --- | --- |
| 同时部署患者端和医生端 | `frontend/` | `cp .env.example .env && docker compose up -d --build` |
| 仅部署患者端 | `frontend/ChineseMedicine/` | `cp .env.example .env && docker compose up -d --build` |
| 仅部署医生端 | `frontend/DoctorBackgroundSystem/` | `cp .env.example .env && docker compose up -d --build` |

各目录 `.env` 中的 `VITE_API_BASE_URL` 应填写后端完整地址，例如 `https://bcwfapi.hahalololos.top`，不要添加 `/api` 或结尾 `/`。完整说明见[前后端分离前端部署指南](docs/guides/deployment/frontend-only-docker-compose.md)。

### 3. 本地开发

后端本地开发可继续使用 `Backend/Medical_Agent/docker-compose.yml`；它只启动后端依赖与网关，不是生产部署入口。患者端和医生端分别执行：

```bash
cd frontend/ChineseMedicine && npm install && npm run dev:h5
cd frontend/DoctorBackgroundSystem && npm install && npm run dev
```

两套开发服务器均通过 `/api` 代理访问后端；如后端不在本机，可设置 `VITE_DEV_PROXY_TARGET`。小程序等非 H5 端使用 `VITE_API_BASE_URL` 配置完整后端地址。

### 4. Docker 一键启动

填写根目录 `.env` 中的数据库、Neo4j、Agent 与模型密钥后，可直接启动全部服务：

```bash
docker compose up --build -d
docker compose ps
```

患者端访问 `http://服务器IP:8080/`，医生端访问 `http://服务器IP:3000/`（端口可在 `.env` 调整）。两端均通过同源 `/api` 访问后端，不需要单独设置前端 API 地址；生产环境可由部署者在外层反向代理中自行绑定域名和 HTTPS。

## 文档

所有项目文档统一放在 [docs/](docs/README.md)：

- [完整功能需求](docs/requirements/完整功能需求说明.md)
- [前后端 API 规范 v2.3](docs/api/API接口规范.md)
- [系统测试用例](docs/testing/system-test-cases.md)
- [患者端视觉规范](docs/design/patient-visual-guidelines.md)
- [Linux Docker Compose 全栈部署指南](docs/guides/deployment/linux-docker-compose.md)
- [前后端分离前端部署指南](docs/guides/deployment/frontend-only-docker-compose.md)

## 技术栈

| 模块 | 技术 |
| --- | --- |
| 患者端 | Uni-app、Vue 3、Vite |
| 医生端 | Vue 3、Vite |
| 业务后端 | FastAPI、Django、SQLAlchemy |
| 数据与知识图谱 | MySQL、Neo4j |
| 智能体 | LangChain / LangGraph、LLM |

## 使用边界

本项目用于中医药诊疗辅助、教学与项目实践。系统输出不能替代执业医师的独立诊断、处方或紧急医疗决策；实际诊疗应由具备资质的医疗专业人员确认。

## 仓库描述

`基于知识图谱与智能体的中医药两级诊疗辅助系统，覆盖患者预问诊、医生接诊与中医药知识检索。`
