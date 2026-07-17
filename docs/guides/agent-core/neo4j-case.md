# case_neo4j 对接说明

本说明用于把 `case_neo4j` 文件夹交给 AI Agent 开发同学时快速对接。该文件夹提供一个固定 Neo4j 查询接口层：Agent 只需要传入接口名称和参数，JS 文件内部负责连接 Neo4j、执行 Cypher，并返回 JSON。

## 文件说明

| 文件 | 作用 |
| --- | --- |
| `neo4j_agent_api.js` | Agent 调用入口。内部封装 Neo4j 连接、固定 Cypher 查询、参数校验和 JSON 返回格式。 |
| `package.json` | Node.js 项目依赖声明，主要依赖 `neo4j-driver`。 |
| `package-lock.json` | 锁定依赖版本，保证对接同学安装到一致依赖。 |

## 环境要求

- Node.js 18 或以上版本，推荐 Node.js 20+。
- 可访问 Neo4j Aura 网络地址。
- 首次使用需要在 `case_neo4j` 目录下安装依赖：

```bash
npm install
```

快速连通性检查：

```bash
npm run health
```

或：

```bash
node neo4j_agent_api.js healthCheck
```

正常情况下会返回类似：

```json
{
  "ok": true,
  "data": {
    "nodes": 29462,
    "relationships": 58267,
    "database": "611304ef"
  }
}
```

## 调用方式

推荐统一入口：

```js
const kg = require("./neo4j_agent_api");

const result = await kg.runAgentQuery("recommendClinicalOptions", {
  symptoms: ["头痛", "眩晕", "失眠"],
  disease: "高血压",
  limit: 5
});

console.log(JSON.stringify(result, null, 2));
await kg.close();
```

也可以直接调用命名函数：

```js
const kg = require("./neo4j_agent_api");

const result = await kg.searchByDisease({
  disease: "关节炎",
  limit: 10
});

await kg.close();
```

命令行调试：

```bash
node neo4j_agent_api.js searchByDisease "{\"disease\":\"关节炎\",\"limit\":5}"
```

在 Windows PowerShell 中，复杂 JSON 参数建议用 JS 调用方式，避免命令行引号转义问题。

## 统一返回格式

成功：

```json
{
  "ok": true,
  "query": "searchByDisease",
  "params": {},
  "data": []
}
```

失败：

```json
{
  "ok": false,
  "query": "searchByDisease",
  "error": "disease is required"
}
```

未知接口：

```json
{
  "ok": false,
  "error": "Unknown action: xxx",
  "availableActions": []
}
```

## 接口列表

### 1. `healthCheck`

检查 Neo4j 是否可连接，并返回知识图谱规模。

参数：无。

示例：

```js
await kg.runAgentQuery("healthCheck");
```

返回字段：

| 字段 | 说明 |
| --- | --- |
| `data.nodes` | `KGNode` 总节点数。 |
| `data.relationships` | 901020 医案图谱关系数。 |
| `data.database` | 当前连接数据库名称。 |

### 2. `graphSummary`

返回各类节点和关系的数量统计。

参数：无。

示例：

```js
await kg.runAgentQuery("graphSummary");
```

返回字段：

| 字段 | 说明 |
| --- | --- |
| `data.labels` | 节点标签统计，如 `医案`、`病名`、`证型`、`方剂`、`中药名`。 |
| `data.relationships` | 关系类型统计，如 `涉及病名`、`辨证为`、`使用方剂`。 |

### 3. `searchByDisease`

按病名检索相关医案，并返回关联证型、方剂、名医和治法。

参数：

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `disease` | string | 是 | 病名关键词，如 `关节炎`、`高血压`、`子宫肌瘤`。 |
| `limit` | number | 否 | 返回条数，默认 10，最大 50。 |

示例：

```js
await kg.runAgentQuery("searchByDisease", {
  disease: "关节炎",
  limit: 5
});
```

主要返回字段：

| 字段 | 说明 |
| --- | --- |
| `caseId` | 医案节点 ID。 |
| `title` | 医案标题。 |
| `summary` | 医案摘要。 |
| `sourceUrl` | 来源网页。 |
| `diseases` | 关联病名。 |
| `syndromes` | 关联证型。 |
| `formulas` | 关联方剂。 |
| `doctors` | 关联名医。 |
| `treatmentMethods` | 关联治法。 |

### 4. `searchBySyndrome`

按证型检索相关医案和推荐方剂。

