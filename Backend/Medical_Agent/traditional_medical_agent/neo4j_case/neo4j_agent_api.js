const neo4j = require("neo4j-driver");
const crypto = require("crypto");

const CONFIG = Object.freeze({
  uri: process.env.NEO4J_CASE_URI,
  username: process.env.NEO4J_CASE_USERNAME,
  password: process.env.NEO4J_CASE_PASSWORD,
  database: process.env.NEO4J_CASE_DATABASE,
});

const DEFAULT_LIMIT = 10;
const MAX_LIMIT = 50;
let driver;

function getDriver() {
  if (!CONFIG.uri || !CONFIG.username || !CONFIG.password || !CONFIG.database) {
    throw new Error("NEO4J_CASE_URI、NEO4J_CASE_USERNAME、NEO4J_CASE_PASSWORD、NEO4J_CASE_DATABASE 必须配置");
  }
  if (!driver) {
    driver = neo4j.driver(CONFIG.uri, neo4j.auth.basic(CONFIG.username, CONFIG.password));
  }
  return driver;
}

async function close() {
  if (driver) {
    await driver.close();
    driver = undefined;
  }
}

function asLimit(value, fallback = DEFAULT_LIMIT) {
  const parsed = Number.parseInt(value, 10);
  if (!Number.isFinite(parsed) || parsed <= 0) return fallback;
  return Math.min(parsed, MAX_LIMIT);
}

function asText(value) {
  return typeof value === "string" ? value.trim() : "";
}

function normalizeTerms(params = {}) {
  const values = [];
  if (Array.isArray(params.symptoms)) values.push(...params.symptoms);
  if (Array.isArray(params.keywords)) values.push(...params.keywords);
  if (params.symptom) values.push(params.symptom);
  if (params.keyword) values.push(params.keyword);
  if (params.description) values.push(params.description);

  const stopWords = new Set(["患者", "症状", "出现", "伴有", "感觉", "治疗", "中医", "建议"]);
  const terms = values
    .flatMap((value) => String(value || "").split(/[,\s，。；;、/|]+/u))
    .map((value) => value.trim())
    .filter((value) => value.length >= 2 && !stopWords.has(value));
  return [...new Set(terms)].slice(0, 12);
}

function nativeValue(value) {
  if (neo4j.isInt(value)) return value.toNumber();
  if (Array.isArray(value)) return value.map(nativeValue);
  if (value && typeof value === "object") {
    const object = {};
    for (const [key, item] of Object.entries(value)) object[key] = nativeValue(item);
    return object;
  }
  return value;
}

function cypherValue(value) {
  if (Number.isSafeInteger(value)) return neo4j.int(value);
  if (Array.isArray(value)) return value.map(cypherValue);
  if (value && typeof value === "object") {
    const object = {};
    for (const [key, item] of Object.entries(value)) object[key] = cypherValue(item);
    return object;
  }
  return value;
}

function cypherParams(params) {
  const converted = {};
  for (const [key, value] of Object.entries(params || {})) converted[key] = cypherValue(value);
  return converted;
}

function recordsToObjects(result) {
  return result.records.map((record) => {
    const object = {};
    for (const key of record.keys) object[key] = nativeValue(record.get(key));
    return object;
  });
}

function cleanHerbs(herbs) {
  const noise = new Set(["日", "续进", "嘱一顿服"]);
  return (herbs || [])
    .filter((item) => item && item.name && !noise.has(item.name))
    .filter((item) => !/(嘱|续进|每日|每服|水煎|温服)/u.test(item.name))
    .map((item) => ({ name: item.name, dosage: item.dosage || null }));
}

async function readQuery(cypher, params = {}) {
  const session = getDriver().session({ database: CONFIG.database, defaultAccessMode: neo4j.session.READ });
  try {
    const result = await session.executeRead((tx) => tx.run(cypher, cypherParams(params)));
    return recordsToObjects(result);
  } finally {
    await session.close();
  }
}

