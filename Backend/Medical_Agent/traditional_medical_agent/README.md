# 中医药智能诊疗 Agent 内核

> 本仓库为面向**后端同学**的 Agent 核心模块（LangGraph + Neo4j 双图谱），不直接面向终端用户。
> 后端需要将其封装为 HTTP/RPC 接口后，再供前端（Uni-app 患者端 / Vue3 医生 PC 端）调用。

---

## 1. 模块定位

| 角色 | 职责 |
|------|------|
| **本仓库** | 智能诊疗 Agent 核心：意图识别、症状提取、知识图谱查询、辨证、问诊引导、医案检索 |
| **后端（你/运维/服务端同学负责）** | 1) 鉴权与权限 2) 业务数据库（MySQL）CRUD 3) 包装本 Agent 为 REST/RPC API 4) 病历/处方/挂号业务逻辑 |
| **前端** | 通过后端 API 调用，不直接 import 本仓库 |

> ⚠️ **本仓库不包含** HTTP API、不包含前端代码、不包含 MySQL 业务库。  
> 业务数据库相关（病历、用户、挂号、聊天记录、医生信息等）由后端同学维护，Agent 只负责"调用一次 → 返一次结果"。

---

## 2. 目录结构

```
g:\中医药agent\
├── tcm_agent.py            # ★ Agent 核心（LangGraph 图 + 对外函数）
├── kg_service.py           # 知识图谱服务封装（neo4j_main / neo4j_case）
├── requirements.txt        # Python 依赖
├── 需求.txt                 # 产品需求文档（中文）
├── neo4j_main/             # 中药/方剂/证型图谱（Node.js 服务，subprocess 调用）
└── neo4j_case/             # 经典医案图谱（Node.js 服务，subprocess 调用）
```

---

## 3. 环境准备

### 3.1 Python 环境
- Python 3.10+（测试环境 3.13）
- 安装依赖：
  ```bash
  pip install -r requirements.txt
  ```

### 3.2 Node.js 子服务
两个知识图谱服务（`neo4j_main`、`neo4j_case`）是 Node.js 实现的，通过 `subprocess` 调用：
- **运行环境**：Node.js 16+（测试环境 v22+）
- **无需后端手工启动**：`kg_service.py` 内部会按需 spawn Node 进程调用
- **依赖配置**：两个目录各自维护 Neo4j 连接配置（详见各自 README）

### 3.3 环境变量（.env）
后端部署时需要将 `.env` 拷贝到运行目录：

```env
# 阿里云百炼 LLM（必需）
LLM_MODEL_32B=qwen3-32b
LLM_MODEL_SMALL=qwen-turbo
DASHSCOPE_API_KEY=sk-xxxxxxxx

# Neo4j 知识图谱（neo4j_main / neo4j_case 子服务内部读取）
NEO4J_URI=neo4j://127.0.0.1:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=xxxx
NEO4J_DATABASE=neo4j
```

> ⚠️ **不要把真实 .env 提交到代码仓库**！建议运维侧用环境变量/K8s Secret 注入。

---

## 4. 对外 API（后端需要集成的接口）

本 Agent 暴露**一个** Python 函数：

```python
from tcm_agent import tcm_agent_chat

result = tcm_agent_chat(
    session_id="s_001",          # 必填：会话 ID（同一问诊会话保持一致）
    patient_id="p_001",          # 必填：患者 ID
    user_input="我最近头痛，发冷",   # 必填：本次输入文本
    mode="normal",               # 可选：normal=首问 / follow-up=同一会话追问
    scene="guide",               # 可选：guide=患者导诊 / doctor=医生辅助
    patient_profile=None,        # 可选：患者档案（含过敏史）
)
```

### 4.1 参数详解

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `session_id` | str | ✅ | 同一问诊会话保持一致；不同患者/不同会话必须不同。Agent 用此维持上下文。 |
| `patient_id` | str | ✅ | 患者 ID，传给后端用于关联业务数据。Agent 内部暂不直接查询业务库。 |
| `user_input` | str | ✅ | 患者/医生输入的文本。后端不需要做任何预处理（标点、大小写都行）。 |
| `mode` | str | — | `"normal"`（默认，首次输入）或 `"follow-up"`（同会话继续提问）。后端根据是否是首问自行切换。 |
| `scene` | str | — | `"guide"`（默认，患者端导诊）或 `"doctor"`（医生 PC 端辅助）。后端根据场景调用。 |
| `patient_profile` | dict | — | 患者档案，至少包含 `allergy_history.herbs: List[str]`。**强烈建议传**，否则不会触发过敏药材过滤。 |

#### `patient_profile` 示例
```python
patient_profile = {
    "allergy_history": {
        "herbs": ["麻黄", "桂枝"]   # 过敏药材列表
    },
    # 可选：其他字段（如姓名/年龄/性别），Agent 当前只读取 allergy_history
}
```

### 4.2 返回值（dict）

后端拿到的永远是一个 `dict`，按 `status` 字段分支处理：

