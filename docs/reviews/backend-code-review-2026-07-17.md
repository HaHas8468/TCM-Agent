# 后端代码审查问题清单

- 审查日期：2026-07-17
- 审查范围：`Backend/Medical_Agent` 的 FastAPI、Django、Agent、知识图谱及运维脚本
- 审查方式：静态代码审查；未修改业务代码，未替代生产环境渗透测试

## 整改优先级

- P0：可导致敏感数据泄露、身份冒用、越权修改诊疗数据的问题，必须在对外部署前修复。
- P1：可导致内存耗尽、数据不一致、服务不可用或部署失败的问题，应在下一轮发布前修复。
- P2：安全基线、质量和可维护性问题，应纳入技术债计划。

状态说明：`✅ 已修复` 表示本次已完成对应整改；未标记项仍待处理或仅完成部分整改。

## P0：安全与越权

### P0-01 密码以明文存储、校验和返回

- 证据：`fastapi_app/main.py` 的注册逻辑直接写入 `password`（461-465 行）；登录以 `patient.password != input_data.password` 和 `doctor.password != input_data.password` 比较（480-505 行）；医生资料接口返回 `password`（1164-1177 行）。
- 风险：数据库、备份、日志或接口响应一旦泄露，攻击者可直接获得账号密码；密码复用会扩大影响。
- 整改：使用 Argon2 或 bcrypt 哈希；比较使用安全验证函数；任何响应、日志、序列化器中均不得包含密码字段；修改密码需验证旧密码和强度策略。

### P0-02 数据库凭据和弱口令硬编码在源码中

- 证据：`scripts/test_db.py`、`check_schema.py`、`update_schema.py`、`fix_schema.py`、`add_default_landing.py` 均写有 MySQL root 密码；部分脚本写入 `Prototype123`、`123456` 等固定口令。
- 风险：仓库成员、归档或 Git 历史持有者均可获取数据库访问凭据。
- 整改：立即轮换已泄露的密码；删除硬编码凭据和默认账号；使用环境变量或密钥管理服务；将旧密钥从 Git 历史和发布包中清除。

### ✅ P0-03 订单操作仅检查“已登录”，未校验角色和资源归属

- 证据：`PUT /api/orders/{order_id}/start`、`finish`、`save` 及 `POST /diagnosis` 仅调用 `parse_token`，未校验医生角色、订单医生或患者归属（`fastapi_app/main.py` 751-881 行）。
- 风险：任意已登录用户可修改他人的就诊状态、诊断、方剂和病历。
- 整改：集中实现 RBAC 与资源级授权。医生仅能操作自己的订单；患者仅能读取自己的订单且不可完成诊疗；管理员权限独立管理。增加越权回归测试。

### ✅ P0-04 病历和订单详情接口存在匿名访问

- 证据：`GET /api/records`、`GET /api/records/{record_id}`、`GET /api/patient/{patient_id}/history`、`GET /api/orders/{order_id}` 无 `authorization` 参数或鉴权检查（923-1109 行）。
- 风险：匿名用户可读取患者身份、症状、舌脉、处方及病史。
- 整改：默认拒绝访问，逐接口显式授权；患者仅访问本人数据、医生仅访问其诊疗范围、管理员访问须审计。

### ✅ P0-05 患者可使用请求体中的任意 patient_id 创建订单

- 证据：`POST /api/orders` 只确认当前令牌角色为 patient，随后按 `input_data.patient_id` 查询患者，未比对令牌的 `role_id`（647-665 行）。
- 风险：患者可代替其他患者创建垃圾订单或污染其就诊记录。
- 整改：患者端忽略请求体 `patient_id`，一律从令牌提取；只有受控的管理员/工作人员流程可指定患者。

### ✅ P0-06 普通医生可访问用户管理接口

- 证据：`GET /api/admin/users` 仅要求 role 为 doctor（1204-1217 行）。
- 风险：任何医生可枚举全部患者与医生账户信息。
- 整改：引入 `admin`/`operator` 权限，并默认拒绝医生访问后台管理接口。

### ✅ P0-07 日志记录完整令牌和医疗隐私

- 证据：创建订单日志输出完整 `authorization` 和 `token_info`（650-655 行）；`tcm_agent.py` 会打印 session ID、patient ID 与用户问诊文本（2331-2354 行）。
- 风险：日志访问者可盗用令牌并获取医疗隐私；日志外传会造成合规事件。
- 整改：已移除 Agent/图谱运行路径中的原始问诊、会话/患者标识、症状、舌脉、诊断和处方调试输出；改为仅记录事件、耗时、数量与状态。Agent/图谱失败对客户端返回通用文案，详细排障信息仅保留在受保护的服务日志中。

