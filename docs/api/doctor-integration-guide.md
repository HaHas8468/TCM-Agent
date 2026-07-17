# 医生端 API 对接整理与前端差异检查

## 依据范围

- API 来源：`api规范/API接口规范.md`
- 前端来源：`src/App.vue`、`src/composables/useDoctorPrototype.js`、`src/data/doctorPrototypeData.js`、`src/modules/doctor/**`
- 结论日期：2026-07-11

## 总体结论

当前前端医生端仍是纯原型状态，没有真实 API service 层，所有登录、队列、工作台、病历、医案、统计、设置、用户管理逻辑都由 `useDoctorPrototype.js` 和 `doctorPrototypeData.js` 在本地模拟。

API 文档已经覆盖了医生登录、医生队列、开始/暂存/完成接诊、四诊补录、病历检索、病历详情、医生资料、Agent 统一入口等医生端主流程。但前端原型包含的部分功能在 API 文档中还没有完整定义，尤其是用户管理、个人医案库、系统统计、工作台设置、通知设置、安全设置、图谱维护统计等。

医生端真正联调前，建议先补一层 `doctorApi` adapter，把 API 的 snake_case、英文枚举、order_id 业务主键转换成前端当前使用的 camelCase、中文状态和患者工作台结构。

## 医生端 API 汇总

| 模块 | 接口 | 方法 | 当前前端入口 | 对接状态 |
| --- | --- | --- | --- | --- |
| 医生登录 | `/api/doctor/auth/login` | POST | `LoginView.vue` / `login()` | 有接口，但前端未接 token |
| 医生资料 | `/api/doctor/profile` | GET | `SettingsCenter` / 侧栏资料 | 有接口，字段不完全匹配 |
| 医生资料更新 | `/api/doctor/profile` | PUT | `ProfileSettingsCard` | 有接口，字段不完全匹配 |
| 接诊队列 | `/api/doctor/queue` | GET | `QueueOverview.vue` | 有接口，但队列字段不足 |
| 开始接诊 | `/api/orders/{order_id}/start` | PUT | `openConsultation()` | 有接口，前端当前用 patientId |
| 四诊补录 | `/api/orders/{order_id}/diagnosis` | POST | `FaceToFaceSupplementPanel.vue` | 有接口，字段需转换 |
| 暂存诊断 | `/api/orders/{order_id}/save` | PUT | `DoctorFinalConfirmPanel.vue` 暂存 | 有接口，字段需转换 |
| 完成接诊 | `/api/orders/{order_id}/finish` | PUT | `DoctorFinalConfirmPanel.vue` 完成接诊 | 有接口，字段需补齐治疗字段 |
| Agent 对话 | `/api/agent/chat` | POST | `WorkspaceConversationPanel.vue` / Agent 查询 | 有接口，前端仍是本地模拟 |
| 病历检索 | `/api/records` | GET | `RecordsManager.vue` | 有接口，字段需转换 |
| 病历详情 | `/api/records/{record_id}` | GET | `RecordsManager.vue` 详情 | 有接口，字段需转换 |
| 患者历史病历 | `/api/patient/{patient_id}/history` | GET | 工作台患者历史信息 | 有接口，但工作台未真实调用 |
| 用户管理 | `/api/admin/users` | GET | `UserManagement.vue` | 仅总览出现，缺 CRUD 详情 |

## 主要不一致与遗漏

### 1. 登录接口返回 token，但前端没有鉴权状态

API 返回：

```json
{
  "token": "eyJ...",
  "doctor_id": "D001",
  "name": "林青和",
  "department": "中医内科",
  "default_landing": "queue"
}
```

前端当前：

- `login(credentials)` 只把 `loggedIn` 设为 `true`。
- 没有保存 `token`、`doctor_id`。
- 没有把 `default_landing` 映射到默认模块。
- 侧栏医生资料来自本地 `doctorProfile`，不是登录返回值或 `/api/doctor/profile`。

建议：

- 新增 `authToken`、`doctorId`、`currentDoctor` 状态。
- 登录成功后保存 token，并作为后续接口的 `Authorization: Bearer <token>`。
- `default_landing` 映射到 `activeModule`。

### 2. 队列接口字段不足以支撑当前前端工作台

