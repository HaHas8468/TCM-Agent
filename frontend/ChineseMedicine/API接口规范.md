前后端 API 接口规范（v2.3）
============================================================
设计原则
============================================================
1. 字段精简：同类 ID 只用一个名称（patient_id / doctor_id / record_id / order_id / session_id），不在同一资源内重复出现嵌套 ID
2. 角色区分：患者 ID 用 patient_id，医生 ID 用 doctor_id（角色不同命名不同，便于后端权限校验）
3. 资源 ID：业务表用业务名_id（record_id 门诊病历 / order_id 挂号单）
4. 鉴权：所有需要登录的接口必须携带 Authorization: Bearer <token>
5. 时间：所有时间字段统一 ISO8601（YYYY-MM-DDTHH:mm:ss）
6. 分页：列表接口统一带 ?page=1&page_size=20
7. 响应：成功统一 { code: 0, data: {...} }，失败统一 { code: 非0, msg: "..." }

============================================================
一、鉴权相关（3 个接口）
============================================================

1.1 患者注册
POST /api/auth/register
请求：
{
  "username": "zhangsan",
  "password": "12345678",
  "confirm_password": "12345678"
}
响应：
{
  "code": 0,
  "data": { "patient_id": "P001" }
}

1.2 患者登录
POST /api/auth/login
请求：
{
  "username": "zhangsan",
  "password": "12345678"
}
响应：
{
  "code": 0,
  "data": {
    "token": "eyJ...",
    "patient_id": "P001",
    "name": "张三"
  }
}

1.3 医生登录
POST /api/doctor/auth/login
请求：
{
  "username": "doctor.lin",
  "password": "Prototype123"
}
响应：
{
  "code": 0,
  "data": {
    "token": "eyJ...",
    "doctor_id": "D001",
    "name": "林青和",
    "department": "中医内科",
    "default_landing": "queue"
  }
}

============================================================
二、患者档案（3 个接口）
============================================================

2.1 获取个人档案
GET /api/patient/profile
响应：
{
  "code": 0,
  "data": {
    "patient_id": "P001",
    "name": "张三",
    "gender": "女",
    "birth_date": "1995-06-15",
    "age": 31,
    "phone": "138****1234",
    "allergy_history": ["麻黄", "桂枝"]
  }
}

2.2 更新个人档案
PUT /api/patient/profile
请求：
{
  "name": "张三",
  "gender": "女",
  "birth_date": "1995-06-15",
  "age": 31,
  "phone": "138****1234",
  "allergy_history": ["麻黄", "桂枝"]
}
响应：{ "code": 0, "data": null }

2.3 （已删除：avatar 改为前端本地管理，详见附录 D）

============================================================
三、AI 智能挂号/问诊（2 个接口）
============================================================

3.1 AI 问诊多轮对话
POST /api/agent/chat
请求：
{
  "session_id": "S20260710001",     // 同一问诊保持一致
  "patient_id": "P001",            // 由后端从 token 解析，前端可省
  "user_input": "我最近头痛，发冷",
  "mode": "normal",                 // normal=首问 / follow-up=追问
  "scene": "guide",                 // guide=患者 / doctor=医生
  "therapy": "辛温解表，宣肺平喘",    // 疗法（存入 api_clinicrecord.chief_complaint）
  "precautions": "忌生冷，注意保暖"   // 注意事项（存入 api_clinicrecord.history_of_present_illness）
}
响应（status=asking 信息不完整）：
{
  "code": 0,
  "data": {
    "status": "asking",
    "response": "根据您目前描述的「头痛, 恶寒」等症状，初步建议您优先考虑挂【呼吸内科/中医内科】...",
    "session_id": "S20260710001",
    "finish": false,
    "ask_round": 1
  }
}
响应（status=diagnosed 诊断完成）：
{
  "code": 0,
  "data": {
    "status": "diagnosed",
    "session_id": "S20260710001",
    "response": "根据您症状，辨证为风寒表实证，建议使用麻黄汤。",
    "finish": true,
    "diagnosis": {
      "syndrome": "风寒表实证",
      "prescription": "麻黄汤",
      "ingredients": ["麻黄", "桂枝", "杏仁", "甘草"],
      "department": "呼吸内科/中医内科",
      "allergy_warnings": ["麻黄"]
    }
  }
}
响应（status=query_answer 查询回答）：
{
  "code": 0,
  "data": {
    "status": "query_answer",
    "response": "关于「人参」的中药信息：\n\n## 人参\n...",
    "session_id": "S20260710001",
    "finish": false
  }
}
响应（status=error）：
{
  "code": 0,
  "data": {
    "status": "error",
    "response": "处理失败：xxx",
    "finish": false
  }
}

