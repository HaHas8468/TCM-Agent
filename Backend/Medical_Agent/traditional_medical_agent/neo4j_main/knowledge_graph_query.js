"use strict";

const neo4j = require("neo4j-driver");

const DEFAULT_LIMIT = 10;
const MAX_LIMIT = 50;

let driver;

function getKnowledgeGraphConfig() {
  return {
    uri: process.env.NEO4J_URI,
    username: process.env.NEO4J_USERNAME || process.env.NEO4J_USER,
    password: process.env.NEO4J_PASSWORD,
    database: process.env.NEO4J_DATABASE,
    limit: asLimit(process.env.KG_QUERY_LIMIT, DEFAULT_LIMIT),
  };
}

function assertConfig(config) {
  const missing = ["uri", "username", "password"].filter((key) => !config[key]);
  if (missing.length > 0) {
    throw new Error(`Missing Neo4j connection config: ${missing.join(", ")}`);
  }
}

function createDriver(config = getKnowledgeGraphConfig()) {
  assertConfig(config);
  return neo4j.driver(config.uri, neo4j.auth.basic(config.username, config.password), {
    disableLosslessIntegers: true,
  });
}

function getDriver() {
  if (!driver) driver = createDriver();
  return driver;
}

async function close() {
  if (driver) {
    await driver.close();
    driver = undefined;
  }
}

function asText(value) {
  return typeof value === "string" ? value.trim() : "";
}

function asLimit(value, fallback = DEFAULT_LIMIT) {
  const parsed = Number.parseInt(value, 10);
  if (!Number.isFinite(parsed) || parsed <= 0) return fallback;
  return Math.min(parsed, MAX_LIMIT);
}

function parseQueryTerms(input) {
  const rawValues = Array.isArray(input) ? input : [input];
  const stopWords = new Set([
    "患者",
    "病人",
    "症状",
    "出现",
    "感觉",
    "感到",
    "伴有",
    "并且",
    "而且",
    "治疗",
    "中医",
    "建议",
    "方案",
  ]);
  const terms = rawValues
    .flatMap((value) => String(value || "").split(/[，。；;、,\s/|]+/u))
    .map((term) => term.replace(/^(我|患者|病人|刚到|感到|感觉|出现|伴有|有|是|为|并且|而且|且|还|又)/u, "").trim())
    .filter((term) => term.length >= 2 && !stopWords.has(term));
  return [...new Set(terms)].slice(0, 16);
}

function normalizeTerms(params = {}) {
  const values = [];
  if (Array.isArray(params.terms)) values.push(...params.terms);
  if (Array.isArray(params.symptoms)) values.push(...params.symptoms);
  if (Array.isArray(params.keywords)) values.push(...params.keywords);
  if (params.term) values.push(params.term);
  if (params.symptom) values.push(params.symptom);
  if (params.keyword) values.push(params.keyword);
  if (params.description) values.push(params.description);
  return parseQueryTerms(values);
}