参数：

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `syndrome` | string | 是 | 证型关键词，如 `湿热`、`肝肾不足`、`气滞血瘀`。 |
| `limit` | number | 否 | 返回条数，默认 10，最大 50。 |

示例：

```js
await kg.runAgentQuery("searchBySyndrome", {
  syndrome: "湿热",
  limit: 5
});
```

返回字段与 `searchByDisease` 类似。

### 5. `searchByDoctor`

按名医名字检索相关医案，并返回关联病名、证型、方剂、治法和名医。匹配方式为对 `:名医` 节点 `name` 做 `CONTAINS` 模糊匹配，再沿 `医案 -[:关联名医]-> 名医` 召回医案。

参数：

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `doctor` | string | 是 | 名医名字关键词，如 `刘渡舟`、`张仲景`、`胡希恕`。也可传 `keyword`。 |
| `limit` | number | 否 | 返回条数，默认 10，最大 50。 |

示例：

```js
await kg.runAgentQuery("searchByDoctor", {
  doctor: "刘渡舟",
  limit: 5
});
```

主要返回字段：

| 字段 | 说明 |
| --- | --- |
| `caseId` | 医案节点 ID。 |
| `title` | 医案标题。 |
| `summary` | 医案摘要。 |
| `sourceUrl` | 来源网页。 |
| `publishDate` | 发布日期。 |
| `diseases` | 关联病名。 |
| `syndromes` | 关联证型。 |
| `formulas` | 关联方剂。 |
| `treatmentMethods` | 关联治法。 |
| `doctors` | 该医案关联的全部名医（含被查询的名医）。 |

### 6. `searchByDoctorId`

按名医节点 id 精确查询相关医案。与 `searchByDoctor`（按名字模糊匹配）互补：当后端已知名医节点 id 时，用本接口做精确召回，避免同名/名字包含带来的歧义。匹配方式为 `MATCH (:名医 {id: $doctorId})`，再沿 `医案 -[:关联名医]-> 名医` 召回医案。

参数：

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `doctorId` | string | 是 | 名医节点 id，如 `DOCTOR_b54c2314bc9a5698`。也可传 `id`。 |
| `limit` | number | 否 | 返回条数，默认 10，最大 50。 |

示例：

```js
await kg.runAgentQuery("searchByDoctorId", {
  doctorId: "DOCTOR_b54c2314bc9a5698",
  limit: 5
});
```

主要返回字段：

| 字段 | 说明 |
| --- | --- |
| `caseId` | 医案节点 ID。 |
| `title` | 医案标题。 |
| `summary` | 医案摘要。 |
| `sourceUrl` | 来源网页。 |
| `publishDate` | 发布日期。 |
| `diseases` | 关联病名。 |
| `syndromes` | 关联证型。 |
| `formulas` | 关联方剂。 |
| `treatmentMethods` | 关联治法。 |
| `doctors` | 该医案关联的全部名医（含被查询的名医）。 |

> 若 `doctorId` 不存在或该名医无关联医案，`data` 返回空数组。

### 7. `searchByFormula`

按方剂名查询方剂、组成药物和关联医案。精确方名优先返回。

参数：

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `formula` | string | 是 | 方剂关键词，如 `桂枝汤`、`柴胡桂枝汤`、`真武汤`。 |
| `limit` | number | 否 | 返回条数，默认 10，最大 50。 |

示例：

```js
await kg.runAgentQuery("searchByFormula", {
  formula: "柴胡桂枝汤",
  limit: 5
});
```

主要返回字段：

| 字段 | 说明 |
| --- | --- |
| `formulaId` | 方剂节点 ID。 |
| `name` | 方剂名。 |
| `matchScore` | 匹配分，精确匹配最高。 |
| `herbs` | 组成药物数组，含 `name` 和 `dosage`。 |
| `cases` | 使用该方剂的医案列表。 |

### 8. `searchCases`

对医案标题、摘要、原文做全文检索，适合处理患者自然语言描述的第一步召回。

参数：

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `keyword` | string | 是 | 检索关键词或短句。也可传 `description`。 |
| `limit` | number | 否 | 返回条数，默认 10，最大 50。 |

示例：

```js
await kg.runAgentQuery("searchCases", {
  keyword: "头痛 眩晕 失眠",
  limit: 10
});
```

主要返回字段：