#### 状态 1：`status = "asking"`（信息不完整，需要继续追问）

```python
{
    "status": "asking",
    "response": "根据您目前描述的「头痛, 恶寒」等症状，初步建议您优先考虑挂【呼吸内科/中医内科】。\n\n为了能帮您更准确地辨证...再补充一下舌象、脉象吗？",
    "symptoms_info": {
        "symptoms": ["头痛", "恶寒"],
        "tongue": None,
        "pulse": None,
        "chief_complaint": "头痛",
        "is_complete": False,
        "missing_info": "舌象、脉象"
    }
}
```

> **前端怎么用**：把 `response` 直接展示给用户，让用户继续回答即可。
> 第 2 轮时用 `mode="follow-up"` + 同一个 `session_id` 再次调用。

#### 状态 2：`status = "diagnosed"`（诊断完成）

```python
{
    "status": "diagnosed",
    "response": "根据您的症状（头痛、恶寒、无汗、舌苔薄白、脉浮紧），辨证为风寒表实证...",
    "diagnosis_result": {
        "syndrome": "风寒表实证",                  # 证型
        "prescription": "麻黄汤",                 # 方剂名
        "ingredients": ["麻黄", "桂枝", "杏仁", "甘草"],   # 药材组成
        "department": "呼吸内科/中医内科",          # 推荐科室
        "allergy_warnings": ["含您过敏的麻黄"],    # 过敏警告（若有）
        "kg_warning": "知识图谱匹配度 0.78"        # 知识图谱置信提示
    }
}
```

> **后端怎么用**：将 `diagnosis_result` 入库，作为该次问诊的"AI 建议"草稿，等医生在 PC 端确认/调整后形成正式处方。

#### 状态 3：`status = "done"`（自定义查询/医案检索完成）

```python
{
    "status": "done",
    "response": "桂枝汤的组成：桂枝 9g、白芍 9g、生姜 9g、大枣 4 枚、甘草 6g...",
    # 注：自定义查询和医案检索没有 diagnosis_result 字段
}
```

> **后端怎么用**：`response` 直接转发给前端展示。

#### 状态 4：`status = "error"`（异常）

```python
{"status": "error", "response": "处理失败：xxx"}
```

> **后端怎么用**：返回 500，写日志，前端显示"系统繁忙请重试"。

---

## 5. 典型集成流程

### 5.1 FastAPI 包装示例（仅参考骨架，后端同学实现）

```python
from fastapi import FastAPI
from pydantic import BaseModel
from tcm_agent import tcm_agent_chat
from typing import Optional, List

app = FastAPI()


class ChatRequest(BaseModel):
    session_id: str
    patient_id: str
    user_input: str
    mode: str = "normal"
    scene: str = "guide"
    allergy_herbs: Optional[List[str]] = []


@app.post("/api/agent/chat")
def agent_chat(req: ChatRequest):
    patient_profile = {
        "allergy_history": {"herbs": req.allergy_herbs or []}
    }
    result = tcm_agent_chat(
        session_id=req.session_id,
        patient_id=req.patient_id,
        user_input=req.user_input,
        mode=req.mode,
        scene=req.scene,
        patient_profile=patient_profile,
    )
    return result
```

### 5.2 一次问诊的多轮调用模式

```
[前端]  POST /api/agent/chat  session_id=S1, user_input="头痛、发冷"
[后端]  → tcm_agent_chat(S1, p1, "头痛、发冷", "normal", "guide")
[Agent] status="asking", response="请问您现在还有其他不舒服吗？..."
[后端]  → 200 OK {status:"asking", response:"..."}
[前端]  渲染追问气泡

[前端]  POST /api/agent/chat  session_id=S1, user_input="没有其他不舒服"
[后端]  → tcm_agent_chat(S1, p1, "没有其他不舒服", "follow-up", "guide")
[Agent] status="asking", response="根据您描述的...建议挂【呼吸内科】..."
[后端]  → 200 OK {status:"asking", response:"..."}
[前端]  继续渲染

[前端]  POST /api/agent/chat  session_id=S1, user_input="舌淡红苔薄白，脉浮紧"
[后端]  → tcm_agent_chat(S1, p1, "舌淡红苔薄白，脉浮紧", "follow-up", "guide")
[Agent] status="diagnosed", diagnosis_result={syndrome:"风寒表实", prescription:"麻黄汤", ...}
[后端]  → 200 OK {status:"diagnosed", diagnosis_result:{...}}
[后端]  ★ 同时把 diagnosis_result 写入 MySQL 病历表（草稿状态）
[前端]  渲染诊断结果卡片 + 处方清单
```

### 5.3 session 生命周期
- **生成规则**：建议后端用 `f"{user_id}_{timestamp}"` 或 UUID
- **超时清理**：Agent 内部会话状态驻留内存（`_SESSIONS` 字典），**不会自动过期**。建议后端在以下时机主动清理：
  - 问诊结束（医生点击"完成"） → 调用 `del tcm_agent._SESSIONS[session_id]`
  - 超时 30 分钟无活动 → 后端 cron 清理