3.2 AI 问诊流式对话（SSE）
POST /api/agent/chat/stream
请求：同 3.1
响应（Server-Sent Events）：
data: 根据您目前描述的
data: 「头痛, 恶寒」等症状，
data: 初步建议您优先考虑挂
...
data: [METADATA]
data: {"finish": false, "status": "asking"}
data: [DONE]

finish 参数说明：
- true：问诊已结束（仅 status=diagnosed 时为 true），前端应显示结束弹窗
- false：问诊进行中或查询回答，无需弹窗

============================================================
四、挂号（3 个接口）
============================================================

4.1 科室列表（含医生）
GET /api/departments
响应：
{
  "code": 0,
  "data": [
    {
      "department": "中医内科",
      "doctors": [
        { "doctor_id": "D001", "name": "林青和", "specialty": "呼吸系统疾病" },
        { "doctor_id": "D002", "name": "周闻素", "specialty": "脾胃病" }
      ]
    }
  ]
}

4.2 医生可预约时段
GET /api/doctors/{doctor_id}/slots?date=2026-07-10
响应：
{
  "code": 0,
  "data": {
    "doctor_id": "D001",
    "date": "2026-07-10",
    "available_slots": ["09:00", "10:00", "14:00", "15:00"]
  }
}

4.3 创建挂号订单
POST /api/orders
请求：
{
  "patient_id": "P001",
  "doctor_id": "D001",
  "department": "中医内科",
  "date": "2026-07-10",
  "time": "09:00",
  "source": "smart"          // smart=智能挂号推荐 / direct=直接挂号
}
响应：
{
  "code": 0,
  "data": {
    "order_id": "O20260710001",
    "status": "pending",      // pending=待接诊 / ongoing=问诊中 / finished=已结束 / cancelled=已取消
    "doctor_id": "D001",
    "date": "2026-07-10",
    "time": "09:00"
  }
}

============================================================
五、医生接诊（4 个接口）
============================================================

5.1 今日接诊队列
GET /api/doctor/queue?date=2026-07-10&department=中医内科&period=all
响应：
{
  "code": 0,
  "data": [
    {
      "order_id": "O20260710001",
      "patient_id": "P001",
      "patient_name": "张三",
      "department": "中医内科",
      "time": "09:00",
      "status": "pending"
    }
  ],
  "kpi": {
    "today_total": 20,
    "pending": 5,
    "ongoing": 3,
    "finished": 12
  }
}

5.2 接诊（开始问诊）
PUT /api/orders/{order_id}/start
响应：
{
  "code": 0,
  "data": { "order_id": "O20260710001", "status": "ongoing" }
}

5.3 完成接诊
PUT /api/orders/{order_id}/finish
请求：
{
  "syndrome": "风寒表实证",
  "prescription": "麻黄汤",
  "ingredients": ["麻黄", "桂枝", "杏仁", "甘草"],
  "advice": "避风寒，清淡饮食",
  "therapy": "辛温解表，宣肺平喘",      // 疗法（存入 api_clinicrecord.chief_complaint）
  "precautions": "忌生冷，注意保暖"     // 注意事项（存入 api_clinicrecord.history_of_present_illness）
}
响应：
{
  "code": 0,
  "data": { "order_id": "O20260710001", "status": "finished" }
}

