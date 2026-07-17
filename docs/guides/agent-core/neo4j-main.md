# neo4j_2 知识图谱查询接口说明

本目录用于交付给 Agent 开发同学。`knowledge_graph_query.js` 已封装 Neo4j 连接和固定 Cypher 查询，Agent 只传接口名与参数，接收 JSON，不需要拼接 Cypher。

## 文件说明

- `knowledge_graph_query.js`: 查询接口主文件，内置 0d140a6a Neo4j Aura 连接参数，支持方剂、中药、症状、功效等维度检索。
- `package.json`: Node.js 项目配置，声明 `neo4j-driver` 依赖。
- `package-lock.json`: 依赖锁定文件。

## 安装与验证

```powershell
npm install
node knowledge_graph_query.js healthCheck
```

旧版症状查询方式仍可用：

```powershell
node knowledge_graph_query.js "头痛 发寒 无汗"
```

在 Node.js 中推荐使用统一入口：

```js
const kg = require("./knowledge_graph_query");

const result = await kg.runAgentQuery("recommendClinicalOptions", {
  description: "头痛 发寒 无汗 咳嗽",
  limit: 5
});

console.log(JSON.stringify(result, null, 2));
await kg.close();
```

也可以直接调用单个函数：

```js
const { searchFormulasBySymptom, close } = require("./knowledge_graph_query");

const result = await searchFormulasBySymptom({
  symptom: "头痛 发寒 无汗",
  limit: 5
});

await close();
```

## 通用返回格式

成功：

```json
{
  "ok": true,
  "query": "接口名",
  "params": {},
  "data": {}
}
```

失败：

```json
{
  "ok": false,
  "query": "接口名",
  "error": "错误信息"
}
```

未知接口会返回 `availableActions`，列出可用接口名。

## 接口列表

### healthCheck

检查 Neo4j 是否可连接，并返回节点和关系总数。

参数：无。

```js
await kg.runAgentQuery("healthCheck");
```

返回核心字段：

- `data.connected`: 是否连接成功。
- `data.database`: 当前数据库名。
- `data.nodes`: 节点总数。
- `data.relationships`: 关系总数。

### graphSummary

返回图谱标签和关系类型统计。

参数：无。

```js
await kg.runAgentQuery("graphSummary");
```

返回核心字段：

- `data.labels`: 标签统计，如 `方名`、`中药名`、`功效`、`症状病症`。
- `data.relationships`: 关系统计，如 `治疗`、`中药组成`、`功效`、`常用配伍`。

### searchFormulasBySymptom

按患者症状或自然语言描述召回候选方剂。

参数：

- `symptom`: string，可选，单个症状。
- `symptoms`: string[]，可选，多个症状。
- `description`: string，可选，自然语言描述。
- `limit`: number，可选，默认 10，最大 50。

```js
await kg.runAgentQuery("searchFormulasBySymptom", {
  symptom: "头痛 发寒 无汗",
  limit: 5
});
```

返回每个方剂包含：

- `id`, `name`, `sourceUrl`, `sourceId`
- `score`: 匹配分数。
- `matchedSymptoms`: 命中的图谱症状。
- `matchedQueryTerms`: 命中的用户输入词。
- `herbs`: 中药组成，包含药名、剂量及可用的中药功效/禁忌。
- `effects`, `indications`, `symptoms`, `usages`, `contraindications`, `sources`, `categories`

### searchFormulasByEffect

按功效检索方剂，既匹配方剂自身功效，也参考组成中药的功效。

参数：

- `effect`: string，必填，如 `止咳平喘`。
- `limit`: number，可选。

```js
await kg.runAgentQuery("searchFormulasByEffect", {
  effect: "止咳平喘",
  limit: 5
});
```

返回字段同方剂结果，并额外包含：

- `matchedFormulaEffects`: 命中的方剂功效。
- `matchedHerbEffects`: 命中的中药功效。
- `score`: 匹配分数。

### searchFormulaByName

按方剂名称检索方剂详情。

参数：

- `formula`: string，必填，如 `麻黄汤`。
- `limit`: number，可选。

```js
await kg.runAgentQuery("searchFormulaByName", {
  formula: "麻黄汤"
});
```

### getFormulaDetail

获取单个方剂详情。适合 Agent 在已拿到候选方剂后进行二次展开。

参数：