// 写入事务：WRITE 模式，用于新增/修改图谱数据
async function writeQuery(cypher, params = {}) {
  const session = getDriver().session({ database: CONFIG.database, defaultAccessMode: neo4j.session.WRITE });
  try {
    const result = await session.executeWrite((tx) => tx.run(cypher, cypherParams(params)));
    return recordsToObjects(result);
  } finally {
    await session.close();
  }
}

// 由名称生成与现有图谱同构的确定性节点 id（类型前缀 + md5 前 16 位）
function makeEntityId(prefix, name) {
  const hash = crypto.createHash("md5").update(String(name), "utf8").digest("hex").slice(0, 16);
  return `${prefix}_${hash}`;
}

// 将字符串或数组归一化为去空白、去重的标签数组（按逗号/顿号/分号/斜杠/竖线切分，保留名称内空格）
function normalizeTags(value) {
  if (value == null) return [];
  const raw = Array.isArray(value) ? value.map(String) : String(value).split(/[,\n，、；;|/]+/u);
  return [...new Set(raw.map((item) => item.trim()).filter(Boolean))];
}

// 将字符串/数组/对象数组归一化为 {name, id?} 实体列表。
// 支持三种传入形式：纯字符串("刘渡舟")、字符串数组(["刘渡舟"])、对象数组([{name:"刘渡舟",id:"DOCTOR_xxx"}])。
// 传入的 id 原样保留（留空交由调用方生成）；同名去重，保留首个及其 id。
function normalizeEntities(value) {
  if (value == null) return [];
  const raw = Array.isArray(value) ? value : [value];
  const items = [];
  for (const entry of raw) {
    if (entry == null) continue;
    if (typeof entry === "string") {
      for (const name of entry.split(/[,\n，、；;|/]+/u)) {
        const trimmed = name.trim();
        if (trimmed) items.push({ name: trimmed, id: "" });
      }
    } else if (typeof entry === "object") {
      const name = asText(entry.name);
      if (!name) continue;
      items.push({ name, id: asText(entry.id) });
    }
  }
  const seen = new Map();
  for (const item of items) {
    if (!seen.has(item.name)) seen.set(item.name, item);
  }
  return [...seen.values()];
}

// 各实体类型的标签、关系名、id 前缀（与现有图谱保持同构）
const ENTITY_TYPES = Object.freeze({
  diseases:         { label: "病名", rel: "涉及病名", prefix: "DISEASE" },
  syndromes:        { label: "证型", rel: "辨证为",   prefix: "SYNDROME" },
  symptoms:         { label: "症状", rel: "表现症状", prefix: "SYMPTOM" },
  formulas:         { label: "方剂", rel: "使用方剂", prefix: "FORMULA" },
  treatmentMethods: { label: "治法", rel: "采用治法", prefix: "PRINCIPLE" },
  // 医生 ID 与业务系统一致，写医案时应复用已有医生节点，避免与全局 id 唯一约束冲突。
  doctors:          { label: "名医", rel: "关联名医", prefix: "DOCTOR", matchById: true },
});