### ✅ P0-08 Agent 服务的 API Key 为空时默认放行

- 证据：`agent_service/main.py` 的 `verify_api_key` 在 `API_KEY` 为空时直接 `return`（47-55 行）。
- 风险：漏配环境变量即公开 Agent、知识图谱和高成本模型接口。
- 整改：生产环境启动时强制校验密钥；Agent 仅绑定内部网络并通过网关访问；增加健康检查与配置校验。

## P1：稳定性、性能与数据一致性

### ✅ P1-01 LangGraph 内存检查点无淘汰，导致内存持续增长

- 证据：`tcm_agent.py` 创建 `MemorySaver()` 并作为 graph checkpointer（1969-2011 行）；每次调用以 `thread_id=session_id` 执行 graph（2331-2401 行）；清理线程只删除 `_SESSIONS` 字典，未清理 `MemorySaver`（2014-2046 行）。
- 风险：新会话会永久积累检查点、消息和结果，长期运行必然 OOM。
- 整改：改用 Redis/数据库检查点并设置 TTL；或关闭持久 checkpoint，仅保存带大小上限的会话摘要；添加会话总量、消息长度和内存水位监控。

### ✅ P1-02 异步接口执行同步阻塞操作

- 证据：`agent_service/main.py` 的 async 路由内直接调用同步 `tcm_agent_chat`（122-169 行）；FastAPI 路由还混用同步 SQLAlchemy。
- 风险：LLM、Neo4j 或网络慢时阻塞事件循环，请求排队导致超时、线程/内存堆积。
- 整改：将阻塞任务移至受限线程池、任务队列或独立 worker；设置并发阈值、超时、取消与熔断。

### ✅ P1-03 每请求创建线程池并可能启动 Node 子进程

- 证据：`kg_service.py` 在 `query_kg_for_symptoms` 中每次创建 `ThreadPoolExecutor(max_workers=3)`（426 行）；`call_case_kg_service` 每调用一次执行 `subprocess.run(["node", ...])`，默认 60 秒超时（793-836 行）。
- 风险：并发流量会快速产生线程和子进程，耗尽 CPU、内存和文件描述符。
- 整改：主图谱与医案图谱已统一为仅内部网络可访问的常驻 Node `kg` 服务，复用 Neo4j Driver；Python 侧改用复用 HTTP 客户端与全局有界并发控制，移除 `subprocess.run` 和每请求线程池。服务、客户端与 Node 层均设置可配置超时/并发上限。

### ✅ P1-04 完成订单分两次提交，无法保证原子性

- 证据：`finish_order` 先提交订单状态，再插入病历并再次提交（791-815 行）。
- 风险：第二次失败时订单已完成但病历丢失，形成数据不一致。
- 整改：订单更新和病历创建使用单一事务；异常时整体 rollback；增加失败注入测试。

### ✅ P1-05 挂号未校验排班、余号和并发冲突

- 证据：创建订单只确认患者和医生存在，直接插入订单（647-696 行），未读取 `ApiSchedule`、未递减 `available_slots`。
- 风险：可预约不存在的时段，同一时段可无限超卖。
- 整改：在事务中锁定排班记录，校验时间段和余号，使用条件更新原子扣减余号；建立唯一约束和幂等键。

### ✅ P1-06 队列、日期和筛选统计错误

- 证据：`get_doctor_queue` 接收 `date`、`department`、`period`，却查询医生全部订单，未使用这些条件（699-748 行）。
- 风险：医生队列及 KPI 不可信。
- 整改：在 SQL 查询层过滤日期、科室和时段，并为关键查询添加索引和测试。

### P1-07 全表加载、Python 过滤和 N+1 查询

- 证据：病历搜索 `db.query(ApiClinicRecord).all()` 后逐条查患者并在内存过滤（923-968 行）；队列和科室列表也逐条查询关联记录。
- 风险：数据增长后响应时间、数据库连接和内存占用都会恶化。
- 整改：使用 SQL WHERE、JOIN/eager loading、数据库分页及 `COUNT`；限制 `page_size`。

### ✅ P1-08 没有输入大小、分页和速率限制

- 证据：Agent 文本、病例正文、症状列表以及 page/page_size 基本没有上限校验。
- 风险：恶意大请求可消耗 LLM 费用、内存和数据库资源。
- 整改：网关及 Agent 模型已对文本、列表、日期/时间和分页设置长度、数量及范围限制；Nginx 请求体限制收敛为 128KB。Redis 限流默认限制登录 10 次/分钟/IP、普通写接口 30 次/分钟/身份、Agent 10 次/分钟/身份；超限返回 429 和 `Retry-After`。

## P1：架构与部署一致性