- `id`: string，可选，方剂 ID。
- `name` / `formula`: string，可选，方剂名。

`id` 或 `name` 至少传一个。

```js
await kg.runAgentQuery("getFormulaDetail", {
  name: "麻黄汤"
});
```

返回：

- 方剂基本信息。
- `prescription`: 处方节点及中药组成。
- `herbs`: 中药组成快捷字段。
- `effects`, `indications`, `symptoms`, `usages`, `contraindications`, `sources`, `categories`
- `rawText`: 原始方剂文本，便于 Agent 生成解释时引用和核对。

### searchHerbs

按中药名、功效、主治、类别、性味、归经等维度检索中药。

参数：

- `keyword`: string，必填，如 `咳嗽`、`止咳`、`温`、`肺经`。
- `limit`: number，可选。
- `includeFormulaOnly`: boolean，可选，默认 `false`。

默认只查已从中药详情页增强过的 `中药名` 节点，以减少方剂处方解析噪声。若需要连方剂处方中仅出现过、但没有中药详情的药名一起查，可传 `includeFormulaOnly: true`。

```js
await kg.runAgentQuery("searchHerbs", {
  keyword: "咳嗽",
  limit: 5
});
```

返回每味中药包含：

- `id`, `name`, `sourceUrl`
- `aliases`, `effectText`, `indicationText`, `usageText`, `contraindicationText`
- `effects`, `symptoms`, `categories`, `natures`, `meridians`, `contraindications`
- `pairings`: 常用配伍。
- `relatedFormulas`: 图谱中包含该中药的方剂。
- `score`: 匹配分数。

### getHerbDetail

获取单味中药详情。

参数：

- `id`: string，可选，中药 ID。
- `name` / `herb`: string，可选，中药名。

```js
await kg.runAgentQuery("getHerbDetail", {
  name: "杏仁"
});
```

返回：

- 中药基础属性和原始文本。
- `effects`, `symptoms`, `indications`, `categories`, `natures`, `meridians`
- `contraindications`, `pairings`
- `relatedFormulas`

### recommendClinicalOptions

综合症状、功效、指定方剂或指定中药召回临床候选方案。适合 Agent 面向患者描述生成初步方案草稿时使用。

参数：

- `description`: string，可选，自然语言症状描述。
- `symptom` / `symptoms`: string 或 string[]，可选。
- `effect`: string，可选，期望功效。
- `formula`: string，可选，指定或偏好的方剂名。
- `herb`: string，可选，指定或偏好的中药名。
- `limit`: number，可选。

```js
await kg.runAgentQuery("recommendClinicalOptions", {
  description: "头痛 发寒 无汗 咳嗽",
  limit: 5
});
```

返回：

- `data.formulas`: 推荐方剂列表，包含组成、功效、主治、用法、禁忌、匹配词和分数。
- `data.relatedHerbs`: 与推荐方剂组成相关的中药详情。
- `data.note`: 安全提示。

## 兼容接口

`queryKnowledgeGraph(symptom)` 保留旧版调用方式，本质上调用 `searchFormulasBySymptom`：

```js
const result = await kg.queryKnowledgeGraph("头痛 发寒 无汗");
```

返回：

- `symptom`
- `queryTerms`
- `count`
- `formulas`

## Agent 使用建议

推荐调用顺序：

1. 用 `recommendClinicalOptions` 根据患者描述召回候选方剂和相关中药。
2. 对候选方剂调用 `getFormulaDetail` 展开原始用法、禁忌和处方组成。
3. 对关键中药调用 `getHerbDetail` 或 `searchHerbs` 检查功效、归经、禁忌、常用配伍。
4. Agent 自行识别并过滤患者提到的过敏、孕产妇、儿童、基础疾病、禁忌药物等风险因素。

本查询层只做知识图谱召回，不替代执业医师诊疗。所有输出都应作为学习和辅助分析材料，不能直接作为临床处方。

## 可选环境变量

虽然 JS 文件内置了 Neo4j Aura 连接参数，仍支持环境变量覆盖：

- `NEO4J_URI`
- `NEO4J_USERNAME`
- `NEO4J_PASSWORD`
- `NEO4J_DATABASE`
- `KG_QUERY_LIMIT`

注意：本目录包含可连接 Neo4j Aura 的账号信息，请不要上传到公开仓库或公开聊天记录。