// 新增单个医案及其关联实体与关系
async function addCase(params = {}) {
  const title = asText(params.title);
  if (!title) throw new Error("title is required");

  const sourceId = `901020_manual_${Date.now()}_${Math.floor(Math.random() * 1000)}`;
  const caseId = `CASE_${sourceId}`;

  // 医案主体节点属性
  const caseProps = {
    caseId,
    sourceId,
    title,
    summary: asText(params.summary),
    rawText: asText(params.rawText),
    sourceUrl: asText(params.sourceUrl),
    publishDate: asText(params.publishDate),
    author: asText(params.author) || "前端录入",
    channel: asText(params.channel),
  };

  // 组装各实体参数（name + id）。id 优先用后端传入值，未传则用确定性生成方案回退。
  const entityParams = {};
  const linked = {};
  for (const [key, cfg] of Object.entries(ENTITY_TYPES)) {
    const items = normalizeEntities(params[key]);
    entityParams[key] = items.map((item) => ({
      name: item.name,
      id: item.id || makeEntityId(cfg.prefix, item.name),
    }));
    linked[key] = items.length;
  }
  const channelNames = normalizeTags(params.channel ? [params.channel] : []);
  entityParams.channels = channelNames.map((name) => ({ name, id: makeEntityId("CHANNEL", name) }));
  linked.channel = channelNames.length;

  // 动态拼接各实体类型的 UNWIND 建点建边块（每块使用独立变量名，避免作用域冲突）
  const blocks = [];
  for (const [key, cfg] of Object.entries(ENTITY_TYPES)) {
    if (!entityParams[key].length) continue;
    const nodeMatch = cfg.matchById
      ? `{id: ${key}_item.id}`
      : `{name: ${key}_item.name}`;
    const onCreate = cfg.matchById
      ? `ON CREATE SET ${key}_node.name = ${key}_item.name`
      : `ON CREATE SET ${key}_node.id = ${key}_item.id`;
    blocks.push(`
    WITH c
    UNWIND $${key} AS ${key}_item
      MERGE (${key}_node:KGNode:${cfg.label} ${nodeMatch})
      ${onCreate}
      MERGE (c)-[:${cfg.rel} {source_id: $sourceId}]->(${key}_node)`);
  }
  if (entityParams.channels.length) {
    blocks.push(`
    WITH c
    UNWIND $channels AS channel_item
      MERGE (channel_node:KGNode:栏目 {name: channel_item.name})
      ON CREATE SET channel_node.id = channel_item.id
      MERGE (c)-[:属于栏目 {source_id: $sourceId}]->(channel_node)`);
  }

  const cypher = `
    MERGE (c:KGNode:医案 {id: $caseId})
      ON CREATE SET
        c.name = $title,
        c.source_id = $sourceId,
        c.source_url = $sourceUrl,
        c.summary = $summary,
        c.raw_text = $rawText,
        c.author = $author,
        c.publish_date = $publishDate,
        c.channel = $channel,
        c.views = null
      ON MATCH SET
        c.name = $title,
        c.summary = coalesce(c.summary, $summary),
        c.raw_text = coalesce(c.raw_text, $rawText),
        c.source_url = coalesce(c.source_url, $sourceUrl),
        c.publish_date = coalesce(c.publish_date, $publishDate),
        c.author = coalesce(c.author, $author),
        c.channel = coalesce(c.channel, $channel)
    ${blocks.join("\n")}
    RETURN c.id AS caseId
  `;

  await writeQuery(cypher, { ...caseProps, ...entityParams });
  return { ok: true, query: "addCase", caseId, sourceId, linked };
}

function requireKeyword(name, value) {
  const text = asText(value);
  if (!text) throw new Error(`${name} is required`);
  return text;
}

async function healthCheck() {
  const rows = await readQuery(`
    CALL {
      MATCH (n:KGNode)
      RETURN count(n) AS nodes
    }
    CALL {
      MATCH ()-[r]->()
      WHERE r.source_id STARTS WITH '901020_'
      RETURN count(r) AS relationships
    }
    RETURN nodes, relationships, $database AS database
  `, { database: CONFIG.database });
  return { ok: true, data: rows[0] || {} };
}

async function graphSummary() {
  const rows = await readQuery(`
    CALL {
      MATCH (n:KGNode)
      UNWIND labels(n) AS label
      WITH label, count(*) AS count
      WHERE label <> 'KGNode'
      RETURN collect({label: label, count: count}) AS labels
    }
    CALL {
      MATCH ()-[r]->()
      WHERE r.source_id STARTS WITH '901020_'
      WITH type(r) AS type, count(*) AS count
      RETURN collect({type: type, count: count}) AS relationships
    }
    RETURN labels, relationships
  `);
  return { ok: true, data: rows[0] || { labels: [], relationships: [] } };
}

