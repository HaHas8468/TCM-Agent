# API 规范符合性检查报告

检查时间：2026-07-16

检查范围：
- 规范文档：`API接口规范.md`
- 前端实现：`api/index.js`、`api/mappers.js`、`api/sse-parser.js`
- 页面使用层：`pages/register/smart.vue`、`pages/register/direct.vue`、`pages/user/profile.vue`、`pages/user/history.vue`、`pages/user/history-detail.vue`、`pages/info/index.vue`、`pages/info/result.vue`、`pages/main/main.vue`

## 结论

当前仓库是患者端前端，已经覆盖了规范中的患者主链路接口，但还没有覆盖医生端、管理端、知识图谱端的大部分接口。

从对齐结果看：
- 规范附录 C 共列出 `25` 个接口，见 `API接口规范.md:568-596`
- 当前前端已封装 `12` 个规范内接口
- 当前前端额外调用了 `1` 个规范中未定义的接口：`/api/patient/notifications`
- 核心患者流程基本可用，但存在：
  - `2` 个实现与规范直接不一致的问题
  - `4` 个前端展示与接口数据未完全对齐的问题
  - `4` 个规范文档自身的冲突/缺口

## 1. 已封装接口检查

| 接口 | 前端状态 | 结论 | 说明 |
|---|---|---|---|
| `POST /api/auth/register` | 已封装 | 符合 | `api/index.js:17-29` |
| `POST /api/auth/login` | 已封装 | 符合 | `api/index.js:32-40` |
| `GET /api/patient/profile` | 已封装 | 基本符合 | 请求与字段映射符合规范，失败时页面会回退本地缓存，见 `api/index.js:46-51`、`api/mappers.js:16-27`、`pages/user/profile.vue:137-152` |
| `PUT /api/patient/profile` | 已封装 | 符合 | `api/index.js:55-61`、`api/mappers.js:30-38` |
| `POST /api/agent/chat` | 已封装 | 基本符合 | 请求体字段符合规范；当前患者端页面未实际使用该入口 |
| `POST /api/agent/chat/stream` | 已封装 | 部分符合 | 流式入口已实现，但 SSE 控制帧解析与 `finish` 处理不完整，见下文问题 2.1 / 2.2 |
| `GET /api/departments` | 已封装 | 符合 | `api/index.js:202-207`、`api/mappers.js:41-57` |
| `GET /api/doctors/{doctor_id}/slots` | 已封装 | 符合 | `api/index.js:211-218` |
| `POST /api/orders` | 已封装 | 符合 | `api/index.js:221-241` |
| `GET /api/patient/diagnosis-history` | 已封装 | 基本符合 | 接口调用与列表映射存在，状态展示未完全覆盖规范枚举，见下文问题 3.2 |
| `GET /api/orders/{order_id}` | 已封装 | 基本符合 | 数据映射存在，但详情页未完整展示规范里的诊断字段，见下文问题 3.3 |
| `GET /api/patient/latest-diagnosis` | 已封装 | 基本符合 | 接口与映射存在，但结果详情页未完整展示同步结果，见下文问题 3.1 |
| `GET /api/patient/notifications` | 已封装 | 规范缺失 | 前端在用，但规范正文和总览未收录，见 `api/index.js:279-285` |

## 2. 实现与规范直接不一致

### 2.1 SSE 解析器会把 `[METADATA]` 当成普通文本渲染

严重程度：高

规范在 `API接口规范.md:166-180` 明确给出了 SSE 帧格式：

```text
data: 根据您目前描述的
...
data: [METADATA]
data: {"finish": false, "status": "asking"}
data: [DONE]
```

当前解析器逻辑见 `api/sse-parser.js:16-34`：
- 只把 `"[DONE]"` 识别为控制帧
- 只把以 `{` 开头的 `data:` 行识别为结构化 JSON
- 其余内容全部走 `handlers.onText`

这意味着规范里的 `data: [METADATA]` 会被当成普通文本追加到聊天气泡中，用户有机会直接看到 `[METADATA]`。

建议：
- 在 `api/sse-parser.js` 中显式忽略 `[METADATA]`
- 同步补一个测试用例，覆盖规范中的完整帧序列