5.4 暂存（不结束）
PUT /api/orders/{order_id}/save
请求：同 5.3 的诊断字段（部分可空）
响应：{ "code": 0, "data": { "order_id": "O20260710001", "status": "ongoing" } }

5.5 查询订单所属患者
GET /api/orders/{order_id}/patient
用途：通过 order_id 查 api_order 拿到 patient_id，避免队列/详情接口做联表。
响应：
{
  "code": 0,
  "data": {
    "order_id": "O20260717001",
    "patient_id": 3
  }
}
说明：
- patient_id 类型按后端实际返回（数字或字符串均可），前端不强类型
- 拿到 patient_id 后调用 7.3（GET /api/patient/{patient_id}/history）获取患者档案与历史病历

============================================================
六、面诊四诊补录（1 个接口）
============================================================

6.1 提交四诊信息
POST /api/orders/{order_id}/diagnosis
请求：
{
  "chief_complaint": "头痛3天",
  "present_illness": "受凉后出现头痛，恶寒，无汗",
  "tongue": "舌淡红苔薄白",
  "pulse": "脉浮紧",
  "symptoms": ["头痛", "恶寒", "无汗"],
  "signs": "体温37.5℃",
  "other": "无既往史"
}
响应：
{
  "code": 0,
  "data": { "order_id": "O20260710001" }
}

============================================================
七、病历管理（4 个接口）
============================================================

7.1 病历检索
GET /api/records?name=张三&patient_id=P001&syndrome=风寒&date_from=2026-01-01&date_to=2026-12-31&page=1&page_size=20
响应：
{
  "code": 0,
  "data": {
    "list": [
      {
        "record_id": "R001",
        "patient": { "patient_id": "P001", "name": "张三" },
        "syndrome": "风寒表实证",
        "prescription": "麻黄汤",
        "therapy": "辛温解表，宣肺平喘",
        "precautions": "忌生冷，注意保暖",
        "date": "2026-07-10T09:30:00"
      }
    ],
    "total": 5,
    "page": 1,
    "page_size": 20
  }
}

7.2 单次门诊病历详情
GET /api/records/{record_id}
响应：
{
  "code": 0,
  "data": {
    "record_id": "R001",
    "patient": { "patient_id": "P001", "name": "张三", "gender": "女", "age": 31 },
    "doctor": { "doctor_id": "D001", "name": "林青和" },
    "chief_complaint": "头痛3天",
    "present_illness": "受凉后出现头痛，恶寒，无汗",
    "tongue": "舌淡红苔薄白",
    "pulse": "脉浮紧",
    "syndrome": "风寒表实证",
    "treatment_principle": "辛温解表、宣肺平喘",
    "prescription": "麻黄汤",
    "ingredients": ["麻黄", "桂枝", "杏仁", "甘草"],
    "advice": "避风寒，清淡饮食",
    "date": "2026-07-10T09:30:00"
  }
}

7.3 患者历史病历（含历史辨证/处方）
GET /api/patient/{patient_id}/history
响应：
{
  "code": 0,
  "data": {
    "patient_id": "P001",
    "name": "张三",
    "gender": "女",
    "age": 31,
    "phone": "138****1234",
    "history_syndromes": [
      { "date": "2026-07-10", "syndrome": "风寒表实证", "prescription": "麻黄汤" },
      { "date": "2026-05-15", "syndrome": "脾胃虚寒", "prescription": "理中汤" }
    ],
    "allergy_history": ["麻黄", "桂枝"]
  }
}