async function searchByDisease(params = {}) {
  const disease = requireKeyword("disease", params.disease || params.keyword);
  const limit = asLimit(params.limit);
  const rows = await readQuery(`
    MATCH (d:病名)
    WHERE d.name CONTAINS $disease
    MATCH (c:医案)-[:涉及病名]->(d)
    WITH DISTINCT c
    ORDER BY coalesce(c.publish_date, '') DESC, c.name
    LIMIT $limit
    CALL {
      WITH c
      OPTIONAL MATCH (c)-[:涉及病名]->(d2:病名)
      RETURN collect(DISTINCT d2.name)[..20] AS diseases
    }
    CALL {
      WITH c
      OPTIONAL MATCH (c)-[:辨证为]->(s:证型)
      RETURN collect(DISTINCT s.name)[..20] AS syndromes
    }
    CALL {
      WITH c
      OPTIONAL MATCH (c)-[:使用方剂]->(f:方剂)
      RETURN collect(DISTINCT f.name)[..20] AS formulas
    }
    CALL {
      WITH c
      OPTIONAL MATCH (c)-[:关联名医]->(doctor:名医)
      RETURN collect(DISTINCT doctor.name)[..10] AS doctors
    }
    CALL {
      WITH c
      OPTIONAL MATCH (c)-[:采用治法]->(method:治法)
      RETURN collect(DISTINCT method.name)[..20] AS treatmentMethods
    }
    RETURN c.id AS caseId,
           c.name AS title,
           c.summary AS summary,
           c.source_url AS sourceUrl,
           c.publish_date AS publishDate,
           diseases,
           syndromes,
           formulas,
           doctors,
           treatmentMethods
  `, { disease, limit });
  return { ok: true, query: "searchByDisease", params: { disease, limit }, data: rows };
}

async function searchBySyndrome(params = {}) {
  const syndrome = requireKeyword("syndrome", params.syndrome || params.keyword);
  const limit = asLimit(params.limit);
  const rows = await readQuery(`
    MATCH (s:证型)
    WHERE s.name CONTAINS $syndrome
    MATCH (c:医案)-[:辨证为]->(s)
    WITH DISTINCT c
    ORDER BY coalesce(c.publish_date, '') DESC, c.name
    LIMIT $limit
    CALL {
      WITH c
      OPTIONAL MATCH (c)-[:涉及病名]->(d:病名)
      RETURN collect(DISTINCT d.name)[..20] AS diseases
    }
    CALL {
      WITH c
      OPTIONAL MATCH (c)-[:辨证为]->(s2:证型)
      RETURN collect(DISTINCT s2.name)[..20] AS syndromes
    }
    CALL {
      WITH c
      OPTIONAL MATCH (c)-[:使用方剂]->(f:方剂)
      RETURN collect(DISTINCT f.name)[..20] AS formulas
    }
    CALL {
      WITH c
      OPTIONAL MATCH (c)-[:采用治法]->(method:治法)
      RETURN collect(DISTINCT method.name)[..20] AS treatmentMethods
    }
    RETURN c.id AS caseId,
           c.name AS title,
           c.summary AS summary,
           c.source_url AS sourceUrl,
           c.publish_date AS publishDate,
           diseases,
           syndromes,
           formulas,
           treatmentMethods
  `, { syndrome, limit });
  return { ok: true, query: "searchBySyndrome", params: { syndrome, limit }, data: rows };
}

// 按名医名字检索相关医案，返回关联病名、证型、方剂、治法、名医。
async function searchByDoctor(params = {}) {
  const doctor = requireKeyword("doctor", params.doctor || params.keyword);
  const limit = asLimit(params.limit);
  const rows = await readQuery(`
    MATCH (doc:名医)
    WHERE doc.name CONTAINS $doctor
    MATCH (c:医案)-[:关联名医]->(doc)
    WITH DISTINCT c
    ORDER BY coalesce(c.publish_date, '') DESC, c.name
    LIMIT $limit
    CALL {
      WITH c
      OPTIONAL MATCH (c)-[:涉及病名]->(d:病名)
      RETURN collect(DISTINCT d.name)[..20] AS diseases
    }
    CALL {
      WITH c
      OPTIONAL MATCH (c)-[:辨证为]->(s:证型)
      RETURN collect(DISTINCT s.name)[..20] AS syndromes
    }
    CALL {
      WITH c
      OPTIONAL MATCH (c)-[:使用方剂]->(f:方剂)
      RETURN collect(DISTINCT f.name)[..20] AS formulas
    }
    CALL {
      WITH c
      OPTIONAL MATCH (c)-[:采用治法]->(method:治法)
      RETURN collect(DISTINCT method.name)[..20] AS treatmentMethods
    }
    CALL {
      WITH c
      OPTIONAL MATCH (c)-[:关联名医]->(doc2:名医)
      RETURN collect(DISTINCT doc2.name)[..10] AS doctors
    }
    RETURN c.id AS caseId,
           c.name AS title,
           c.summary AS summary,
           c.source_url AS sourceUrl,
           c.publish_date AS publishDate,
           diseases,
           syndromes,
           formulas,
           treatmentMethods,
           doctors
  `, { doctor, limit });
  return { ok: true, query: "searchByDoctor", params: { doctor, limit }, data: rows };
}

