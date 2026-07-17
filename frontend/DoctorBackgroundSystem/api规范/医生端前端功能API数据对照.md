# 医生端前端功能 API 与数据对照

## 文档目的

这份文档按当前前端医生端功能归纳 API 和数据结构，方便逐页判断前后端是否一致。

依据：

- API 文档：`api规范/API接口规范.md`
- 前端入口：`src/App.vue`
- 状态原型：`src/composables/useDoctorPrototype.js`
- 原型数据：`src/data/doctorPrototypeData.js`
- 页面模块：`src/modules/doctor/**`

说明：

- 当前前端没有真实接口请求层，所有数据都来自本地原型数据。
- API 文档使用 snake_case 和英文状态枚举。
- 前端原型大量使用 camelCase、中文展示状态和本地聚合对象。
- 本文只按当前实际渲染页面整理；`src/modules/doctor/settings/components` 下未被 `SettingsCenter.vue` 引用的旧设置组件不计入当前前端功能。

## 当前医生端前端功能总览

| 前端模块 | 组件 | 当前是否展示 | API 覆盖情况 |
| --- | --- | --- | --- |
| 登录页 | `LoginView.vue` | 是 | 有医生登录 API |
| 左侧医生信息/导航 | `SidebarNav.vue` | 是 | 部分依赖医生资料 API |
| 接诊队列 | `QueueOverview.vue` | 是 | 有队列 API，但字段不完整 |
| 问诊工作台 | `ConsultationWorkspace.vue` | 是 | 有零散 API，缺工作台聚合详情 |
| 智能助手对话 | `WorkspaceConversationPanel.vue` | 是 | 有 Agent 统一入口，前端未接 |
| 患者基本信息 | `WorkspacePatientInfoCard.vue` | 是 | 需要工作台详情或患者历史接口支撑 |
| 面诊补录 | `FaceToFaceSupplementPanel.vue` | 是 | 有四诊补录 API，字段需适配 |
| 系统分析 | `SystemAnalysisPanel.vue` | 是 | 来自 Agent diagnosis，需适配 |
| 医生最终确认 | `DoctorFinalConfirmPanel.vue` | 是 | 有暂存/完成 API，字段需适配 |
| 病历管理 | `RecordsManager.vue` | 是 | 有病历列表和详情 API |
| 个人医案库 | `CaseLibrary.vue` | 是 | API 文档未定义医案库 CRUD |
| 系统统计 | `AnalyticsDashboard.vue` | 是 | API 文档未定义医生统计接口 |
| 用户设置 | `SettingsCenter.vue` | 是 | 可用医生资料 API，但字段不完全一致 |
| 账号安全 | `SettingsCenter.vue` | 是 | API 文档未定义改密/绑定联系方式接口 |
| 用户管理 | `UserManagement.vue` | 是 | 总览提到 `/api/admin/users`，缺 CRUD 详情 |

## 1. 登录页

### 前端功能

组件：`src/modules/doctor/auth/LoginView.vue`

当前表单字段：

```js
{
  account: 'doctor.lin',
  password: 'Prototype123',
  remember: true
}
```

当前前端行为：

- 点击登录后触发 `login(credentials)`。
- 本地设置 `state.loggedIn = true`。
- 未保存 token。
- 未保存 doctor_id。
- 未调用真实接口。

### 对应 API

```text
POST /api/doctor/auth/login
```

API 请求：

```json
{
  "username": "doctor.lin",
  "password": "Prototype123"
}
```

API 响应：

```json
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
```

### 需要对齐

| 前端 | API | 处理建议 |
| --- | --- | --- |
| `account` | `username` | 提交前重命名 |
| `password` | `password` | 直接传 |
| `remember` | 无 | 前端本地保存偏好 |
| 无 | `token` | 登录成功后保存 |
| 无 | `doctor_id` | 登录成功后保存 |
| 无 | `default_landing` | 映射到 `activeModule` |

## 2. 左侧医生信息与导航

### 前端功能

组件：`src/components/layout/SidebarNav.vue`

当前医生资料字段：

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

导航字段：

```js
[
  { key: 'queue', label: '接诊队列' },
  { key: 'workspace', label: '问诊工作台' },
  { key: 'records', label: '病历管理' },
  { key: 'cases', label: '个人医案库' },
  { key: 'analytics', label: '系统统计' },
  { key: 'settings', label: '用户设置' },
  { key: 'users', label: '用户管理' }
]
```

### 对应 API

```text
GET /api/doctor/profile
PUT /api/doctor/profile
```