API 队列返回：

```json
{
  "order_id": "O20260710001",
  "patient_id": "P001",
  "patient_name": "张三",
  "department": "中医内科",
  "time": "09:00",
  "status": "pending"
}
```

前端队列和工作台当前需要：

```js
{
  id,
  recordId,
  name,
  gender,
  age,
  department,
  visitType,
  schedule,
  status,
  symptomBrief,
  registrationNote,
  basicInfo,
  fourDiagnosis,
  treatmentPlan,
  aiPlan,
  agentMessages
}
```

差异：

- API 使用 `order_id` 作为接诊主键，前端现在主要使用 `patient.id`。
- API 没有返回 `gender`、`age`、`visit_type`、`symptomBrief`、`registrationNote`。
- API 没有返回 `record_id`。
- API `status` 是 `pending / ongoing / finished / cancelled`，前端展示是 `待接诊 / 问诊中 / 已结束`。
- API `kpi` 在响应外层，前端当前用本地 patients 计算 `queueStats`。

建议：

- 前端队列模型新增 `orderId`，所有接诊操作改用 `orderId`。
- 建立状态映射：

| API | 前端展示 |
| --- | --- |
| `pending` | `待接诊` |
| `ongoing` | `问诊中` |
| `finished` | `已结束` |
| `cancelled` | `已取消` |

- 后端可选择在 `/api/doctor/queue` 增加 `patient.gender`、`patient.age`、`record_id`、`visit_type`、`symptoms_summary`。
- 或者前端点击接诊后，再通过工作台详情接口拉取完整患者上下文。

### 3. 缺少“医生工作台详情”聚合接口

当前工作台需要一次性展示：

- 患者基本信息
- 过敏史
- 历史辨证
- 历史处方
- 四诊信息
- Agent 已有结论
- 推荐方剂、药材、医案
- 当前对话消息
- 当前病历/挂号单状态

API 文档中有：

- `/api/orders/{order_id}/start`
- `/api/orders/{order_id}`，说明为历史诊断详情，且“同 7.2 病历详情”
- `/api/patient/{patient_id}/history`
- `/api/records/{record_id}`

但这些接口还不能直接覆盖当前工作台首屏的数据结构。

建议新增或明确：

```text
GET /api/doctor/orders/{order_id}/workspace
```

建议响应：

```json
{
  "order": {
    "order_id": "O20260710001",
    "status": "ongoing",
    "department": "中医内科",
    "time": "09:00"
  },
  "patient": {
    "patient_id": "P001",
    "name": "张三",
    "gender": "女",
    "age": 31,
    "phone": "138****1234",
    "allergy_history": ["麻黄", "桂枝"],
    "history_syndromes": ["肝胃不和"],
    "history_prescriptions": ["半夏泻心汤"]
  },
  "four_diagnosis": {
    "chief_complaint": "头痛3天",
    "present_illness": "受凉后出现头痛",
    "tongue": "舌淡红",
    "pulse": "脉浮紧",
    "symptoms": ["头痛", "恶寒"],
    "signs": "体温37.5℃",
    "other": "无"
  },
  "agent": {
    "session_id": "S_D_O20260710001",
    "messages": [],
    "diagnosis": null
  }
}
```

### 4. Agent 接口已定义，但前端还没有按协议传参

API 要求：

```json
{
  "session_id": "S_D_{order_id}",
  "patient_id": "P001",
  "user_input": "医生输入内容",
  "mode": "normal",
  "scene": "doctor"
}
```

前端当前：

- `sendAgentMessage(text)` 只传文本。
- `buildAgentReply()` 在本地模拟返回。
- 没有 `session_id`。
- 没有 `scene: doctor`。
- 没有处理 `asking / diagnosed / done / error`。
- 没有把 API 的 `diagnosis` 写入工作台系统分析和医生最终确认区。

建议：

- 工作台主对话使用 `session_id = S_D_{order_id}`。
- 辅助知识查询使用 `session_id = S_Q_{order_id}`。
- 医案详情弹窗使用 `S_CASE_{case_id}`。
- 药材详情弹窗使用 `S_HERB_{herb_name}`。
- Agent 返回 `diagnosed` 时，将 `data.diagnosis` 转换为前端 `patient.agentResult.diagnosisResult`。