// 按名医节点 id 精确查询相关医案（与 searchByDoctor 的名字模糊匹配互补）。
async function searchByDoctorId(params = {}) {
  const doctorId = requireKeyword("doctorId", params.doctorId || params.id);
  const limit = asLimit(params.limit);
  const rows = await readQuery(`
    MATCH (doc:名医 {id: $doctorId})
    MATCH (c:医案)-[:关联名医]->(doc)
    WITH DISTINCT c
    ORDER BY coalesce(c.publish_date, '') DESC, c.name
    LIMIT $limit
    CALL {
      WITH c
      OPTIONAL MATCH (c)-[:涉及病名]->(d:病名)
      RETURN collect(DISTINCT d.name)[..20] AS diseases
    }
    CALL {
      WITH c
      OPTIONAL MATCH (c)-[:辨证为]->(s:证型)
      RETURN collect(DISTINCT s.name)[..20] AS syndromes
    }
    CALL {
      WITH c
      OPTIONAL MATCH (c)-[:使用方剂]->(f:方剂)
      RETURN collect(DISTINCT f.name)[..20] AS formulas
    }
    CALL {
      WITH c
      OPTIONAL MATCH (c)-[:采用治法]->(method:治法)
      RETURN collect(DISTINCT method.name)[..20] AS treatmentMethods
    }
    CALL {
      WITH c
      OPTIONAL MATCH (c)-[:关联名医]->(doc2:名医)
      RETURN collect(DISTINCT doc2.name)[..10] AS doctors
    }
    RETURN c.id AS caseId,
           c.name AS title,
           c.summary AS summary,
           c.source_url AS sourceUrl,
           c.publish_date AS publishDate,
           diseases,
           syndromes,
           formulas,
           treatmentMethods,
           doctors
  `, { doctorId, limit });
  return { ok: true, query: "searchByDoctorId", params: { doctorId, limit }, data: rows };
}

async function getFormulaDetailsByNames(names) {
  const uniqueNames = [...new Set((names || []).filter(Boolean))].slice(0, 20);
  if (uniqueNames.length === 0) return [];
  const rows = await readQuery(`
    UNWIND $names AS formulaName
    MATCH (f:方剂 {name: formulaName})
    CALL {
      WITH f
      OPTIONAL MATCH (f)-[r:中药组成]->(h:中药名)
      RETURN collect(DISTINCT {name: h.name, dosage: r.weight})[..30] AS herbs
    }
    RETURN f.id AS formulaId,
           f.name AS name,
           herbs
    ORDER BY f.name
  `, { names: uniqueNames });
  return rows.map((row) => ({ ...row, herbs: cleanHerbs(row.herbs) }));
}

async function searchByFormula(params = {}) {
  const formula = requireKeyword("formula", params.formula || params.keyword);
  const limit = asLimit(params.limit);
  const rows = await readQuery(`
    MATCH (f:方剂)
    WHERE f.name CONTAINS $formula
    WITH f,
         CASE
           WHEN f.name = $formula THEN 3
           WHEN f.name STARTS WITH $formula THEN 2
           ELSE 1
         END AS matchScore
    CALL {
      WITH f
      OPTIONAL MATCH (f)-[r:中药组成]->(h:中药名)
      RETURN collect(DISTINCT {name: h.name, dosage: r.weight})[..30] AS herbs
    }
    CALL {
      WITH f
      OPTIONAL MATCH (c:医案)-[:使用方剂]->(f)
      WITH c
      ORDER BY coalesce(c.publish_date, '') DESC, c.name
      RETURN collect(DISTINCT {
        caseId: c.id,
        title: c.name,
        summary: c.summary,
        sourceUrl: c.source_url,
        publishDate: c.publish_date
      })[..$limit] AS cases
    }
    RETURN f.id AS formulaId,
           f.name AS name,
           matchScore,
           herbs,
           cases
    ORDER BY matchScore DESC, size(cases) DESC, f.name
    LIMIT $limit
  `, { formula, limit });
  return {
    ok: true,
    query: "searchByFormula",
    params: { formula, limit },
    data: rows.map((row) => ({ ...row, herbs: cleanHerbs(row.herbs) })),
  };
}