### 2.2 流式接口的 `finish` 语义没有被前端消费

严重程度：中

规范说明见：
- `API接口规范.md:178-180`
- `API接口规范.md:754-760`

规范要求：
- `finish=true` 且 `status=diagnosed` 时，前端应把问诊视为结束，并显示结束弹窗

当前患者端流式页面 `pages/register/smart.vue:282-330` 只处理了：
- `onText`
- `status === "diagnosed"` 时生成结果卡片
- `status === "error"` 时提示错误
- `onDone` 时结束发送态

但没有消费 `finish` 字段，也没有结束弹窗或等价的结束状态 UI。

影响：
- 当前实现更像“收到诊断结果后显示卡片”，而不是“严格按规范消费流状态”
- 如果后端后续依赖 `finish` 控制更多结束行为，前端会漏掉

建议：
- 在 `onPayload` 中显式读取 `data.finish`
- 将 `diagnosed + finish=true` 作为会话结束条件处理

## 3. 前端展示与接口数据未完全对齐

### 3.1 诊断结果详情页丢失了接口中的关键信息

严重程度：中

`mapLatestDiagnosis` 与 `mapDiagnosisToResult` 已经保存了这些字段，见 `api/mappers.js:138-170`：
- `title`，包含辨证结果
- `summary`
- `signals`，包含 `syndrome` / `prescription`
- `advice`

但 `pages/info/result.vue:11-45` 实际只展示了：
- 固定标题 `"初步辨证完成"`
- `department`
- `updatedAt`
- `reason`
- `notices`

没有展示：
- 辨证标题
- 推荐方剂/摘要
- 诊断信号
- 调理建议

影响：
- 接口已经返回并映射到前端状态的数据，没有在详情页完整呈现
- 结果详情页的信息密度反而低于列表/首页卡片

建议：
- 结果详情页至少展示 `result.title`、`result.summary`、`result.signals`、`result.advice`

### 3.2 历史诊断页没有完整覆盖规范中的状态枚举

严重程度：中

规范枚举见 `API接口规范.md:562-565`，订单状态包含：
- `pending`
- `ongoing`
- `finished`
- `cancelled`

当前历史页实现：
- 统计只计算 `finished` 与 `pending`，见 `pages/user/history.vue:74-80`
- 徽标样式只区分 `finished` 与“非 finished”，见 `pages/user/history.vue:41-48`

当前映射层虽然对 `ongoing` 做了文案映射，但 `cancelled` 只能回落显示原始字符串，见 `api/mappers.js:61-85`。

影响：
- 如果后端返回 `ongoing` 或 `cancelled`，历史页统计和状态视觉都不准确
- `cancelled` 不会有本地化文案

建议：
- 在 `mapDiagnosisHistory` 中补齐 `cancelled`
- 历史页统计与 badge 样式至少补齐 `ongoing` / `cancelled`

### 3.3 历史详情页没有把规范中的完整病历字段展示出来

严重程度：中

规范 `GET /api/records/{record_id}` / `GET /api/orders/{order_id}` 的详情字段见 `API接口规范.md:345-364`，包括：
- `chief_complaint`
- `present_illness`
- `tongue`
- `pulse`
- `syndrome`
- `treatment_principle`
- `prescription`
- `ingredients`
- `advice`

当前映射 `api/mappers.js:120-134` 已经保留了：
- `syndrome`
- `prescription`
- `ingredients`
- `tongue`
- `pulse`

但详情页 `pages/user/history-detail.vue:29-77` 实际只展示了：
- 医生/科室/预约时间
- 症状概要
- 诊断说明
- 调理建议
- 注意事项

未展示：
- 舌象
- 脉象
- 方剂
- 药材组成
- 独立辨证结果

影响：
- 前端状态里有数据，但详情页没有完整呈现
- 对“病历详情”来说，当前页面更像摘要页

建议：
- 如果页面定位是“病历详情”，应补齐 `syndrome / prescription / ingredients / tongue / pulse`
- 如果页面只做摘要展示，建议把接口映射和页面命名区分清楚，避免误解

### 3.4 个人资料页会在接口失败时展示本地缓存，导致页面数据可能与服务端不一致