- **重启失效**：Agent 重启后会话状态全部丢失。**生产环境建议后端用 Redis 持久化 session**（自行实现，Agent 内部 `_SESSIONS` 需改造为可注入的 Storage）。

---

## 6. 集成要点 / 注意事项

### 6.1 性能
- 单次 LLM 调用 2~5 秒（症状提取 + 诊断 + 回复生成）
- 图谱查询 0.5~2 秒
- **建议后端**：
  - 异步返回（WebSocket / SSE）用户体验更好
  - 加入 30 秒超时，超时则前端降级为"系统繁忙"

### 6.2 资源消耗
- 每次 LLM 调用消耗 token（症状提取约 1k tokens，诊断+回复约 2k tokens）
- Neo4j 连接由 Node 子服务维护，**Agent 进程重启不影响图谱**
- **不要在循环里直接调**：在批量任务中要加并发控制（如 asyncio.Semaphore(3)）

### 6.3 安全
- **不要把 `.env` 提交到 git**！本仓库 `.env` 仅供参考，部署时用环境变量注入
- **`session_id` 必须防伪**：否则攻击者可以猜测他人会话 ID 偷听问诊内容
- **patient_id 必须由后端从 token 解析**，不能由前端直接传（防越权）

### 6.4 数据持久化
Agent 内部**不写数据库**。以下数据需要后端在调用前后自行落库：
- 每次 `tcm_agent_chat` 的入参和出参 → 落"问诊消息表"
- `diagnosis_result` → 落"诊断建议表"（待医生确认）
- 患者档案（含过敏史）→ 从业务库读取后传入 `patient_profile`

### 6.5 错误处理
- Agent 内部已 try/except 所有 LLM 和图谱调用，错误会转为 `status="error"`
- **后端应该额外监控**：连续 N 次 error 时告警（可能是 LLM quota 用尽 / Neo4j 挂了）

---

## 7. 部署建议

### 7.1 进程模型
- **推荐**：`gunicorn -w 2 -k uvicorn.workers.UvicornWorker` 启动 FastAPI 包装
- **不推荐**：把 Agent 跑在 serverless（如 AWS Lambda）—— LangGraph 状态驻留内存
- **资源**：单实例 2 核 4GB 足够支撑 50 QPS

### 7.2 健康检查
```python
@app.get("/api/agent/health")
def health():
    return {"status": "ok", "sessions_in_memory": len(tcm_agent._SESSIONS)}
```

### 7.3 监控指标
- 调用次数 / 状态分布（asking/diagnosed/done/error 各占多少）
- P50 / P95 / P99 响应时间
- `_SESSIONS` 字典大小（异常增长说明有泄漏）

---

## 8. 常见问题

**Q1: 患者问"我要吃麻黄吗？"，agent 会自动排除过敏药材吗？**  
A: 会。但**必须传 `patient_profile` 含 `allergy_history.herbs`**，否则 Agent 不知道患者过敏什么。

**Q2: 同 session_id 不同患者混用会怎样？**  
A: 会串台！session_id 是隔离会话的最小单位，**严禁** 不同 patient 复用 session_id。

**Q3: agent 会主动调用业务库（MySQL）吗？**  
A: 不会。Agent 只读 Neo4j（通过子服务）。所有 MySQL 操作由后端负责。

**Q4: 能支持流式输出吗？**  
A: 当前版本不支持（同步 LLM 调用）。如需流式，后端同学改 `tcm_agent.py` 中的 `ChatTongyi` 为 `streaming=True`。

**Q5: 删了测试文件（test_agent.py）后，怎么验证没退化？**  
A: 建议运维部署时跑一遍 `debug_*.py` 中的几个（先用 git 恢复 test_agent.py 跑回归测试，验证完再删除）。

---

## 9. 联系 / 责任分工

| 模块 | 负责人 | 内容 |
|------|--------|------|
| Agent 核心（本仓库） | 你（开发同学） | `tcm_agent.py`、`kg_service.py`、图谱子服务 |
| HTTP API + MySQL | 后端同学 | 包装 Agent、管理 session、调业务库 |
| 前端 | 前端同学 | 微信小程序 / Vue3 PC 后台 |
| 部署 / 监控 | 运维同学 | K8s / Docker / Prometheus |

**Agent 侧有任何行为不对的地方**（如返回字段缺失、状态机错误），**找 Agent 负责同学**；
**HTTP/数据库相关问题**（如 500 错误、SQL 慢查询），**找后端同学**。

---

## 10. 版本

- 当前版本：v1.0（2026-07-08）
- 知识图谱：`neo4j_main`（中药/方剂/证型）+ `neo4j_case`（经典医案）
- LLM：阿里云百炼 `qwen3-32b` + `qwen-turbo`
- Python：3.13（兼容 3.10+）
- Node.js：22+（仅供图谱子服务）