async function searchCases(params = {}) {
  const keyword = requireKeyword("keyword", params.keyword || params.description);
  const limit = asLimit(params.limit);
  const rows = await readQuery(`
    CALL db.index.fulltext.queryNodes('医案全文检索', $keyword)
    YIELD node, score
    WITH node AS c, score
    WHERE c:医案
    ORDER BY score DESC
    LIMIT $limit
    CALL {
      WITH c
      OPTIONAL MATCH (c)-[:涉及病名]->(d:病名)
      RETURN collect(DISTINCT d.name)[..20] AS diseases
    }
    CALL {
      WITH c
      OPTIONAL MATCH (c)-[:辨证为]->(s:证型)
      RETURN collect(DISTINCT s.name)[..20] AS syndromes
    }
    CALL {
      WITH c
      OPTIONAL MATCH (c)-[:使用方剂]->(f:方剂)
      RETURN collect(DISTINCT f.name)[..20] AS formulas
    }
    RETURN c.id AS caseId,
           c.name AS title,
           c.summary AS summary,
           c.source_url AS sourceUrl,
           score,
           diseases,
           syndromes,
           formulas
  `, { keyword, limit });
  return { ok: true, query: "searchCases", params: { keyword, limit }, data: rows };
}

async function recommendFormulas(params = {}) {
  const disease = asText(params.disease);
  const syndrome = asText(params.syndrome);
  const symptom = asText(params.symptom || params.keyword);
  const limit = asLimit(params.limit, 20);
  if (!disease && !syndrome && !symptom) throw new Error("At least one of disease, syndrome, or symptom is required");

  const rows = await readQuery(`
    MATCH (c:医案)
    CALL {
      WITH c
      OPTIONAL MATCH (c)-[:涉及病名]->(d:病名)
      RETURN collect(DISTINCT d.name) AS diseases
    }
    CALL {
      WITH c
      OPTIONAL MATCH (c)-[:辨证为]->(s:证型)
      RETURN collect(DISTINCT s.name) AS syndromes
    }
    CALL {
      WITH c
      OPTIONAL MATCH (c)-[:表现症状]->(sym:症状)
      RETURN collect(DISTINCT sym.name) AS symptoms
    }
    WITH c, diseases, syndromes, symptoms
    WHERE ($disease = '' OR any(item IN diseases WHERE item CONTAINS $disease))
      AND ($syndrome = '' OR any(item IN syndromes WHERE item CONTAINS $syndrome))
      AND ($symptom = '' OR any(item IN symptoms WHERE item CONTAINS $symptom)
        OR c.name CONTAINS $symptom
        OR coalesce(c.summary, '') CONTAINS $symptom
        OR coalesce(c.raw_text, '') CONTAINS $symptom)
    MATCH (c)-[:使用方剂]->(f:方剂)
    OPTIONAL MATCH (f)-[r:中药组成]->(h:中药名)
    WITH f,
         count(DISTINCT c) AS support,
         collect(DISTINCT c.name)[..5] AS evidenceCases,
         collect(DISTINCT {name: h.name, dosage: r.weight})[..30] AS herbs
    RETURN f.id AS formulaId,
           f.name AS formula,
           support,
           evidenceCases,
           herbs
    ORDER BY support DESC, formula
    LIMIT $limit
  `, { disease, syndrome, symptom, limit });
  return {
    ok: true,
    query: "recommendFormulas",
    params: { disease, syndrome, symptom, limit },
    data: rows.map((row) => ({ ...row, herbs: cleanHerbs(row.herbs) })),
  };
}