### 5. 四诊补录字段命名和结构需要 adapter

API `POST /api/orders/{order_id}/diagnosis` 需要：

```json
{
  "chief_complaint": "头痛3天",
  "present_illness": "受凉后出现头痛",
  "tongue": "舌淡红苔薄白",
  "pulse": "脉浮紧",
  "symptoms": ["头痛", "恶寒", "无汗"],
  "signs": "体温37.5℃",
  "other": "无既往史"
}
```

前端当前提交：

```js
{
  fourDiagnosis: {
    tongue,
    pulse,
    signs,
    symptoms,
    other
  },
  treatmentPlan: {},
  completeVisit: false
}
```

差异：

- 前端缺 `chiefComplaint`、`presentIllness` 在面诊补录表单中的显式编辑。
- 前端 `symptoms` 是文本，API 是数组。
- 前端是 camelCase 嵌套结构，API 是 snake_case 平铺结构。

建议：

- 面诊补录表单补充 `chiefComplaint`、`presentIllness`。
- 前端提交前将症状文本按 `、 / ， / 换行` 拆成数组。
- 新增 `mapFourDiagnosisToApi(form)`。

### 6. 暂存/完成接诊缺少治疗字段对齐

API `PUT /api/orders/{order_id}/finish` 需要：

```json
{
  "syndrome": "风寒表实证",
  "prescription": "麻黄汤",
  "ingredients": ["麻黄", "桂枝", "杏仁", "甘草"],
  "advice": "避风寒，清淡饮食"
}
```

前端医生确认区当前有：

```js
{
  syndrome,
  therapy,
  formula,
  herbsText,
  advice
}
```

差异：

- 前端 `therapy` 没有对应 API 字段。
- 前端 `formula` 对应 API `prescription`。
- 前端 `herbsText` 需要拆成 API `ingredients`。
- 病历详情 API 中有 `treatment_principle`，但暂存/完成接口没有该字段。

建议：

- API 暂存/完成增加 `treatment_principle`。
- 前端 adapter：

```js
{
  syndrome: form.syndrome,
  treatment_principle: form.therapy,
  prescription: form.formula,
  ingredients: splitTextList(form.herbsText),
  advice: form.advice
}
```

### 7. 病历管理字段需要转换

API 病历列表返回：

```json
{
  "record_id": "R001",
  "patient": { "patient_id": "P001", "name": "张三" },
  "syndrome": "风寒表实证",
  "prescription": "麻黄汤",
  "date": "2026-07-10T09:30:00"
}
```

前端列表使用：

```js
{
  recordId,
  patientId,
  patientName,
  syndrome,
  formula,
  visitTime
}
```

需要转换：

| API | 前端 |
| --- | --- |
| `record_id` | `recordId` |
| `patient.patient_id` | `patientId` |
| `patient.name` | `patientName` |
| `prescription` | `formula` |
| `date` | `visitTime` |
| `treatment_principle` | `therapy` |

另外，前端详情展示 `chatSummary`，API 病历详情当前没有返回聊天摘要。若病历页需要保留该区块，建议后端增加 `chat_summary` 或前端隐藏该项。

### 8. 医生资料字段不一致

API 医生资料：

```json
{
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
```

前端医生资料：

```js
{
  name,
  title,
  role,
  account,
  organization,
  shift,
  focus,
  dutyStatus
}
```

差异：

- `username` 对应前端 `account`。
- `duty_time` 对应前端 `shift`。
- `specialty` 对应前端 `focus`。
- API 没有 `title`、`organization`、`dutyStatus`。
- 前端没有展示/编辑 `phone`、`bio`。

建议：

- API 增加 `title`、`organization`、`duty_status`。
- 前端设置页补充 `phone`、`bio`，或确认这两个字段不在医生端展示。

### 9. 用户管理前端有完整 CRUD，但 API 只出现列表入口

前端用户管理支持：

- 创建用户
- 编辑用户等级
- 启用/禁用
- 删除用户

API 文档仅在接口总览出现：

```text
GET /api/admin/users
```

缺少：

```text
POST /api/admin/users
PUT /api/admin/users/{user_id}
PUT /api/admin/users/{user_id}/status
DELETE /api/admin/users/{user_id}
```

