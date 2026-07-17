# 患者端 API 对接测试报告

- 测试时间：2026-07-12
- 后端地址：`http://10.250.215.156:8000`（中医药诊疗智能体 API v1.0.0，FastAPI，23 个端点）
- 测试方式：Node 22 `fetch` 复刻 `config/http.js` 请求层（Bearer + `{code,data}` 解包），并直接调用项目内真实 mappers 对**真实后端响应**做字段映射校验。
- 结果：**14 / 14 既有接口通过**；智能挂号已迁移到新增 SSE 接口，需在后端发布 `/api/agent/chat/stream` 后完成流式联调。

## 一、各接口测试结果

| # | 接口 | 方法 | 结果 | 关键发现 |
|---|------|------|------|----------|
| 1 | `/health` | GET | ✅ | `{code:0,data:{status:"healthy",database:"connected"}}` |
| 2 | `/api/auth/register` | POST | ✅ | 返回 `{patient_id}`，**不返回 token**（符合设计，注册后需登录） |
| 3 | `/api/auth/login` | POST | ✅ | 返回 `{token, patient_id, name}`，前端据此存 token+patientId |
| 4 | `/api/patient/profile` | GET | ✅ | `mapProfileToForm` 字段齐全；默认 `gender:"男", age:0, allergy_history:[]` |
| 5 | `/api/patient/profile` | PUT | ✅ | 过敏史数组 ↔ 字符串互转持久化正确（`青霉素、海鲜`） |
| 6 | `/api/departments` | GET | ✅ | `flattenDepartments` 正确拍平：3 科室 / 4 医生，字段 `doctor_id/name/specialty` 匹配 |
| 7 | `/api/doctors/{id}/slots` | GET | ✅ | query `?date=` 正确；`available_slots:[]`（后端未配置排班） |
| 8 | `/api/agent/chat` | POST | ✅（兼容） | 非流式兼容接口；新智能挂号页面不再调用 |
| 9 | `/api/agent/chat` (follow-up) | POST | ✅（兼容） | `mode:follow-up` 正常，多轮返回 `status:"asking"` |
| 新增 | `/api/agent/chat/stream` | POST | 待后端发布 | SSE：文本片段 → 单个结构化结果 → `[DONE]`；同一输入仅一次 Agent 推理与会话写入 |
| 10 | `/api/orders` | POST | ✅ | 创建成功返回 `order_id/status:"pending"` |
| 11 | `/api/orders/{id}` | GET | ✅ | `mapOrderDetail` 字段齐全（见下方问题修复） |
| 12 | `/api/patient/diagnosis-history` | GET | ✅ | query `?status=all`；`mapDiagnosisHistory` 正确 |
| 13 | `/api/patient/latest-diagnosis` | GET | ✅ | 无记录时返回 null，前端容错正常（信息页回退默认） |
| 14 | `/api/patient/notifications` | GET | ✅ | 返回数组（当前为空），铃铛红点逻辑可用 |

## 二、发现的问题与修复

### 问题 1：后端 `date` 字段为创建时间戳，且不含预约 time（已修复）
- 现象：`/api/orders/{id}` 与 `/api/patient/diagnosis-history` 的 `date` 均为订单**创建时间戳**（如 `2026-07-12T11:13:00`），而创建时传入的预约日期 `2026-07-13`、时间 `09:00` 未被回显。
- 影响：`mapOrderDetail` / `mapDiagnosisHistory` 原用 `formatDateTime(data.date)` 作为「预约时间」，会错误显示创建时间。
- 修复：
  - `pages/register/direct.vue`：下单成功后把用户选择的 `{date, time, label}` 写入 `uni.storage`（`cm_appt_{orderId}`）。
  - `pages/user/history.vue` 与 `pages/user/history-detail.vue`：读取该缓存覆盖 `appointmentDate`。
  - `api/mappers.js` `mapOrderDetail` 支持 `ctx.apptLabel` 优先。
  - 已用真实响应验证：覆盖后 `appointmentDate=2026-07-13 09:00` ✅。
- 仍需后端侧修复：建议订单/历史接口返回真实预约日期与时间字段，从根本上解决。

### 问题 2：`available_slots` 为空（后端数据缺失，非前端 bug）
- `GET /api/doctors/{id}/slots` 返回 `available_slots:[]`，说明后端未配置医生排班。
- `direct.vue` 为**软校验**：仅当 `available_slots` 非空且所选时段不在其中时才拦截，因此当前可正常下单。建议后端补全排班数据，否则用户看到的「预约时间」与医生实际可约时段无关。

### 问题 3：`agent/chat` 多轮未触达 `diagnosed`（后端对话策略）
- 测试中多轮追问后端仍返回 `status:"asking"`，未进入 `diagnosed`。因此 `mapDiagnosisToResult`（推荐结果卡 / 信息详情页）分支未用真实 `diagnosis` 数据验证，但代码路径与字段（`syndrome/prescription/department/allergy_warnings`）已按规范编写且容错正确。

## 三、结论
既有 14 个接口均已完成真实后端联调。患者端智能挂号已切换为 SSE 主链路，前端不再在流结束后重复调用 chat；待后端按接口规范发布 stream 后，补充 H5 与微信小程序流式联调记录。