async function recommendClinicalOptions(params = {}) {
  const terms = normalizeTerms(params);
  const disease = asText(params.disease);
  const syndrome = asText(params.syndrome);
  const formula = asText(params.formula);
  const limit = asLimit(params.limit);
  if (terms.length === 0 && !disease && !syndrome && !formula) {
    throw new Error("At least one of symptoms, description, disease, syndrome, or formula is required");
  }

  const cases = await readQuery(`
    MATCH (c:医案)
    CALL {
      WITH c
      OPTIONAL MATCH (c)-[:涉及病名]->(d:病名)
      RETURN collect(DISTINCT d.name)[..20] AS diseases
    }
    CALL {
      WITH c
      OPTIONAL MATCH (c)-[:辨证为]->(s:证型)
      RETURN collect(DISTINCT s.name)[..20] AS syndromes
    }
    CALL {
      WITH c
      OPTIONAL MATCH (c)-[:表现症状]->(sym:症状)
      RETURN collect(DISTINCT sym.name)[..60] AS symptoms
    }
    CALL {
      WITH c
      OPTIONAL MATCH (c)-[:使用方剂]->(f:方剂)
      RETURN collect(DISTINCT f.name)[..25] AS formulas
    }
    CALL {
      WITH c
      OPTIONAL MATCH (c)-[:采用治法]->(method:治法)
      RETURN collect(DISTINCT method.name)[..25] AS treatmentMethods
    }
    CALL {
      WITH c
      OPTIONAL MATCH (c)-[:关联名医]->(doctor:名医)
      RETURN collect(DISTINCT doctor.name)[..10] AS doctors
    }
    WITH c, diseases, syndromes, symptoms, formulas, treatmentMethods, doctors,
      reduce(score = 0, term IN $terms |
        score
        + CASE WHEN c.name CONTAINS term THEN 10 ELSE 0 END
        + CASE WHEN coalesce(c.summary, '') CONTAINS term THEN 6 ELSE 0 END
        + CASE WHEN coalesce(c.raw_text, '') CONTAINS term THEN 2 ELSE 0 END
        + 4 * size([item IN symptoms WHERE item CONTAINS term])
      )
      + CASE WHEN $disease <> '' AND any(item IN diseases WHERE item CONTAINS $disease) THEN 20 ELSE 0 END
      + CASE WHEN $syndrome <> '' AND any(item IN syndromes WHERE item CONTAINS $syndrome) THEN 20 ELSE 0 END
      + CASE WHEN $formula <> '' AND any(item IN formulas WHERE item CONTAINS $formula) THEN 15 ELSE 0 END
      AS score
    WHERE score > 0
    RETURN c.id AS caseId,
           c.name AS title,
           c.summary AS summary,
           c.source_url AS sourceUrl,
           c.publish_date AS publishDate,
           score,
           diseases,
           syndromes,
           symptoms[..20] AS matchedSymptoms,
           formulas,
           treatmentMethods,
           doctors
    ORDER BY score DESC, coalesce(c.publish_date, '') DESC
    LIMIT $limit
  `, { terms, disease, syndrome, formula, limit });

  const formulaScores = new Map();
  for (const item of cases) {
    for (const name of item.formulas || []) {
      if (!name) continue;
      const current = formulaScores.get(name) || { formula: name, support: 0, score: 0, evidenceCases: [] };
      current.support += 1;
      current.score += item.score || 0;
      if (current.evidenceCases.length < 5) current.evidenceCases.push(item.title);
      formulaScores.set(name, current);
    }
  }
  const recommendedFormulas = [...formulaScores.values()]
    .sort((left, right) => right.support - left.support || right.score - left.score || left.formula.localeCompare(right.formula, "zh-Hans-CN"))
    .slice(0, 10);

  const formulaDetails = await getFormulaDetailsByNames(recommendedFormulas.map((item) => item.formula));
  const formulaDetailByName = new Map(formulaDetails.map((item) => [item.name, item]));
  const formulasWithHerbs = recommendedFormulas.map((item) => ({
    ...item,
    herbs: formulaDetailByName.get(item.formula)?.herbs || [],
  }));

  return {
    ok: true,
    query: "recommendClinicalOptions",
    params: { terms, disease, syndrome, formula, limit },
    data: {
      cases,
      recommendedFormulas: formulasWithHerbs,
    },
  };
}