### P1-09 Django、FastAPI 和 Agent Service 并存且接口重复

- 证据：仓库同时存在 Django 项目、`fastapi_app`、`agent_service`；FastAPI 既导入 `remote_agent_client` 又直接 import Agent（`fastapi_app/main.py` 26-28 行）。
- 风险：部署入口不明确，认证、ORM、错误格式和依赖容易漂移；多进程会重复加载重型依赖。
- 整改：确定单一网关和单一 Agent 服务边界；网关仅经 HTTP/RPC 调用 Agent；移除未使用的服务和重复接口。

### P1-10 Django 与 FastAPI 默认连接不同数据库

- 证据：Django 默认为 `medical_agent`（`medical_agent/settings.py` 62-74 行），FastAPI 默认为 `traditional_medical`（`fastapi_app/main.py` 44-53 行）。
- 风险：漏配环境变量时两个服务读写不同数据源。
- 整改：集中配置并在启动时验证数据库名、迁移版本和连接；避免两套 ORM 管理同一业务表。

### P1-11 依赖版本冲突、环境不可复现

- 证据：根 `requirements.txt` 使用 LangChain 0.1/Pydantic 2.6；子 Agent 使用 LangChain 1.x/Pydantic 2.12；本地虚拟环境含 Windows 二进制。
- 风险：不同机器/容器安装结果不同，Linux 环境无法复用本地虚拟环境。
- 整改：拆分并锁定每个服务的依赖；使用 Linux Docker 多阶段构建；删除 `.venv`、`node_modules` 与 zip 归档，不纳入构建上下文。

## P2：安全基线、质量与可维护性

### ✅ P2-01 CORS 过宽

- 证据：两个 FastAPI 服务使用 `allow_origins=["*"]` 和 `allow_credentials=True`（`fastapi_app/main.py` 385-393 行）。
- 整改：生产环境使用明确的前端域名白名单，限制 methods 和 headers。

### ✅ P2-02 令牌仅保存在进程内存

- 证据：`TOKENS` 是全局字典；过期 token 仅在再次访问时清理（196-227 行）。
- 风险：多 worker/多实例不一致，重启即全部失效，未访问的过期 token 会滞留内存。
- 整改：使用短时 JWT 或 Redis 会话，支持登出、撤销和定期清理。

### ✅ P2-03 内部异常直接回显给客户端

- 证据：多处返回 `str(e)`，包括数据库、Neo4j 和 Agent 异常。
- 风险：泄露 SQL、表结构、服务地址和调用链。
- 整改：网关新增统一异常处理，验证失败、限流和未捕获异常分别返回稳定的 422、429/503、500 格式；Agent SSE 与图谱包装层不再回传原始异常、Neo4j/Node 输出或堆栈。

### P2-04 不安全默认配置

- 证据：Django `SECRET_KEY`、MySQL 和 Neo4j 均有默认值（`medical_agent/settings.py` 9 行；`knowledge_graph/neo4j_connection.py` 19-21 行）。
- 整改：生产模式缺失关键变量时立即启动失败；提供 `.env.example`，不提供可用默认口令。

### P2-05 医疗 AI 缺少安全护栏

- 证据：用户输入直接进入模型提示词，模型结果可影响诊断和方剂推荐。
- 风险：Prompt Injection、错误建议、费用失控和医疗合规风险。
- 整改：建立输入/输出策略校验、敏感信息脱敏、模型超时重试、人工确认和固定免责声明；不得将模型输出直接作为临床处方。

### P2-06 Django 子模块路由未注册

- 证据：根 URL 仅 include `api.urls`（`medical_agent/urls.py` 4-7 行），`diagnosis`、`herbs`、`prescription`、`medical_records` 的 ViewSet 无路由注册。
- 风险：代码不可达、文档与实际接口不一致。
- 整改：注册路由或删除废弃实现；在 CI 中生成 OpenAPI/路由快照并校验。

### P2-07 测试覆盖不足

- 证据：现有测试主要是脚本化连通性测试，未覆盖越权、事务回滚、抢号、会话回收、限流和错误脱敏。
- 整改：补充单元、集成与安全回归测试，并将关键用例接入 CI。

## 建议实施顺序

1. 立即下线匿名病历接口，修复订单资源授权，停止返回/记录密码和令牌，并轮换数据库密码。
2. 修复 LangGraph 会话存储，限制 Agent、线程池和子进程并发，增加超时与限流。
3. 将订单写入和病历创建合并为单一事务，落实排班余号原子扣减。
4. 收敛为单一服务边界，统一配置、依赖、数据库和认证方案。
5. 建立 CI 安全扫描、鉴权回归、负载测试与审计日志规范。