API 字段：

```js
{
  doctor_id,
  name,
  role,
  username,
  phone,
  department,
  duty_time,
  specialty,
  bio
}
```

### 需要对齐

| 前端 | API | 处理建议 |
| --- | --- | --- |
| `account` | `username` | adapter 转换 |
| `shift` | `duty_time` | adapter 转换 |
| `focus` | `specialty` | adapter 转换 |
| `department` | `department` | 直接使用 |
| `title` | 无 | 后端补充或前端移除 |
| `organization` | 无 | 后端补充或前端写死/移除 |
| `dutyStatus` | 无 | 若要持久化，需要新增字段或接口 |
| `phone` | 前端未展示在侧栏 | 设置页可使用 |
| `bio` | 前端未展示 | 可暂不接 |

## 3. 接诊队列

### 前端功能

组件：`src/modules/doctor/queue/QueueOverview.vue`

前端患者队列对象：

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

前端队列统计：

```js
[
  { label: '今日挂号', value, meta },
  { label: '待接诊', value, meta },
  { label: '问诊中', value, meta },
  { label: '已归档', value, meta }
]
```

### 对应 API

```text
GET /api/doctor/queue?date=2026-07-10&department=中医内科&period=all
```

API 响应：

```js
{
  data: [
    {
      order_id,
      patient_id,
      patient_name,
      department,
      time,
      status
    }
  ],
  kpi: {
    today_total,
    pending,
    ongoing,
    finished
  }
}
```

### 字段映射建议

| API | 前端 | 说明 |
| --- | --- | --- |
| `order_id` | `orderId` | 前端需新增，接诊主键 |
| `patient_id` | `id` 或 `patientId` | 建议保留 `patientId`，不要混用 |
| `patient_name` | `name` | 展示姓名 |
| `department` | `department` | 直接使用 |
| `time` | `schedule` | 展示挂号时间 |
| `status` | `status` | 需要枚举转换 |
| `kpi.today_total` | 今日挂号统计 | 直接映射 |
| `kpi.pending` | 待接诊统计 | 直接映射 |
| `kpi.ongoing` | 问诊中统计 | 直接映射 |
| `kpi.finished` | 已归档统计 | 直接映射 |

状态映射：

| API | 前端展示 |
| --- | --- |
| `pending` | `待接诊` |
| `ongoing` | `问诊中` |
| `finished` | `已结束` 或 `已归档` |
| `cancelled` | `已取消` |

### 当前缺口

队列 API 不返回前端当前表格之外的工作台详情字段。若点击接诊后直接进入工作台，需要额外接口拉取完整上下文。

建议：

- 队列表只保留轻量字段。
- 进入工作台后调用 `GET /api/doctor/orders/{order_id}/workspace`。

## 4. 问诊工作台

### 前端功能

组件：`src/modules/doctor/workspace/ConsultationWorkspace.vue`

工作台由以下区域组成：

- 智能助手对话
- 患者基本信息
- 面诊补录
- 系统分析
- 医生最终确认
- 推荐详情弹窗

### 当前前端需要的数据

```js
{
  orderId,
  patientId,
  recordId,
  patient: {
    name,
    gender,
    age,
    department,
    schedule,
    status,
    basicInfo: {
      phone,
      patientId,
      bloodPressure,
      allergies,
      historySyndromes,
      historyPrescriptions
    }
  },
  fourDiagnosis: {
    chiefComplaint,
    presentIllness,
    tongue,
    pulse,
    symptoms,
    signs,
    other
  },
  treatmentPlan: {
    formula,
    usage,
    followUp
  },
  aiPlan: {
    gaps,
    syndrome,
    therapy,
    formula,
    evidence,
    recommendations: {
      herbs,
      cases
    }
  },
  agentMessages
}
```

### 现有 API

```text
PUT /api/orders/{order_id}/start
POST /api/orders/{order_id}/diagnosis
PUT /api/orders/{order_id}/save
PUT /api/orders/{order_id}/finish
POST /api/agent/chat
GET /api/patient/{patient_id}/history
GET /api/records/{record_id}
```

### 当前缺口

现有 API 是分散的，不足以直接支撑工作台首屏。建议新增聚合接口：

```text
GET /api/doctor/orders/{order_id}/workspace
```

建议包含：

```js
{
  order,
  patient,
  patient_history,
  four_diagnosis,
  agent_session,
  agent_messages,
  diagnosis_result,
  recommendations,
  record
}
```

## 5. 智能助手对话

### 前端功能