async function getCaseDetail(params = {}) {
  const caseId = asText(params.caseId || params.id);
  const title = asText(params.title);
  const limit = asLimit(params.limit, 5);
  if (!caseId && !title) throw new Error("caseId or title is required");

  const rows = await readQuery(`
    MATCH (c:医案)
    WHERE ($caseId <> '' AND c.id = $caseId)
       OR ($title <> '' AND c.name CONTAINS $title)
    WITH c
    ORDER BY coalesce(c.publish_date, '') DESC, c.name
    LIMIT $limit
    CALL {
      WITH c
      OPTIONAL MATCH (c)-[:涉及病名]->(d:病名)
      RETURN collect(DISTINCT d.name)[..30] AS diseases
    }
    CALL {
      WITH c
      OPTIONAL MATCH (c)-[:辨证为]->(s:证型)
      RETURN collect(DISTINCT s.name)[..30] AS syndromes
    }
    CALL {
      WITH c
      OPTIONAL MATCH (c)-[:使用方剂]->(f:方剂)
      RETURN collect(DISTINCT f.name)[..30] AS formulas
    }
    CALL {
      WITH c
      OPTIONAL MATCH (c)-[:采用治法]->(m:治法)
      RETURN collect(DISTINCT m.name)[..30] AS treatmentMethods
    }
    CALL {
      WITH c
      OPTIONAL MATCH (c)-[:表现症状]->(sym:症状)
      RETURN collect(DISTINCT sym.name)[..80] AS symptoms
    }
    CALL {
      WITH c
      OPTIONAL MATCH (c)-[:关联名医]->(doc:名医)
      RETURN collect(DISTINCT doc.name)[..10] AS doctors
    }
    RETURN c.id AS caseId,
           c.name AS title,
           c.summary AS summary,
           c.raw_text AS rawText,
           c.source_url AS sourceUrl,
           c.publish_date AS publishDate,
           diseases,
           syndromes,
           symptoms,
           formulas,
           treatmentMethods,
           doctors
  `, { caseId, title, limit });
  return { ok: true, query: "getCaseDetail", params: { caseId, title, limit }, data: rows };
}

const ACTIONS = Object.freeze({
  healthCheck,
  addCase,
  graphSummary,
  searchByDisease,
  searchByDoctor,
  searchByDoctorId,
  searchBySyndrome,
  searchByFormula,
  searchCases,
  recommendFormulas,
  recommendClinicalOptions,
  getCaseDetail,
});

async function runAgentQuery(action, params = {}) {
  const fn = ACTIONS[action];
  if (!fn) {
    return {
      ok: false,
      error: `Unknown action: ${action}`,
      availableActions: Object.keys(ACTIONS),
    };
  }
  try {
    return await fn(params);
  } catch (error) {
    return {
      ok: false,
      query: action,
      error: error.message,
    };
  }
}

module.exports = {
  addCase,
  close,
  getCaseDetail,
  graphSummary,
  healthCheck,
  recommendClinicalOptions,
  recommendFormulas,
  runAgentQuery,
  searchByDisease,
  searchByDoctor,
  searchByDoctorId,
  searchByFormula,
  searchBySyndrome,
  searchCases,
  writeQuery,
};

if (require.main === module) {
  const [action, rawParams = "{}"] = process.argv.slice(2);
  let params;
  try {
    params = JSON.parse(rawParams);
  } catch (error) {
    console.error(JSON.stringify({ ok: false, error: `Invalid JSON params: ${error.message}` }, null, 2));
    process.exitCode = 1;
  }

  if (params) {
    runAgentQuery(action, params)
      .then((result) => {
        console.log(JSON.stringify(result, null, 2));
        if (!result.ok) process.exitCode = 1;
      })
      .catch((error) => {
        console.error(JSON.stringify({ ok: false, error: error.message }, null, 2));
        process.exitCode = 1;
      })
      .finally(close);
  }
}