严重程度：低

`pages/user/profile.vue:137-152` 中：
- `getProfile()` 成功时使用后端数据
- 失败时静默回退到 `getCurrentUserProfile()` 本地缓存

影响：
- 页面可能展示旧数据，但用户不会知道当前服务端请求已经失败
- 用户容易误判“页面打开正常，说明服务端数据也正常”

建议：
- 保留本地兜底可以，但应增加“当前显示为本地缓存”的提示
- 或者区分“服务端加载失败”和“本地默认值”

## 4. 规范文档自身的冲突与缺口

### 4.1 Stream 章节前后自相矛盾

严重程度：中

`API接口规范.md:166-180` 明确保留了 `POST /api/agent/chat/stream`，但同一节 `API接口规范.md:182` 又写了：

> 3.2 已删除：所有 Agent 调用统一走 /api/agent/chat，详见附录 F

这会导致实现方无法判断：
- 是否仍需实现 `/api/agent/chat/stream`
- 患者端主链路到底应该走 SSE 还是统一走 `/api/agent/chat`

### 4.2 规范引用了“附录 F”，但文档实际只到“附录 E”

严重程度：中

引用位置：
- `API接口规范.md:182`
- `API接口规范.md:383`

实际文档最后一节是 `附录 E：Agent 统一入口使用约定`，见 `API接口规范.md:694`。

这说明规范中的交叉引用没有同步更新。

### 4.3 `/api/admin/users` 出现在总览里，但正文没有定义

严重程度：低

`API接口规范.md:594` 在总览中列出了：
- `GET /api/admin/users`

但正文没有对应章节、请求参数、响应结构、鉴权说明。

### 4.4 消息通知接口未写入规范

严重程度：中

当前前端使用了 `GET /api/patient/notifications`，见 `api/index.js:279-285`、`pages/main/main.vue`。

但 `API接口规范.md`：
- 正文没有“消息通知”章节
- 附录 C 也没有该接口

这意味着当前联调需要依赖代码或测试报告，而不是依赖规范本身。

## 5. 当前未覆盖的规范接口

以下接口未在当前患者端前端中封装；其中大部分属于医生端、管理端或知识图谱侧，当前仓库没有对应页面，属于范围外而不是直接缺陷。

| 接口 | 当前状态 | 备注 |
|---|---|---|
| `POST /api/doctor/auth/login` | 未封装 | 医生端范围 |
| `GET /api/doctor/queue` | 未封装 | 医生端范围 |
| `PUT /api/orders/{id}/start` | 未封装 | 医生端范围 |
| `PUT /api/orders/{id}/finish` | 未封装 | 医生端范围 |
| `PUT /api/orders/{id}/save` | 未封装 | 医生端范围 |
| `POST /api/orders/{id}/diagnosis` | 未封装 | 医生端范围 |
| `GET /api/records` | 未封装 | 病历检索未接入当前患者端 |
| `GET /api/records/{id}` | 未封装 | 当前患者端直接复用了 `GET /api/orders/{id}` |
| `GET /api/patient/{id}/history` | 未封装 | 患者历史病历未单独接入 |
| `GET /api/doctor/profile` | 未封装 | 医生端范围 |
| `PUT /api/doctor/profile` | 未封装 | 医生端范围 |
| `GET /api/knowledge/case/doctor` | 未封装 | 知识图谱/医生端范围 |
| `POST /api/knowledge/case` | 未封装 | 知识图谱/医生端范围 |
| `GET /api/admin/users` | 未封装 | 管理端范围 |

## 6. 建议优先级

建议按下面顺序处理：

1. 修复 `api/sse-parser.js` 对 `[METADATA]` 的处理，并补测试
2. 明确 `chat` 与 `chat/stream` 的最终规范，删除文档中的冲突表述
3. 把 `/api/patient/notifications` 正式补入规范，或前端停止依赖该接口
4. 补齐诊断结果页与历史详情页的数据展示，至少把已映射的数据真正展示出来
5. 为 `ongoing / cancelled` 补齐历史状态文案、统计和样式
6. 补齐规范中缺失的 `/api/admin/users` 正文定义，修正“附录 F”引用