组件：`WorkspaceConversationPanel.vue`

当前前端消息结构：

```js
{
  id,
  sender,
  roleLabel,
  time,
  text
}
```

当前行为：

- 医生输入文本。
- 前端本地生成智能助手回复。
- 没有调用 API。

### 对应 API

```text
POST /api/agent/chat
```

请求：

```js
{
  session_id,
  patient_id,
  user_input,
  mode,
  scene
}
```

响应状态：

| API `data.status` | 前端处理 |
| --- | --- |
| `asking` | 追加追问气泡 |
| `diagnosed` | 追加回复，并写入系统分析 |
| `done` | 追加普通文本回复 |
| `error` | 展示错误回复 |

### 需要对齐

| 前端 | API |
| --- | --- |
| `text` | `user_input` |
| 无 | `session_id = S_D_{order_id}` |
| 无 | `scene = doctor` |
| 无 | `mode = normal / follow-up` |
| `agentMessages[]` | 由 API response 追加 |
| `agentResult.diagnosisResult` | 由 API `data.diagnosis` 转换 |

## 6. 患者基本信息

### 前端功能

组件：`WorkspacePatientInfoCard.vue`

前端表单字段：

```js
{
  name,
  gender,
  age,
  department,
  schedule,
  status,
  allergiesText,
  historySyndromesText,
  historyPrescriptionsText
}
```

### 对应 API

当前 API 文档没有专门的医生端患者基本信息更新接口。

可复用或补充：

```text
GET /api/doctor/orders/{order_id}/workspace
PUT /api/doctor/orders/{order_id}/patient
GET /api/patient/{patient_id}/history
```

### 当前缺口

- 前端可以修改患者姓名、性别、年龄、科室、挂号时间、状态、过敏史、历史辨证、历史处方。
- API 只定义了患者端 `/api/patient/profile`，不适合医生端直接更新他人档案。
- 需要明确医生端是否允许修改患者基本资料。

建议：

- 如果允许医生编辑，新增医生端接口。
- 如果不允许，前端患者基本信息区改成只读或只允许补充本次病历信息。

## 7. 面诊补录

### 前端功能

组件：`FaceToFaceSupplementPanel.vue`

当前字段：

```js
{
  tongue,
  pulse,
  signs,
  symptoms,
  other
}
```

### 对应 API

```text
POST /api/orders/{order_id}/diagnosis
```

API 请求字段：

```js
{
  chief_complaint,
  present_illness,
  tongue,
  pulse,
  symptoms,
  signs,
  other
}
```

### 需要对齐

| 前端 | API | 说明 |
| --- | --- | --- |
| `tongue` | `tongue` | 直接传 |
| `pulse` | `pulse` | 直接传 |
| `signs` | `signs` | 直接传 |
| `symptoms` 文本 | `symptoms` 数组 | 需要拆分 |
| `other` | `other` | 直接传 |
| 前端缺少 | `chief_complaint` | 建议补表单字段 |
| 前端缺少 | `present_illness` | 建议补表单字段 |

## 8. 系统分析

### 前端功能

组件：`SystemAnalysisPanel.vue`

当前展示：

```js
{
  syndromeName,
  syndromeDescription,
  therapy,
  formula,
  herbs,
  attention
}
```

来源优先级：

- `patient.agentResult.diagnosisResult`
- `patient.aiPlan`
- `patient.treatmentPlan`

### 对应 API

主要来自：

```text
POST /api/agent/chat
```

当 `data.status = diagnosed` 时返回：

```js
{
  diagnosis: {
    syndrome,
    prescription,
    ingredients,
    department,
    allergy_warnings
  }
}
```

### 需要对齐

| API | 前端 |
| --- | --- |
| `diagnosis.syndrome` | `syndromeName` |
| `diagnosis.prescription` | `formula` |
| `diagnosis.ingredients` | `herbs` |
| `diagnosis.allergy_warnings` | `attention` |
| API 缺少 | `therapy` |
| API 缺少 | `syndromeDescription` |

建议：

- Agent diagnosis 增加 `treatment` 或 `treatment_principle`。
- Agent diagnosis 增加 `syndrome_description`，否则系统分析描述只能本地拼接。

## 9. 医生最终确认

### 前端功能

组件：`DoctorFinalConfirmPanel.vue`

当前字段：

```js
{
  syndrome,
  therapy,
  formula,
  herbsText,
  advice
}
```

### 对应 API

```text
PUT /api/orders/{order_id}/save
PUT /api/orders/{order_id}/finish
```

API 字段：