7.4 患者基本信息（按业务号）
GET /api/patients/bypatientid/{patient_id}/basic
用途：通过 patient_id（业务号）查询患者基本档案，供医生端工作台患者基本信息卡使用。
响应：
{
  "code": 0,
  "data": {
    "patient_id": "P001",
    "gender": "男",
    "age": 35,
    "allergy_history": ["花粉", "海鲜"]
  }
}

============================================================
八、AI 推荐弹窗（前端调用 /api/agent/chat，详见附录 F）
============================================================
优化可做：前端添加推荐按钮：1.相似药材；2.相似病案。


============================================================
九、历史诊断（患者端，1 个接口）
============================================================

9.1 患者历史诊断列表
GET /api/patient/diagnosis-history?status=all
状态：all=全部 / pending=未开始 / finished=已结束
响应：
{
  "code": 0,
  "data": [
    {
      "order_id": "O20260710001",
      "doctor": { "doctor_id": "D001", "name": "林青和" },
      "department": "中医内科",
      "date": "2026-07-10T09:00:00",
      "status": "finished",
      "symptoms_summary": "头痛、恶寒",
      "diagnosis_summary": "风寒表实证，麻黄汤",
      "advice_list": ["避风寒", "清淡饮食"]
    }
  ]
}

9.2 历史诊断详情
GET /api/orders/{order_id}
响应：同 7.2（病历详情）

============================================================
十、信息中心同步（1 个接口）
============================================================

10.1 同步最近一次诊断
GET /api/patient/latest-diagnosis
响应：
{
  "code": 0,
  "data": {
    "order_id": "O20260710001",
    "syndrome": "风寒表实证",
    "prescription": "麻黄汤",
    "department": "中医内科",
    "diagnosis_basis": "根据您症状，辨证为风寒表实证",
    "advice_list": ["避风寒", "清淡饮食"],
    "sync_time": "2026-07-10T10:30:00"
  }
}

============================================================
十一、医生设置（2 个接口）
============================================================

11.1 获取医生个人资料
GET /api/doctor/profile
响应：
{
  "code": 0,
  "data": {
    "doctor_id": "D001",
    "name": "林青和",
    "role": "doctor",
    "username": "doctor.lin",
    "phone": "139****5678",
    "department": "中医内科",
    "duty_time": "周一至周五 8:00-17:00",
    "specialty": "呼吸系统疾病",
    "bio": "从事中医临床20年..."
  }
}

11.2 更新医生个人资料
PUT /api/doctor/profile
请求：同 11.1 字段（可只传需要修改的）
响应：{ "code": 0, "data": null }

============================================================
十二、知识图谱医案管理（2 个接口）
============================================================

12.1 按医生姓名/ID 查询医案
GET /api/knowledge/case/doctor
请求头：Authorization: Bearer <医生Token>
查询参数：
- doctor: 医生姓名关键词（模糊匹配）
- doctor_id: 医生节点 ID（精确匹配）
- limit: 返回条数，默认 10，最大 50
注：doctor 和 doctor_id 至少传一个

响应：
{
  "code": 0,
  "data": [
    {
      "caseId": "CASE_abc123",
      "title": "刘渡舟治疗风寒感冒医案",
      "summary": "患者男，45岁，外感风寒...",
      "sourceUrl": "https://example.com/case/123.html",
      "publishDate": "2023-05-12",
      "diseases": ["感冒", "风寒表证"],
      "syndromes": ["风寒束表"],
      "formulas": ["麻黄汤", "桂枝汤"],
      "treatmentMethods": ["解表散寒", "宣肺平喘"],
      "doctors": [
        { "name": "刘渡舟", "id": "DOCTOR_b54c2314bc9a5698" }
      ]
    }
  ]
}