function requireKeyword(name, value) {
  const text = asText(value);
  if (!text) throw new Error(`${name} is required`);
  return text;
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

async function readQuery(cypher, params = {}) {
  const config = getKnowledgeGraphConfig();
  const session = getDriver().session({
    database: config.database,
    defaultAccessMode: neo4j.session.READ,
  });
  try {
    const result = await session.executeRead((tx) => tx.run(cypher, cypherParams(params)));
    return recordsToObjects(result);
  } finally {
    await session.close();
  }
}

function cleanHerbs(herbs) {
  return (herbs || [])
    .filter((item) => item && item.name)
    .filter((item) => !/(嘱|续进|每日|每服|水煎|温服)/u.test(item.name))
    .map((item) => ({
      id: item.id || null,
      name: item.name,
      weight: item.weight || null,
      effects: item.effects || [],
      indications: item.indications || [],
      contraindications: item.contraindications || [],
      sourceUrl: item.sourceUrl || null,
    }));
}

const FORMULA_DETAIL_CYPHER = `
CALL {
  WITH formula
  OPTIONAL MATCH (formula)-[:\`配方\`]->(prescription:\`处方\`)
  OPTIONAL MATCH (prescription)-[composition:\`中药组成\`]->(herb:\`中药名\`)
  OPTIONAL MATCH (herb)-[:\`功效\`]->(herbEffect:\`功效\`)
  OPTIONAL MATCH (herb)-[:\`功能主治\`]->(herbIndication:\`功能主治\`)
  OPTIONAL MATCH (herb)-[:\`禁忌\`]->(herbContraindication:\`禁忌\`)
  WITH prescription, herb, composition,
       collect(DISTINCT herbEffect.name)[..10] AS herbEffects,
       collect(DISTINCT herbIndication.name)[..10] AS herbIndications,
       collect(DISTINCT herbContraindication.name)[..8] AS herbContraindications
  WITH prescription,
       collect(
         CASE
           WHEN herb IS NULL THEN null
           ELSE {
             id: herb.id,
             name: herb.name,
             weight: composition.weight,
             effects: [item IN herbEffects WHERE item IS NOT NULL],
             indications: [item IN herbIndications WHERE item IS NOT NULL],
             contraindications: [item IN herbContraindications WHERE item IS NOT NULL],
             sourceUrl: herb.source_url
           }
         END
       ) AS herbs
  RETURN CASE
    WHEN prescription IS NULL THEN null
    ELSE {
      id: prescription.id,
      name: prescription.name,
      herbs: [item IN herbs WHERE item IS NOT NULL]
    }
  END AS prescription
}
CALL {
  WITH formula
  OPTIONAL MATCH (formula)-[:\`功效\`]->(effect:\`功效\`)
  RETURN [item IN collect(DISTINCT effect.name) WHERE item IS NOT NULL][..30] AS effects
}
CALL {
  WITH formula
  OPTIONAL MATCH (formula)-[:\`功能主治\`]->(indication:\`功能主治\`)
  RETURN [item IN collect(DISTINCT indication.name) WHERE item IS NOT NULL][..50] AS indications
}
CALL {
  WITH formula
  OPTIONAL MATCH (formula)-[:\`治疗\`]->(symptom:\`症状病症\`)
  RETURN [item IN collect(DISTINCT symptom.name) WHERE item IS NOT NULL][..60] AS symptoms
}
CALL {
  WITH formula
  OPTIONAL MATCH (formula)-[:\`用法\`]->(usage:\`用法\`)
  RETURN [item IN collect(DISTINCT usage.name) WHERE item IS NOT NULL][..20] AS usages
}
CALL {
  WITH formula
  OPTIONAL MATCH (formula)-[:\`禁忌\`]->(contraindication:\`禁忌\`)
  RETURN [item IN collect(DISTINCT contraindication.name) WHERE item IS NOT NULL][..20] AS contraindications
}
CALL {
  WITH formula
  OPTIONAL MATCH (formula)-[:\`来源\`]->(source:\`来源\`)
  RETURN [item IN collect(DISTINCT source.name) WHERE item IS NOT NULL][..10] AS sources
}
CALL {
  WITH formula
  OPTIONAL MATCH (formula)-[:\`类别\`]->(category:\`类别\`)
  RETURN [item IN collect(DISTINCT category.name) WHERE item IS NOT NULL][..10] AS categories
}
`;

function formulaReturn(extraFields = "") {
  return `
RETURN {
  id: formula.id,
  name: formula.name,
  sourceUrl: formula.source_url,
  sourceId: formula.source_id,
  pageTitle: formula.page_title,
  rawText: formula.raw_text,
  prescription: prescription,
  herbs: CASE WHEN prescription IS NULL THEN [] ELSE prescription.herbs END,
  effects: effects,
  indications: indications,
  symptoms: symptoms,
  usages: usages,
  contraindications: contraindications,
  sources: sources,
  categories: categories${extraFields}
} AS formula
`;
}

const QUERY_FORMULAS_BY_SYMPTOM = `
WITH [term IN $terms WHERE trim(term) <> ""] AS queryTerms
MATCH (formula:\`方名\`)-[:\`治疗\`]->(matchedSymptom:\`症状病症\`)
WITH formula,
     queryTerms,
     collect(DISTINCT matchedSymptom.name) AS allMatchedSymptoms
WITH formula,
     [symptom IN allMatchedSymptoms WHERE any(term IN queryTerms WHERE symptom CONTAINS term OR term CONTAINS symptom)] AS matchedSymptoms,
     [term IN queryTerms WHERE any(symptom IN allMatchedSymptoms WHERE symptom CONTAINS term OR term CONTAINS symptom)] AS matchedQueryTerms
WHERE size(matchedQueryTerms) > 0
WITH formula,
     matchedSymptoms,
     matchedQueryTerms,
     size(matchedQueryTerms) * 10 + size(matchedSymptoms) AS score
ORDER BY score DESC, size(matchedSymptoms) DESC, formula.name ASC
LIMIT $limit
${FORMULA_DETAIL_CYPHER}
${formulaReturn(", matchedSymptoms: matchedSymptoms, matchedQueryTerms: matchedQueryTerms, score: score")}
`;

async function healthCheck() {
  const config = getKnowledgeGraphConfig();
  await getDriver().verifyConnectivity();
  return { ok: true, query: "healthCheck", data: { connected: true, database: config.database || "default" } };
}

async function graphSummary() {
  const rows = await readQuery(`
    CALL {
      MATCH (n)
      UNWIND labels(n) AS label
      WITH label, count(*) AS count
      RETURN collect({label: label, count: count}) AS labels
    }
    CALL {
      MATCH ()-[r]->()
      WITH type(r) AS type, count(*) AS count
      RETURN collect({type: type, count: count}) AS relationships
    }
    RETURN labels, relationships
  `);
  return { ok: true, query: "graphSummary", data: rows[0] || { labels: [], relationships: [] } };
}

async function searchFormulasBySymptom(params = {}) {
  const terms = normalizeTerms(params);
  if (terms.length === 0) throw new Error("symptom, symptoms, keyword, terms, or description is required");
  const limit = asLimit(params.limit, getKnowledgeGraphConfig().limit);
  const rows = await readQuery(QUERY_FORMULAS_BY_SYMPTOM, { terms, limit });
  return {
    ok: true,
    query: "searchFormulasBySymptom",
    params: { terms, limit },
    data: rows.map((row) => ({ ...row.formula, herbs: cleanHerbs(row.formula.herbs) })),
  };
}

async function searchFormulasByEffect(params = {}) {
  const effect = requireKeyword("effect", params.effect || params.keyword);
  const limit = asLimit(params.limit, getKnowledgeGraphConfig().limit);
  const rows = await readQuery(
    `
    MATCH (formula:\`方名\`)
    OPTIONAL MATCH (formula)-[:\`功效\`]->(formulaEffect:\`功效\`)
    OPTIONAL MATCH (formula)-[:\`配方\`]->(:\`处方\`)-[:\`中药组成\`]->(herb:\`中药名\`)-[:\`功效\`]->(herbEffect:\`功效\`)
    WITH formula,
         collect(DISTINCT formulaEffect.name) AS formulaEffects,
         collect(DISTINCT herbEffect.name) AS herbEffects
    WITH formula,
         [item IN formulaEffects WHERE item CONTAINS $effect OR $effect CONTAINS item] AS matchedFormulaEffects,
         [item IN herbEffects WHERE item CONTAINS $effect OR $effect CONTAINS item] AS matchedHerbEffects
    WHERE size(matchedFormulaEffects) + size(matchedHerbEffects) > 0
    WITH formula, matchedFormulaEffects, matchedHerbEffects,
         size(matchedFormulaEffects) * 20 + size(matchedHerbEffects) * 5 AS score
    ORDER BY score DESC, formula.name ASC
    LIMIT $limit
    ${FORMULA_DETAIL_CYPHER}
    ${formulaReturn(", matchedFormulaEffects: matchedFormulaEffects, matchedHerbEffects: matchedHerbEffects, score: score")}
    `,
    { effect, limit },
  );
  return {
    ok: true,
    query: "searchFormulasByEffect",
    params: { effect, limit },
    data: rows.map((row) => ({ ...row.formula, herbs: cleanHerbs(row.formula.herbs) })),
  };
}

async function searchFormulaByName(params = {}) {
  const formula = requireKeyword("formula", params.formula || params.name || params.keyword);
  const limit = asLimit(params.limit, getKnowledgeGraphConfig().limit);
  const rows = await readQuery(
    `
    MATCH (formula:\`方名\`)
    WHERE formula.name CONTAINS $formula OR $formula CONTAINS formula.name
    WITH formula,
         CASE
           WHEN formula.name = $formula THEN 100
           WHEN formula.name STARTS WITH $formula THEN 60
           ELSE 30
         END AS score
    ORDER BY score DESC, formula.name ASC
    LIMIT $limit
    ${FORMULA_DETAIL_CYPHER}
    ${formulaReturn(", score: score")}
    `,
    { formula, limit },
  );
  return {
    ok: true,
    query: "searchFormulaByName",
    params: { formula, limit },
    data: rows.map((row) => ({ ...row.formula, herbs: cleanHerbs(row.formula.herbs) })),
  };
}

async function getFormulaDetail(params = {}) {
  const id = asText(params.id || params.formulaId);
  const name = asText(params.name || params.formula);
  if (!id && !name) throw new Error("id or name is required");
  const rows = await readQuery(
    `
    MATCH (formula:\`方名\`)
    WHERE ($id <> "" AND formula.id = $id)
       OR ($name <> "" AND formula.name = $name)
       OR ($name <> "" AND formula.name CONTAINS $name)
    WITH formula
    ORDER BY CASE WHEN formula.id = $id OR formula.name = $name THEN 0 ELSE 1 END, formula.name
    LIMIT 1
    ${FORMULA_DETAIL_CYPHER}
    ${formulaReturn("")}
    `,
    { id, name },
  );
  const formula = rows[0]?.formula || null;
  return {
    ok: true,
    query: "getFormulaDetail",
    params: { id, name },
    data: formula ? { ...formula, herbs: cleanHerbs(formula.herbs) } : null,
  };
}

async function searchHerbs(params = {}) {
  const keyword = requireKeyword("keyword", params.keyword || params.herb || params.name || params.effect || params.symptom);
  const limit = asLimit(params.limit, getKnowledgeGraphConfig().limit);
  const includeFormulaOnly = params.includeFormulaOnly === true;
  const rows = await readQuery(
    `
    MATCH (herb:\`中药名\`)
    WHERE $includeFormulaOnly = true
       OR coalesce(herb.source_id, "") STARTS WITH "901020_zhongyao_"
    OPTIONAL MATCH (herb)-[:\`功效\`]->(effect:\`功效\`)
    OPTIONAL MATCH (herb)-[:\`治疗\`]->(symptom:\`症状病症\`)
    OPTIONAL MATCH (herb)-[:\`类别\`]->(category:\`类别\`)
    OPTIONAL MATCH (herb)-[:\`性味\`]->(nature:\`性味\`)
    OPTIONAL MATCH (herb)-[:\`归经\`]->(meridian:\`归经\`)
    WITH herb,
         collect(DISTINCT effect.name) AS effects,
         collect(DISTINCT symptom.name) AS symptoms,
         collect(DISTINCT category.name) AS categories,
         collect(DISTINCT nature.name) AS natures,
         collect(DISTINCT meridian.name) AS meridians
    WITH herb, effects, symptoms, categories, natures, meridians,
         CASE WHEN herb.name CONTAINS $keyword OR $keyword CONTAINS herb.name THEN 80 ELSE 0 END
         + 12 * size([item IN effects WHERE item CONTAINS $keyword OR $keyword CONTAINS item])
         + 10 * size([item IN symptoms WHERE item CONTAINS $keyword OR $keyword CONTAINS item])
         + 8 * size([item IN categories WHERE item CONTAINS $keyword OR $keyword CONTAINS item])
         + 5 * size([item IN natures WHERE item CONTAINS $keyword OR $keyword CONTAINS item])
         + 5 * size([item IN meridians WHERE item CONTAINS $keyword OR $keyword CONTAINS item])
         + CASE WHEN coalesce(herb.raw_text, "") CONTAINS $keyword THEN 2 ELSE 0 END
         AS score
    WHERE score > 0
    ORDER BY score DESC, herb.name ASC
    LIMIT $limit
    CALL {
      WITH herb
      OPTIONAL MATCH (formula:\`方名\`)-[:\`配方\`]->(:\`处方\`)-[:\`中药组成\`]->(herb)
      RETURN collect(DISTINCT {id: formula.id, name: formula.name, sourceUrl: formula.source_url})[..20] AS relatedFormulas
    }
    CALL {
      WITH herb
      OPTIONAL MATCH (herb)-[:\`禁忌\`]->(contraindication:\`禁忌\`)
      RETURN collect(DISTINCT contraindication.name)[..20] AS contraindications
    }
    CALL {
      WITH herb
      OPTIONAL MATCH (herb)-[:\`常用配伍\`]->(paired:\`中药名\`)
      RETURN collect(DISTINCT paired.name)[..20] AS pairings
    }
    RETURN herb.id AS id,
           herb.name AS name,
           herb.source_url AS sourceUrl,
           herb.alias_text AS aliases,
           herb.effect_text AS effectText,
           herb.indication_text AS indicationText,
           herb.usage_text AS usageText,
           herb.contraindication_text AS contraindicationText,
           effects,
           symptoms,
           categories,
           natures,
           meridians,
           contraindications,
           pairings,
           relatedFormulas,
           score
    `,
    { keyword, includeFormulaOnly, limit },
  );
  return { ok: true, query: "searchHerbs", params: { keyword, includeFormulaOnly, limit }, data: rows };
}

async function getHerbDetail(params = {}) {
  const id = asText(params.id || params.herbId);
  const name = asText(params.name || params.herb);
  if (!id && !name) throw new Error("id or name is required");
  const rows = await readQuery(
    `
    MATCH (herb:\`中药名\`)
    WHERE ($id <> "" AND herb.id = $id)
       OR ($name <> "" AND herb.name = $name)
       OR ($name <> "" AND herb.name CONTAINS $name)
    WITH herb
    ORDER BY CASE WHEN herb.id = $id OR herb.name = $name THEN 0 ELSE 1 END, herb.name
    LIMIT 1
    OPTIONAL MATCH (herb)-[:\`功效\`]->(effect:\`功效\`)
    OPTIONAL MATCH (herb)-[:\`治疗\`]->(symptom:\`症状病症\`)
    OPTIONAL MATCH (herb)-[:\`功能主治\`]->(indication:\`功能主治\`)
    OPTIONAL MATCH (herb)-[:\`类别\`]->(category:\`类别\`)
    OPTIONAL MATCH (herb)-[:\`性味\`]->(nature:\`性味\`)
    OPTIONAL MATCH (herb)-[:\`归经\`]->(meridian:\`归经\`)
    OPTIONAL MATCH (herb)-[:\`禁忌\`]->(contraindication:\`禁忌\`)
    OPTIONAL MATCH (herb)-[:\`常用配伍\`]->(paired:\`中药名\`)
    WITH herb,
         collect(DISTINCT effect.name) AS effects,
         collect(DISTINCT symptom.name) AS symptoms,
         collect(DISTINCT indication.name) AS indications,
         collect(DISTINCT category.name) AS categories,
         collect(DISTINCT nature.name) AS natures,
         collect(DISTINCT meridian.name) AS meridians,
         collect(DISTINCT contraindication.name) AS contraindications,
         collect(DISTINCT paired.name) AS pairings
    CALL {
      WITH herb
      OPTIONAL MATCH (formula:\`方名\`)-[:\`配方\`]->(:\`处方\`)-[:\`中药组成\`]->(herb)
      RETURN collect(DISTINCT {id: formula.id, name: formula.name, sourceUrl: formula.source_url})[..50] AS relatedFormulas
    }
    RETURN {
      id: herb.id,
      name: herb.name,
      sourceUrl: herb.source_url,
      aliases: herb.alias_text,
      categoryText: herb.category_text,
      medicinalPartText: herb.medicinal_part_text,
      originText: herb.origin_text,
      natureTasteText: herb.nature_taste_text,
      meridianText: herb.meridian_text,
      effectText: herb.effect_text,
      indicationText: herb.indication_text,
      usageText: herb.usage_text,
      contraindicationText: herb.contraindication_text,
      rawText: herb.raw_text,
      effects: [item IN effects WHERE item IS NOT NULL],
      symptoms: [item IN symptoms WHERE item IS NOT NULL],
      indications: [item IN indications WHERE item IS NOT NULL],
      categories: [item IN categories WHERE item IS NOT NULL],
      natures: [item IN natures WHERE item IS NOT NULL],
      meridians: [item IN meridians WHERE item IS NOT NULL],
      contraindications: [item IN contraindications WHERE item IS NOT NULL],
      pairings: [item IN pairings WHERE item IS NOT NULL],
      relatedFormulas: relatedFormulas
    } AS herb
    `,
    { id, name },
  );
  return { ok: true, query: "getHerbDetail", params: { id, name }, data: rows[0]?.herb || null };
}

async function recommendClinicalOptions(params = {}) {
  const terms = normalizeTerms(params);
  const effect = asText(params.effect);
  const formula = asText(params.formula);
  const herb = asText(params.herb);
  const limit = asLimit(params.limit, getKnowledgeGraphConfig().limit);
  if (terms.length === 0 && !effect && !formula && !herb) {
    throw new Error("At least one of symptoms, description, effect, formula, or herb is required");
  }

  const rows = await readQuery(
    `
    MATCH (formulaNode:\`方名\`)
    OPTIONAL MATCH (formulaNode)-[:\`治疗\`]->(formulaSymptom:\`症状病症\`)
    OPTIONAL MATCH (formulaNode)-[:\`功能主治\`]->(formulaIndication:\`功能主治\`)
    OPTIONAL MATCH (formulaNode)-[:\`功效\`]->(formulaEffect:\`功效\`)
    OPTIONAL MATCH (formulaNode)-[:\`配方\`]->(:\`处方\`)-[:\`中药组成\`]->(formulaHerb:\`中药名\`)
    WITH formulaNode,
         collect(DISTINCT formulaSymptom.name) AS formulaSymptoms,
         collect(DISTINCT formulaIndication.name) AS formulaIndications,
         collect(DISTINCT formulaEffect.name) AS formulaEffects,
         collect(DISTINCT formulaHerb.name) AS formulaHerbs
    WITH formulaNode, formulaSymptoms, formulaIndications, formulaEffects, formulaHerbs,
         reduce(score = 0, term IN $terms |
           score
           + CASE WHEN formulaNode.name CONTAINS term THEN 30 ELSE 0 END
           + 12 * size([item IN formulaSymptoms WHERE item CONTAINS term OR term CONTAINS item])
           + 8 * size([item IN formulaIndications WHERE item CONTAINS term OR term CONTAINS item])
           + 6 * size([item IN formulaEffects WHERE item CONTAINS term OR term CONTAINS item])
         )
         + CASE WHEN $effect <> "" THEN 12 * size([item IN formulaEffects WHERE item CONTAINS $effect OR $effect CONTAINS item]) ELSE 0 END
         + CASE WHEN $formula <> "" AND (formulaNode.name CONTAINS $formula OR $formula CONTAINS formulaNode.name) THEN 60 ELSE 0 END
         + CASE WHEN $herb <> "" THEN 20 * size([item IN formulaHerbs WHERE item CONTAINS $herb OR $herb CONTAINS item]) ELSE 0 END
         AS score,
         [term IN $terms WHERE any(item IN formulaSymptoms WHERE item CONTAINS term OR term CONTAINS item)] AS matchedTerms
    WHERE score > 0
    WITH formulaNode AS formula, score, matchedTerms
    ORDER BY score DESC, formula.name ASC
    LIMIT $limit
    ${FORMULA_DETAIL_CYPHER}
    ${formulaReturn(", matchedQueryTerms: matchedTerms, score: score")}
    `,
    { terms, effect, formula, herb, limit },
  );

  const formulas = rows.map((row) => ({ ...row.formula, herbs: cleanHerbs(row.formula.herbs) }));
  const herbNames = [...new Set(formulas.flatMap((item) => (item.herbs || []).map((herbItem) => herbItem.name)).filter(Boolean))].slice(0, 30);
  const herbs = herbNames.length
    ? (await searchHerbs({ keyword: herbNames.join(" "), limit: Math.min(20, limit * 3) })).data
    : [];

  return {
    ok: true,
    query: "recommendClinicalOptions",
    params: { terms, effect, formula, herb, limit },
    data: {
      formulas,
      relatedHerbs: herbs,
      note: "本接口只做知识图谱召回，不替代执业医师诊疗；禁忌、过敏、孕产妇和基础病需由 agent 继续过滤和说明。",
    },
  };
}

async function queryKnowledgeGraph(symptom) {
  if (!Array.isArray(symptom) && (typeof symptom !== "string" || symptom.trim() === "")) {
    throw new TypeError("symptom must be a non-empty string or a non-empty string array.");
  }
  const result = await searchFormulasBySymptom({ symptoms: Array.isArray(symptom) ? symptom : undefined, description: Array.isArray(symptom) ? undefined : symptom });
  return {
    symptom: Array.isArray(symptom) ? symptom : symptom.trim(),
    queryTerms: result.params.terms,
    count: result.data.length,
    formulas: result.data,
  };
}

const QUERY_SYNDROME_BY_SYMPTOM = `
WITH [term IN $terms WHERE trim(term) <> ""] AS queryTerms
MATCH (syndrome:\`证型\`)
OPTIONAL MATCH (syndrome)-[:\`症状\`]->(syndromeSymptom:\`症状病症\`)
OPTIONAL MATCH (syndrome)-[:\`舌象\`]->(tongue:\`舌象\`)
OPTIONAL MATCH (syndrome)-[:\`脉象\`]->(pulse:\`脉象\`)
OPTIONAL MATCH (syndrome)-[:\`方剂\`]->(formula:\`方名\`)
OPTIONAL MATCH (syndrome)-[:\`治法\`]->(treatment:\`治法\`)
WITH syndrome,
     queryTerms,
     collect(DISTINCT syndromeSymptom.name) AS allSymptoms,
     collect(DISTINCT tongue.name) AS tongues,
     collect(DISTINCT pulse.name) AS pulses,
     collect(DISTINCT {id: formula.id, name: formula.name}) AS formulas,
     collect(DISTINCT treatment.name) AS treatments
WITH syndrome,
     allSymptoms,
     [symptom IN allSymptoms WHERE any(term IN queryTerms WHERE symptom CONTAINS term OR term CONTAINS symptom)] AS matchedSymptoms,
     [term IN queryTerms WHERE any(symptom IN allSymptoms WHERE symptom CONTAINS term OR term CONTAINS symptom)] AS matchedQueryTerms,
     tongues,
     pulses,
     formulas,
     treatments
WHERE size(matchedQueryTerms) > 0
WITH syndrome,
     allSymptoms,
     matchedSymptoms,
     matchedQueryTerms,
     tongues,
     pulses,
     formulas,
     treatments,
     size(matchedQueryTerms) * 10 + size(matchedSymptoms) AS score
ORDER BY score DESC, size(matchedSymptoms) DESC, syndrome.name ASC
LIMIT $limit
RETURN {
  id: syndrome.id,
  name: syndrome.name,
  symptoms: allSymptoms,
  matchedSymptoms: matchedSymptoms,
  tongue: tongues,
  pulse: pulses,
  formulas: formulas,
  treatments: treatments,
  score: score
} AS syndrome
`;

async function searchSyndromesBySymptom(params = {}) {
  const terms = normalizeTerms(params);
  if (terms.length === 0) throw new Error("symptom, symptoms, keyword, terms, or description is required");
  const limit = asLimit(params.limit, getKnowledgeGraphConfig().limit);
  const rows = await readQuery(QUERY_SYNDROME_BY_SYMPTOM, { terms, limit });
  return {
    ok: true,
    query: "searchSyndromesBySymptom",
    params: { terms, limit },
    data: rows.map((row) => row.syndrome),
  };
}

const ACTIONS = Object.freeze({
  healthCheck,
  graphSummary,
  searchFormulasBySymptom,
  searchFormulasByEffect,
  searchFormulaByName,
  getFormulaDetail,
  searchHerbs,
  getHerbDetail,
  recommendClinicalOptions,
  searchSyndromesBySymptom,
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
  ACTIONS,
  QUERY_FORMULAS_BY_SYMPTOM,
  QUERY_SYNDROME_BY_SYMPTOM,
  close,
  createDriver,
  getFormulaDetail,
  getHerbDetail,
  getKnowledgeGraphConfig,
  graphSummary,
  healthCheck,
  parseQueryTerms,
  queryKnowledgeGraph,
  recommendClinicalOptions,
  runAgentQuery,
  searchFormulaByName,
  searchFormulasByEffect,
  searchFormulasBySymptom,
  searchHerbs,
  searchSyndromesBySymptom,
};

if (require.main === module) {
  const [firstArg, rawParams] = process.argv.slice(2);
  const action = ACTIONS[firstArg] ? firstArg : "searchFormulasBySymptom";
  const paramsText = ACTIONS[firstArg] ? rawParams || "{}" : JSON.stringify({ description: process.argv.slice(2).join(" ").trim() });

  let params;
  try {
    params = JSON.parse(paramsText);
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