```js
{
  syndrome,
  prescription,
  ingredients,
  advice
}
```

### 需要对齐

| 前端 | API |
| --- | --- |
| `syndrome` | `syndrome` |
| `therapy` | 建议 API 增加 `treatment_principle` |
| `formula` | `prescription` |
| `herbsText` | `ingredients` |
| `advice` | `advice` |

## 10. 病历管理

### 前端功能

组件：`RecordsManager.vue`

筛选字段：

```js
{
  patientName,
  patientId,
  syndrome,
  date
}
```

列表字段：

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

详情字段：

```js
{
  fourDiagnosis,
  syndrome,
  therapy,
  formula,
  chatSummary
}
```

### 对应 API

```text
GET /api/records?name=&patient_id=&syndrome=&date_from=&date_to=&page=&page_size=
GET /api/records/{record_id}
```

### 字段映射

| API | 前端 |
| --- | --- |
| `record_id` | `recordId` |
| `patient.patient_id` | `patientId` |
| `patient.name` | `patientName` |
| `prescription` | `formula` |
| `date` | `visitTime` |
| `treatment_principle` | `therapy` |
| `chief_complaint` | `fourDiagnosis.chiefComplaint` |
| `present_illness` | `fourDiagnosis.presentIllness` |

缺口：

- 前端有 `chatSummary`，API 详情没有。
- 前端只有单个 `date` 筛选，API 是 `date_from / date_to`。

## 11. 个人医案库

### 前端功能

组件：`CaseLibrary.vue`

当前功能：

- 自建医案上传入口
- 医案列表
- 选择两个医案对比
- 展示用药差异、辨证差异、智能匹配结果

当前数据字段：

```js
{
  id,
  title,
  syndrome,
  formula,
  treatment,
  highlights,
  matches,
  herbDifference,
  syndromeDifference
}
```

### 对应 API

API 文档没有独立医案库接口。文档只说明医案详情/推荐类需求统一走：

```text
POST /api/agent/chat
```

### 当前缺口

需要判断个人医案库是否要落库。

若要落库，建议新增：

```text
GET /api/doctor/cases
POST /api/doctor/cases
PUT /api/doctor/cases/{case_id}
DELETE /api/doctor/cases/{case_id}
POST /api/doctor/cases/compare
```

若只是 Agent 查询入口，前端当前“上传入口”和“医案列表管理”需要降级或改文案。

## 12. 系统统计

### 前端功能

组件：`AnalyticsDashboard.vue`

当前数据：

```js
{
  kpis,
  syndromeFrequency,
  formulaFrequency,
  graphMaintenance
}
```

### 对应 API

API 文档没有医生端统计接口。

建议新增：

```text
GET /api/doctor/analytics
```

建议返回：

```js
{
  kpis,
  syndrome_frequency,
  formula_frequency,
  graph_maintenance
}
```

## 13. 设置中心

### 当前实际前端功能

组件：`SettingsCenter.vue`

当前可见入口：

- 用户设置
- 账号安全
- 退出登录

当前“用户设置”字段：

```js
{
  name,
  department,
  shift
}
```

当前“账号安全”字段：

```js
{
  oldPassword,
  newPassword,
  confirmPassword,
  email,
  phone
}
```

注意：

- 当前实际页面没有消息通知设置。
- 当前实际页面没有工作台偏好设置。
- `settings/components` 目录里存在旧组件，但当前 `SettingsCenter.vue` 没有引用。

### 对应 API

已定义：

```text
GET /api/doctor/profile
PUT /api/doctor/profile
```

未定义：

```text
PUT /api/doctor/security/password
PUT /api/doctor/security/contact
```

### 字段对齐

用户设置：

| 前端 | API |
| --- | --- |
| `name` | `name` |
| `department` | `department` |
| `shift` | `duty_time` |

账号安全：

| 前端 | API |
| --- | --- |
| `email` | API 当前无字段 |
| `phone` | `phone` |
| `oldPassword` | API 当前无字段 |
| `newPassword` | API 当前无字段 |
| `confirmPassword` | 前端校验字段，不传后端 |

建议：

- `email` 如果要保留，医生资料 API 增加 `email`。
- 修改密码建议独立接口，不要混在 profile 更新里。

## 14. 用户管理

### 前端功能

组件：`UserManagement.vue`

当前功能：

- 创建用户
- 列出所有用户
- 编辑用户等级
- 启用/禁用
- 删除用户

当前字段：

```js
{
  id,
  name,
  account,
  level,
  disabled
}
```

前端等级：

