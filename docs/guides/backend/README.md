# 中医药诊疗智能体

基于知识图谱的中医药诊疗智能体后端项目，包含辨证论治、方剂推荐、中药材查询和医案检索四大核心功能。

## 技术栈

- **后端框架**: Django 5.0, FastAPI
- **知识图谱**: Neo4j
- **关系数据库**: MySQL
- **AI/NLP**: LangChain, OpenAI API
- **Python**: 3.10+

## 项目结构

```
medical_agent/
├── medical_agent/          # Django项目配置
├── api/                    # 基础API模块
├── diagnosis/              # 辨证论治模块
├── prescription/           # 方剂推荐模块
├── herbs/                  # 中药材知识库模块
├── medical_records/        # 医案检索模块
├── knowledge_graph/        # 知识图谱核心模块
├── fastapi_app/            # FastAPI接口层
├── scripts/                # 初始化脚本
├── requirements.txt        # 依赖文件
└── .env                    # 环境配置
```

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

修改 `.env` 文件，配置数据库连接信息：

```env
MYSQL_DB=medical_agent
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_HOST=localhost

NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password

OPENAI_API_KEY=your_api_key
```

### 3. 初始化数据库

```bash
# 创建MySQL表
python scripts/create_migrations.py

# 初始化Neo4j知识图谱
python scripts/init_db.py
```

### 4. 启动服务

#### Django开发服务器
```bash
python manage.py runserver 0.0.0.0:8000
```

#### FastAPI服务
```bash
python fastapi_app/main.py
```

### 5. Docker Compose 部署（推荐）

```bash
cd Backend/Medical_Agent
cp .env.example .env
# 填写 MySQL、Neo4j、Agent 与 DashScope 配置后执行
docker compose up --build -d
docker compose ps
```

Compose 会启动 MySQL、Redis、Neo4j、常驻 `kg` 图谱服务、Agent、网关与 Nginx；仅 Nginx 映射宿主机 `80` 端口。`kg` 仅在内部网络可访问。

限流参数可在 `.env` 调整：`RATE_LIMIT_LOGIN_PER_MINUTE`（默认 10/IP）、`RATE_LIMIT_WRITE_PER_MINUTE`（默认 30/身份）、`RATE_LIMIT_AGENT_PER_MINUTE`（默认 10/身份）和 `RATE_LIMIT_WINDOW_SECONDS`（默认 60）。

## API接口

### 辨证论治
- `POST /api/diagnosis/diagnosis/classify/` - 辨证分型
- `POST /api/diagnosis/diagnosis/extract_entities/` - 实体提取
- `GET /api/diagnosis/zheng-types/` - 获取所有证型

### 方剂推荐
- `POST /api/prescription/formulas/recommend/` - 根据证型推荐方剂
- `POST /api/prescription/formulas/detail/` - 获取方剂详情
- `GET /api/prescription/formulas/search/` - 搜索方剂

### 中药材查询
- `GET /api/herbs/herbs/search/` - 搜索中药材
- `POST /api/herbs/herbs/detail/` - 获取中药详情
- `GET /api/herbs/herbs/by-property/` - 按药性筛选
- `GET /api/herbs/herbs/by-meridian/` - 按归经筛选

### 医案检索
- `GET /api/records/records/search/` - 搜索医案
- `POST /api/records/records/detail/` - 获取医案详情

## 知识图谱结构

### 节点类型
- `症状` - 中医症状
- `证型` - 中医证型（如风寒感冒、气虚等）
- `方剂` - 经典方剂
- `中药` - 中药材
- `经络` - 十二经络
- `医案` - 经典医案

### 关系类型
- `属于` - 症状→证型
- `典型症状` - 证型→症状
- `典型舌象` - 证型→舌象
- `典型脉象` - 证型→脉象
- `组成` - 方剂→中药
- `主治` - 方剂→证型
- `归经` - 中药→经络
- `配伍` - 中药→中药

## License

MIT