| 字段 | 说明 |
| --- | --- |
| `score` | Neo4j 全文索引相关度分数。 |
| `title` | 医案标题。 |
| `summary` | 医案摘要。 |
| `diseases` | 关联病名。 |
| `syndromes` | 关联证型。 |
| `formulas` | 关联方剂。 |

### 9. `recommendFormulas`

根据病名、证型、症状中的任意组合推荐方剂。

参数：

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `disease` | string | 否 | 病名关键词。 |
| `syndrome` | string | 否 | 证型关键词。 |
| `symptom` | string | 否 | 症状关键词。也可传 `keyword`。 |
| `limit` | number | 否 | 返回条数，默认 20，最大 50。 |

至少需要传入 `disease`、`syndrome`、`symptom` 之一。

示例：

```js
await kg.runAgentQuery("recommendFormulas", {
  disease: "高血压",
  symptom: "头晕",
  limit: 10
});
```

主要返回字段：

| 字段 | 说明 |
| --- | --- |
| `formula` | 推荐方剂。 |
| `support` | 支持该推荐的医案数量。 |
| `evidenceCases` | 证据医案标题。 |
| `herbs` | 组成药物。 |

### 10. `recommendClinicalOptions`

综合推荐接口，适合 Agent 根据患者描述调用。它会根据症状、病名、证型、方剂线索召回医案，并汇总推荐方剂。

参数：

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `description` | string | 否 | 患者自然语言描述。 |
| `symptoms` | string[] | 否 | 症状数组，如 `["头痛", "眩晕"]`。 |
| `keywords` | string[] | 否 | 关键词数组。 |
| `disease` | string | 否 | 病名关键词。 |
| `syndrome` | string | 否 | 证型关键词。 |
| `formula` | string | 否 | 方剂关键词。 |
| `limit` | number | 否 | 医案返回条数，默认 10，最大 50。 |

至少需要传入 `description`、`symptoms`、`keywords`、`disease`、`syndrome`、`formula` 之一。

示例：

```js
await kg.runAgentQuery("recommendClinicalOptions", {
  symptoms: ["头痛", "眩晕", "失眠"],
  disease: "高血压",
  limit: 5
});
```

主要返回字段：

| 字段 | 说明 |
| --- | --- |
| `data.cases` | 匹配医案列表，含病名、证型、症状、方剂、治法、名医等。 |
| `data.recommendedFormulas` | 基于匹配医案汇总出的推荐方剂。 |
| `recommendedFormulas.support` | 支持医案数量。 |
| `recommendedFormulas.score` | 综合匹配分。 |
| `recommendedFormulas.evidenceCases` | 支持推荐的医案标题。 |
| `recommendedFormulas.herbs` | 方剂组成药物。 |

### 11. `getCaseDetail`

按医案 ID 或标题查询详情，适合 Agent 在选中某条医案后补充原文依据。

参数：

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `caseId` | string | 否 | 医案节点 ID，如 `CASE_901020_yian_2988`。 |
| `title` | string | 否 | 医案标题关键词。 |
| `limit` | number | 否 | 返回条数，默认 5，最大 50。 |

`caseId` 和 `title` 至少传一个。

示例：

```js
await kg.runAgentQuery("getCaseDetail", {
  caseId: "CASE_901020_yian_2988"
});
```

主要返回字段：

| 字段 | 说明 |
| --- | --- |
| `rawText` | 医案原文文本。 |
| `summary` | 摘要。 |
| `sourceUrl` | 来源网页。 |
| `diseases` | 关联病名。 |
| `syndromes` | 关联证型。 |
| `symptoms` | 关联症状。 |
| `formulas` | 关联方剂。 |
| `treatmentMethods` | 关联治法。 |

### 12. `addCase`

新增单个医案，并自动建立与病名、证型、症状、方剂、治法、名医、栏目的关联关系。**这是目前唯一的写入接口**，其余 11 个均为只读查询。

节点写入规则：

- 医案节点按 `caseId` 去重（`caseId = CASE_901020_manual_<时间戳>_<随机数>`，每次调用生成新值，因此重复提交同一标题会创建多条医案）。
- 病名 / 证型 / 症状 / 方剂 / 治法 / 名医 / 栏目 等实体节点按 `name` 去重：已存在则复用，不存在则新建。
- 实体节点 id：若后端在对象形式中传入了 `id` 且非空，则优先使用传入值；未传或为空时，回退为确定性生成方案 `类型前缀_md5(name)前16位`。由于建点用 `MERGE (n {name}) ON CREATE SET n.id`，**已存在的实体不会被覆盖**，仅新建实体时才写入 id。
- 所有新建关系带 `source_id`，前缀为 `901020_manual_`，与原有 `901020_` 医案图谱关系同构，可被 `healthCheck` / `graphSummary` 统计到。