```js
['普通用户', '医生', '管理员']
```

### 对应 API

API 总览只出现：

```text
GET /api/admin/users
```

### 当前缺口

缺少接口详情：

```text
GET /api/admin/users
POST /api/admin/users
PUT /api/admin/users/{user_id}
PUT /api/admin/users/{user_id}/status
DELETE /api/admin/users/{user_id}
```

字段建议：

| 前端 | API 建议 |
| --- | --- |
| `id` | `user_id` |
| `name` | `name` |
| `account` | `username` |
| `level` | `role` |
| `disabled` | `disabled` |

角色映射：

| 前端 | API 建议 |
| --- | --- |
| `普通用户` | `patient` 或 `user` |
| `医生` | `doctor` |
| `管理员` | `admin` |

## 15. 推荐的前端数据 adapter

建议新增：

```text
src/api/doctorApi.js
src/api/adapters/doctorAuthAdapter.js
src/api/adapters/doctorProfileAdapter.js
src/api/adapters/doctorQueueAdapter.js
src/api/adapters/doctorWorkspaceAdapter.js
src/api/adapters/doctorRecordAdapter.js
src/api/adapters/doctorUserAdapter.js
```

核心转换职责：

| adapter | 职责 |
| --- | --- |
| `doctorAuthAdapter` | 登录请求/响应，保存 token、doctor_id |
| `doctorProfileAdapter` | `username/duty_time/specialty` 和 `account/shift/focus` 转换 |
| `doctorQueueAdapter` | 队列列表、KPI、状态枚举转换 |
| `doctorWorkspaceAdapter` | 工作台聚合对象、四诊、Agent diagnosis、暂存/完成 payload |
| `doctorRecordAdapter` | 病历列表/详情字段转换 |
| `doctorUserAdapter` | 用户管理角色、禁用状态转换 |

## 16. 按前端功能判断的一致性清单

| 前端功能 | API 是否足够 | 结论 |
| --- | --- | --- |
| 登录 | 基本足够 | 需要前端保存 token |
| 左侧医生信息 | 部分足够 | profile 字段需补 `title/organization/duty_status` 或前端调整 |
| 接诊队列 | 部分足够 | 缺工作台所需患者详情 |
| 开始接诊 | 基本足够 | 前端需改用 `order_id` |
| 工作台详情 | 不足 | 建议新增聚合接口 |
| 智能助手 | 基本足够 | 前端需接 `/api/agent/chat` 并处理状态 |
| 面诊补录 | 部分足够 | 前端需补主诉/现病史或 API 允许为空 |
| 系统分析 | 部分足够 | Agent 返回缺 `therapy/description` |
| 暂存/完成 | 部分足够 | API 建议增加 `treatment_principle` |
| 病历管理 | 基本足够 | 需要字段 adapter，缺聊天摘要 |
| 个人医案库 | 不足 | 缺医案 CRUD/对比接口 |
| 系统统计 | 不足 | 缺统计接口 |
| 用户设置 | 部分足够 | `shift` 可映射 `duty_time` |
| 账号安全 | 不足 | 缺改密和联系方式接口 |
| 用户管理 | 不足 | 缺 CRUD 详情 |

## 17. 最小可联调 API 清单

第一阶段只跑通医生主流程，建议先确认这些接口：

| 顺序 | 接口 | 用途 |
| --- | --- | --- |
| 1 | `POST /api/doctor/auth/login` | 医生登录 |
| 2 | `GET /api/doctor/profile` | 侧栏与设置资料 |
| 3 | `GET /api/doctor/queue` | 接诊队列和 KPI |
| 4 | `PUT /api/orders/{order_id}/start` | 开始接诊 |
| 5 | `GET /api/doctor/orders/{order_id}/workspace` | 工作台详情，建议新增 |
| 6 | `POST /api/agent/chat` | 智能助手 |
| 7 | `POST /api/orders/{order_id}/diagnosis` | 面诊补录 |
| 8 | `PUT /api/orders/{order_id}/save` | 暂存 |
| 9 | `PUT /api/orders/{order_id}/finish` | 完成接诊 |
| 10 | `GET /api/records` | 病历检索 |
| 11 | `GET /api/records/{record_id}` | 病历详情 |
| 12 | `PUT /api/doctor/profile` | 用户设置保存 |
| 13 | `PUT /api/doctor/security/password` | 账号安全改密，建议新增 |

第二阶段再补：

- 用户管理 CRUD
- 个人医案库
- 系统统计
- 医案对比
- 图谱维护事项