12.2 新增医案
POST /api/knowledge/case
请求头：Authorization: Bearer <医生Token>
请求：
{
  "title": "刘渡舟治疗风寒感冒医案",
  "summary": "患者男，45岁，外感风寒...",
  "rawText": "完整医案原文...",
  "sourceUrl": "https://example.com/case/123.html",
  "publishDate": "2023-05-12",
  "author": "前端录入",
  "channel": "经典医案",
  "diseases": [
    { "name": "感冒" },
    "风寒表证"
  ],
  "syndromes": [
    { "name": "风寒束表", "id": "SYNDROME_abc123" }
  ],
  "symptoms": ["头痛", "恶寒", "无汗"],
  "formulas": [
    { "name": "麻黄汤" }
  ],
  "treatmentMethods": ["解表散寒"],
  "doctors": [
    { "name": "刘渡舟", "id": "DOCTOR_b54c2314bc9a5698" }
  ]
}

实体字段格式说明（支持三种形式）：
- 字符串："头痛"
- 字符串数组：["头痛", "恶寒"]
- 对象数组：[{ "name": "刘渡舟", "id": "DOCTOR_xxx" }]

响应：
{
  "code": 0,
  "data": {
    "caseId": "CASE_901020_manual_1709234567_123",
    "sourceId": "901020_manual_1709234567_123",
    "linked": {
      "diseases": 2,
      "syndromes": 1,
      "symptoms": 3,
      "formulas": 1,
      "treatmentMethods": 1,
      "doctors": 1
    }
  }
}

============================================================
附录 A：ID 字段使用规范
============================================================
- patient_id：仅出现在"患者"角色相关资源（档案、病历、挂号单）
- doctor_id：仅出现在"医生"角色相关资源（队列、设置、统计）
- order_id：挂号订单主键
- record_id：门诊病历主键
- case_id：医案主键（来自 neo4j_case 图谱）
- session_id：Agent 会话 ID（同一问诊保持一致）
- 嵌套对象（如 patient / doctor）内不再重复外层的 ID

============================================================
附录 B：枚举值
============================================================
- order.status：pending / ongoing / finished / cancelled
- scene：guide（患者） / doctor（医生）
- mode：normal / follow-up
- gender：男 / 女

============================================================
附录 C：接口总览（28 个）
============================================================
| # | 路径 | 方法 | 用途 |
|---|------|------|------|
| 1 | /api/auth/register | POST | 患者注册 |
| 2 | /api/auth/login | POST | 患者登录 |
| 3 | /api/doctor/auth/login | POST | 医生登录 |
| 4 | /api/patient/profile | GET | 获取患者档案 |
| 5 | /api/patient/profile | PUT | 更新患者档案 |
| 6 | /api/agent/chat | POST | Agent 统一入口（多轮/自定义查询/医案） |
| 7 | /api/agent/chat/stream | POST | Agent 流式对话（SSE） |
| 8 | /api/departments | GET | 科室+医生列表 |
| 9 | /api/doctors/{id}/slots | GET | 医生可预约时段 |
| 10 | /api/orders | POST | 创建挂号单 |
| 11 | /api/doctor/queue | GET | 接诊队列 |
| 12 | /api/orders/{id}/start | PUT | 开始接诊 |
| 13 | /api/orders/{id}/finish | PUT | 完成接诊 |
| 14 | /api/orders/{id}/save | PUT | 暂存 |
| 15 | /api/orders/{id}/diagnosis | POST | 提交四诊信息 |
| 16 | /api/orders/{id}/patient | GET | 查询订单所属患者 |
| 17 | /api/records | GET | 病历检索 |
| 18 | /api/records/{id} | GET | 病历详情 |
| 19 | /api/patient/{id}/history | GET | 患者历史病历 |
| 20 | /api/patients/bypatientid/{id}/basic | GET | 患者基本信息（按业务号） |
| 21 | /api/patient/diagnosis-history | GET | 历史诊断列表 |
| 22 | /api/orders/{id} | GET | 挂号/病历详情 |
| 23 | /api/patient/latest-diagnosis | GET | 最近一次诊断 |
| 24 | /api/doctor/profile | GET/PUT | 医生资料 |
| 25 | /api/admin/users | GET | 用户管理 |
| 26 | /api/knowledge/case/doctor | GET | 按医生姓名/ID查询医案 |
| 27 | /api/knowledge/case | POST | 新增医案 |