建议补充请求/响应字段：

```json
{
  "name": "周明",
  "username": "doctor.zhou",
  "role": "doctor",
  "disabled": false
}
```

### 10. 前端有医案库和统计后台，但 API 文档没有对应业务接口

前端存在：

- `CaseLibrary.vue`
- `AnalyticsDashboard.vue`

API 文档中：

- 医案详情/药材详情建议统一走 `/api/agent/chat`。
- 没有医案列表、上传、自建医案管理、医案对比接口。
- 没有系统统计、证型频次、方剂频次、图谱维护事项接口。

建议补充：

```text
GET /api/doctor/cases
POST /api/doctor/cases
GET /api/doctor/cases/compare?case_ids=C001,C002
GET /api/doctor/analytics/summary
GET /api/doctor/analytics/syndromes
GET /api/doctor/analytics/formulas
GET /api/doctor/graph/tasks
```

也可以先简化为：

```text
GET /api/doctor/dashboard
```

一次返回统计 KPI、证型频次、方剂频次、图谱维护事项。

### 11. 前端设置中心比 API 多

前端设置中心包含：

- 个人资料
- 消息通知
- 工作台偏好
- 账号安全

API 文档只有：

- `GET /api/doctor/profile`
- `PUT /api/doctor/profile`

缺少：

```text
GET /api/doctor/settings
PUT /api/doctor/settings/notifications
PUT /api/doctor/settings/workspace
PUT /api/doctor/settings/security
```

如果后端短期不做这些设置，前端需要标注为本地设置，避免联调时误以为都能持久化。

## 建议的前端 API 目录

建议新增：

```text
src/api/http.js
src/api/doctorApi.js
src/api/adapters/doctorQueueAdapter.js
src/api/adapters/doctorWorkspaceAdapter.js
src/api/adapters/doctorRecordAdapter.js
src/api/adapters/doctorProfileAdapter.js
```

### doctorApi 建议方法

```js
export const doctorApi = {
  login,
  getProfile,
  updateProfile,
  getQueue,
  startOrder,
  getWorkspace,
  sendAgentMessage,
  submitDiagnosis,
  saveOrder,
  finishOrder,
  searchRecords,
  getRecordDetail,
  getPatientHistory,
  getUsers,
  createUser,
  updateUser,
  toggleUser,
  deleteUser
}
```

## 优先级建议

| 优先级 | 事项 | 原因 |
| --- | --- | --- |
| P0 | 接入登录 token 与 Authorization | 所有医生接口依赖鉴权 |
| P0 | 队列字段 adapter 与 `orderId` 改造 | 接诊主链路依赖 `order_id` |
| P0 | 新增或明确工作台详情接口 | 当前工作台首屏数据无法由单个现有接口支撑 |
| P0 | Agent `/api/agent/chat` 对接 | 智能助手是核心功能，现在仍是本地模拟 |
| P1 | 四诊补录、暂存、完成接诊字段映射 | 影响病历写入和闭环 |
| P1 | 病历列表/详情 adapter | 影响病历管理页真实数据 |
| P1 | 医生 profile 字段补齐 | 影响侧栏和设置中心 |
| P2 | 用户管理 CRUD API | 当前前端有页面，接口不完整 |
| P2 | 医案库、统计后台、设置中心扩展 API | 当前前端功能超出接口文档 |

## 最小联调版本建议

若希望先跑通医生端主链路，最小可先实现：

1. `POST /api/doctor/auth/login`
2. `GET /api/doctor/profile`
3. `GET /api/doctor/queue`
4. `PUT /api/orders/{order_id}/start`
5. `GET /api/doctor/orders/{order_id}/workspace`
6. `POST /api/agent/chat`
7. `POST /api/orders/{order_id}/diagnosis`
8. `PUT /api/orders/{order_id}/save`
9. `PUT /api/orders/{order_id}/finish`
10. `GET /api/records`
11. `GET /api/records/{record_id}`

这 11 个接口可以覆盖登录、接诊队列、进入工作台、智能助手、补录、暂存、完成接诊和病历查看。其他医案库、统计、用户管理、通知/安全设置可以作为第二阶段。