参数：

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `title` | string | 是 | 医案标题。 |
| `summary` | string | 否 | 医案摘要。 |
| `rawText` | string | 否 | 医案原文。 |
| `sourceUrl` | string | 否 | 来源网页链接。 |
| `publishDate` | string | 否 | 发布日期，如 `2026-07-12`。 |
| `author` | string | 否 | 作者；不传默认 `前端录入`。 |
| `channel` | string | 否 | 所属栏目。 |
| `diseases` | string \| string[] \| `{name,id}`[] | 否 | 关联病名。字符串可用逗号 / 顿号 / 分号分隔，也可传数组或 `{name,id}` 对象数组。 |
| `syndromes` | string \| string[] \| `{name,id}`[] | 否 | 关联证型，形式同上。 |
| `symptoms` | string \| string[] \| `{name,id}`[] | 否 | 关联症状，形式同上。 |
| `formulas` | string \| string[] \| `{name,id}`[] | 否 | 关联方剂，形式同上。 |
| `treatmentMethods` | string \| string[] \| `{name,id}`[] | 否 | 关联治法，形式同上。 |
| `doctors` | string \| string[] \| `{name,id}`[] | 否 | 关联名医，形式同上。对象形式可传 `id` 指定节点 id。 |

> 对象形式 `{name, id}`：`id` 非空时优先使用传入值，为空则回退 `类型前缀_md5(name)前16位`。`channel` 仅接受字符串。

示例：

```js
await kg.runAgentQuery("addCase", {
  title: "张氏治眩晕验案",
  summary: "平肝潜阳，疗效显著",
  rawText: "患者，男，52岁，眩晕伴头痛……",
  publishDate: "2026-07-12",
  diseases: "眩晕, 头痛",
  syndromes: ["肝阳上亢"],
  symptoms: ["头晕"],
  formulas: ["天麻钩藤饮"],
  treatmentMethods: "平肝潜阳",
  doctors: [
    { name: "刘渡舟", id: "DOCTOR_b54c2314bc9a5698" }, // 传入 id（已存在则保留原 id）
    "张仲景"                                          // 不传 id，自动生成
  ]
});
```

返回字段：

| 字段 | 说明 |
| --- | --- |
| `caseId` | 新建医案节点 ID，形如 `CASE_901020_manual_1783852870971_627`。 |
| `sourceId` | 本次写入的关系来源 ID（与 `caseId` 同源）。 |
| `linked` | 各实体类型实际关联的条数，如 `{ diseases: 2, syndromes: 1, symptoms: 1, formulas: 1, treatmentMethods: 1, doctors: 1, channel: 1 }`。 |

写入失败（如缺 `title`）返回：

```json
{
  "ok": false,
  "error": "title is required"
}
```

## 推荐给 Agent 的调用流程

患者自然语言描述场景：

1. 调用 `recommendClinicalOptions`，传入 `description` 或 `symptoms`，可附带 `disease`、`syndrome`。
2. 从 `data.cases` 读取相似医案证据。
3. 从 `data.recommendedFormulas` 读取推荐方剂和组成。
4. 如需更多原文依据，调用 `getCaseDetail` 查询具体医案。

结构化检索场景：

- 用户问某个病：调用 `searchByDisease`。
- 用户问某个证型：调用 `searchBySyndrome`。
- 用户问某个名医：调用 `searchByDoctor`。
- 已知名医节点 id：调用 `searchByDoctorId`。
- 用户问某个方：调用 `searchByFormula`。
- 用户只给一段症状描述：调用 `searchCases` 或 `recommendClinicalOptions`。

## 注意事项

- 本接口返回的是知识图谱检索和关联推荐结果，不是最终医疗诊断。
- AI Agent 在生成回答时，应明确说明“仅供学习、科研和辅助参考，不能替代执业医师诊疗”。
- `limit` 最大限制为 50，防止一次返回过多内容。
- 查询使用 `CONTAINS` 和全文索引，适合中文关键词召回，但仍可能存在噪声，Agent 需要结合证据医案做二次筛选。
- 使用完成后建议调用 `await kg.close()` 关闭 Neo4j Driver 连接。