附录 D：avatar 本地管理方案
============================================================


前端实现要点：
1. 默认头像：本草问方前端 `config/user-profile.js` 内置 5~8 个静态资源路径
2. 存储：`uni.setStorageSync('user_avatar', 'avatar1')` 持久化到本地
3. 选择：点击网格中某个头像 → 更新本地存储 → uni.previewImage 预览

附录 D：算法核心 (tcm_agent) 与 API 规范的字段映射
============================================================
后端同学在 FastAPI 中调 tcm_agent_chat() 后，需要做以下映射才能匹配 API 规范：

D.1 响应包装
```python
# tcm_agent_chat() 原始返回：
{ "status": "asking", "response": "...", "symptoms_info": {...} }

# API 规范要求：
{ "code": 0, "data": { "status": "asking", "response": "...", "session_id": "..." } }
```

D.2 字段名映射表
| tcm_agent_chat 返回 | API 规范字段 | 备注 |
|---------------------|-------------|------|
| status | data.status | 直接透传 |
| response | data.response | 直接透传 |
| symptoms_info | （无需返回） | 仅供后端内部判断，不暴露 |
| diagnosis_result | data.diagnosis | **改名** |
| — | data.session_id | 后端自行生成/管理 |
| — | code / data | 后端包装 |

D.3 后端 FastAPI 唯一适配函数（极简版）
```python
from fastapi import FastAPI, Header
from pydantic import BaseModel
from typing import Optional
import time
from tcm_agent import tcm_agent_chat

app = FastAPI()


class AgentChatRequest(BaseModel):
    session_id: Optional[str] = None
    user_input: str
    mode: str = "normal"      # normal=首问 / follow-up=追问
    scene: str = "guide"       # guide=患者 / doctor=医生


def parse_token(authorization: str) -> dict:
    """伪代码：实际用 JWT 解析"""
    return {"patient_id": "P001", "role": "patient"}


@app.post("/api/agent/chat")
def agent_chat(req: AgentChatRequest, authorization: str = Header(...)):
    info = parse_token(authorization)
    patient_id = info["patient_id"]
    patient_profile = db.get_patient_profile(patient_id)  # 含 allergy_history.herbs
    
    # session_id：前端传则用前端的，否则后端生成
    sid = req.session_id or f"S_{patient_id}_{int(time.time())}"
    
    # 直接调 agent 唯一入口
    raw = tcm_agent_chat(
        session_id=sid,
        patient_id=patient_id,
        user_input=req.user_input,
        mode=req.mode,
        scene=req.scene,
        patient_profile=patient_profile,
    )
    
    # 适配层：包成 { code, data }，改键名
    response_data = {
        "status": raw.get("status"),
        "response": raw.get("response"),
        "session_id": sid,
    }
    if raw.get("status") == "diagnosed" and "diagnosis_result" in raw:
        response_data["diagnosis"] = raw["diagnosis_result"]
    
    return {"code": 0, "data": response_data}
```

D.4 关键差异总结
| 维度 | tcm_agent_chat 原生 | API 规范要求 | 处理位置 |
|------|-------------------|------------|---------|
| 响应包装 | 平铺 dict | {code, data} | 后端 FastAPI 包装 |
| 诊断键名 | diagnosis_result | diagnosis | 后端 .rename() |
| session_id | 不返回 | 必须回传 | 后端生成/缓存 |
| 鉴权 | 无（信任调用方） | 需 token 解析 patient_id | 后端中间件 |
| 业务持久化 | 不写库 | 档案/病历/挂号全在 MySQL | 后端 MySQL |
| 弹窗/推荐| 无 | 全部走同一接口 | 前端控制 user_input |

附录 E：Agent 统一入口使用约定
============================================================
所有 Agent 类需求（多轮问诊 / 中药功效查询 / 医案查询 / 知识科普 / 弹窗）**统一调 /api/agent/chat**。
Agent 内部 Supervisor 自动识别意图，前端无需关心。

E.1 各类场景的 user_input 模板（前端参考）

场景 1：患者多轮问诊（主对话）
- 入口：患者端主页 → 智能挂号按钮
- session_id 规则：f"S_P_{patient_id}_{int(time.time())}"（一次挂号一个 session）
- mode：normal（首问） / follow-up（追问）
- user_input：患者输入原文

场景 2：医生主对话（工作台左侧 ConversationPanel）
- 入口：医生 PC 端问诊工作台
- session_id 规则：f"S_D_{order_id}"（一次接诊一个 session）
- mode：normal / follow-up
- scene：doctor
- user_input：医生输入原文

场景 3：医生手动知识库查询（工作台右侧 AgentChatPanel）
- 入口：医生在右侧"智能助手"对话栏输入
- session_id 规则：f"S_Q_{order_id}"（独立 session，不污染主对话）
- scene：doctor
- user_input 示例：
  - "麻黄的功效、配伍禁忌、相似药材"
  - "风寒夹湿证经典医案"
  - "桂枝汤加减方案"
  - "什么是风寒表实证"

场景 4：医生点"查看医案详情"弹窗
- 入口：医生点 AiAssistPanel 中的医案条目
- session_id 规则：f"S_CASE_{case_id}"（每个弹窗一个独立 session）
- scene：doctor
- user_input："请详细介绍医案「{case_title}」的辨证、用药、医家"

场景 5：医生点"查看药材详情"弹窗
- 入口：医生点 AiAssistPanel 中的相似药材条目
- session_id 规则：f"S_HERB_{herb_name}"（每个弹窗一个独立 session）
- scene：doctor
- user_input："请详细介绍{herb_name}的功效、用法、禁忌、配伍"

场景 6：医生点 4 个快捷问题按钮
- 入口：AgentChatPanel 上的 4 个按钮
- session_id 规则：复用场景 3 的 session（与手动查询同源）
- scene：doctor
- user_input 模板（前端维护）：
  ```
  补采缺口：  "请基于当前患者信息，列出还需要补采哪些四诊信息"
  辨证与治法："请总结当前患者的辨证结论、治法和推荐方剂"
  既往病历：  "请列出该患者的历史病历和既往处方"
  方剂用法：  "请详细说明当前推荐方剂的组成、用法和注意事项"
  ```

E.2 关键设计点
1. **session 隔离**：弹窗用独立 session_id，避免污染主对话上下文
2. **后端无状态**：Agent 自身不维护 session 状态（_SESSIONS 字典仅用于内部多轮追问），session_id 生命周期由前端控制
3. **scene 由前端传**：guide / doctor 决定 LLM 的语气和话术
4. **意图识别交给 Supervisor**：前端不需要判断"这条消息是问诊还是查询"，Agent 内部自动分类

E.3 接口调用的 5 种状态（data.status）
| status | 含义 | finish | 前端处理 |
|--------|------|--------|---------|
| asking | 信息不完整，需要继续追问 | false | 渲染追问气泡，保留用户上下文，等待下一轮 |
| diagnosed | 诊断完成 | true | 渲染诊断卡片（辨证/方剂/药材/科室/过敏警告），显示结束弹窗 |
| query_answer | 自定义查询/医案/问候/无关内容 | false | 渲染纯文本回答 |
| done | 其他完成状态 | false | 渲染纯文本回答 |
| error | 处理失败 | false | 显示"系统繁忙请重试"，可重发 |

finish 参数说明：
- 仅当 status=diagnosed（诊断完成）时为 true
- 其他状态均为 false
- 前端应在 finish=true 时显示问诊结束弹窗
