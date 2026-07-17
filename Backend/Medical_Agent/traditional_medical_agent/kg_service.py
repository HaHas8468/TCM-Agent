import os
import re
import json
import logging
import threading

import httpx
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

KG_SERVICE_BASE_URL = os.getenv("KG_SERVICE_BASE_URL", "http://kg:3000").rstrip("/")
KG_SERVICE_TIMEOUT_SECONDS = max(1.0, float(os.getenv("KG_SERVICE_TIMEOUT_SECONDS", "20")))
KG_MAX_CONCURRENCY = max(1, int(os.getenv("KG_MAX_CONCURRENCY", "2")))
_kg_capacity = threading.BoundedSemaphore(KG_MAX_CONCURRENCY)
_kg_client = None

_llm_herb_cleaner = None


def _get_kg_client():
    global _kg_client
    if _kg_client is None:
        _kg_client = httpx.Client(base_url=KG_SERVICE_BASE_URL)
    return _kg_client


def _query_kg_service(path: str, action: str, params: dict, timeout: float) -> dict:
    """调用常驻图谱服务；错误细节只保留在服务端日志中。"""
    acquire_timeout = min(timeout, KG_SERVICE_TIMEOUT_SECONDS)
    if not _kg_capacity.acquire(timeout=acquire_timeout):
        logger.warning("kg_request_rejected reason=capacity path=%s action=%s", path, action)
        return {"ok": False, "error": "知识图谱服务繁忙"}
    try:
        response = _get_kg_client().post(
            path,
            json={"action": action, "params": params},
            timeout=acquire_timeout,
        )
        if response.status_code != 200:
            logger.warning("kg_request_failed path=%s action=%s status=%s", path, action, response.status_code)
            return {"ok": False, "error": "知识图谱服务暂不可用"}
        payload = response.json()
        if not isinstance(payload, dict) or not payload.get("ok"):
            logger.warning("kg_request_failed path=%s action=%s reason=invalid_result", path, action)
            return {"ok": False, "error": "知识图谱服务暂不可用"}
        return payload
    except (httpx.HTTPError, ValueError) as exc:
        logger.warning("kg_request_failed path=%s action=%s error=%s", path, action, type(exc).__name__)
        return {"ok": False, "error": "知识图谱服务暂不可用"}
    finally:
        _kg_capacity.release()

def _get_herb_cleaner():
    global _llm_herb_cleaner
    if _llm_herb_cleaner is None:
        from langchain_community.chat_models.tongyi import ChatTongyi
        from langchain_core.messages import HumanMessage
        model = os.getenv("LLM_MODEL_32B", "qwen-max")
        _llm_herb_cleaner = ChatTongyi(model=model, temperature=0)
    return _llm_herb_cleaner

def _clean_herb_name_batch(raw_names):
    if not raw_names:
        return []

    valid = [n for n in raw_names if n and isinstance(n, str) and any('\u4e00' <= c <= '\u9fff' for c in n)]
    if not valid:
        return []

    unique_names = list(dict.fromkeys(valid))

    try:
        cleaner = _get_herb_cleaner()
        names_str = "\n".join([f"{i+1}. {name}" for i, name in enumerate(unique_names)])
        prompt = f"""你是中药专家，任务是将原始中药名称（含剂量、加工说明等杂质）规范化为标准中药名。

规则：
1. 去掉所有剂量信息（如"三两"、"70个"、"120g"等数字和单位）
2. 去掉所有加工说明（如"去心"、"去节"、"去皮"、"酒洗"、"炙"、"炒"、"切"、"擘"等）
3. 保留药材的标准名（如"麻黄"、"桂枝"、"杏仁"、"炙甘草"等）
4. 对于"姜"返回"生姜"；"夏"返回"半夏"
5. 对于"生白芍"返回"生白芍"；"白芍"返回"白芍"（根据原名）
6. 如果原名本身就是标准名（如"川芎"、"当归"），直接返回
7. 如果原名完全无法识别（如只有括号"("），返回空字符串
8. 返回的数量和顺序必须与输入完全一致

输入：
{names_str}

请严格按以上规则，只输出规范化后的中药名，每行一个，顺序对应输入："""

        from langchain_core.messages import HumanMessage
        response = cleaner.invoke([HumanMessage(content=prompt)])
        result = response.content.strip()

        cleaned = [line.strip() for line in result.split("\n") if line.strip()]
        cleaned = [re.sub(r"^\d+[\.、]\s*", "", c) for c in cleaned]

        if len(cleaned) != len(unique_names):
            return ["" for _ in unique_names]

        return cleaned
    except Exception as exc:
        logger.warning("herb_name_cleanup_failed error=%s", type(exc).__name__)
        return ["" for _ in unique_names]

def _clean_herb_name(name):
    return name

def call_kg_service(input_text):
    if not input_text:
        return {"error": "输入为空"}
    result = _query_kg_service(
        "/main/query",
        "searchFormulasBySymptom",
        {"description": input_text},
        KG_SERVICE_TIMEOUT_SECONDS,
    )
    return result if result.get("ok") else {"error": result.get("error", "知识图谱服务暂不可用")}


def call_kg_action(action: str, params: dict = None, timeout: int = 60):
    """通过 Node.js API 入口调用 neo4j_main 知识图谱服务。

    Args:
        action: 接口名（如 searchHerbs、getHerbDetail、getFormulaDetail 等）
        params: 接口参数字典

    Returns:
        dict: {ok, query, params, data} 或 {ok: False, error}
    """
    if not action:
        return {"ok": False, "error": "action is required"}

    return _query_kg_service("/main/query", action, params or {}, timeout)


def search_herbs(keyword: str, limit: int = 5, include_formula_only: bool = False):
    """按中药名/功效/主治/性味/归经等检索中药"""
    if not keyword:
        return {"herbs": [], "success": False, "message": "关键词为空"}

    result = call_kg_action("searchHerbs", {
        "keyword": keyword,
        "limit": limit,
        "includeFormulaOnly": include_formula_only,
    })

    if not result.get("ok"):
        return {
            "herbs": [],
            "success": False,
            "message": result.get("error", "查询失败"),
        }

    return {
        "herbs": result.get("data", []),
        "success": True,
        "message": "查询成功",
    }


def get_herb_detail(name: str = None, herb_id: str = None):
    """获取单味中药详情（功效/禁忌/性味/归经/配伍/相关方剂）"""
    if not name and not herb_id:
        return {"herb": None, "success": False, "message": "name 或 id 至少传一个"}

    params = {}
    if herb_id:
        params["id"] = herb_id
    else:
        params["name"] = name

    result = call_kg_action("getHerbDetail", params)

    if not result.get("ok"):
        return {
            "herb": None,
            "success": False,
            "message": result.get("error", "查询失败"),
        }

    data = result.get("data", [])
    if isinstance(data, list) and data:
        return {"herb": data[0], "success": True, "message": "查询成功"}
    elif isinstance(data, dict):
        return {"herb": data, "success": True, "message": "查询成功"}

    return {"herb": None, "success": False, "message": "未找到该中药"}


def search_formula_by_name(formula: str, limit: int = 5):
    """按方剂名检索方剂详情"""
    if not formula:
        return {"formulas": [], "success": False, "message": "方剂名为空"}

    result = call_kg_action("searchFormulaByName", {
        "formula": formula,
        "limit": limit,
    })

    if not result.get("ok"):
        return {
            "formulas": [],
            "success": False,
            "message": result.get("error", "查询失败"),
        }

    return {
        "formulas": result.get("data", []),
        "success": True,
        "message": "查询成功",
    }


def get_formula_detail(name: str = None, formula_id: str = None):
    """获取单个方剂详情（组成/功效/禁忌/原文）"""
    if not name and not formula_id:
        return {"formula": None, "success": False, "message": "name 或 id 至少传一个"}

    params = {}
    if formula_id:
        params["id"] = formula_id
    else:
        params["name"] = name

    result = call_kg_action("getFormulaDetail", params)

    if not result.get("ok"):
        return {
            "formula": None,
            "success": False,
            "message": result.get("error", "查询失败"),
        }

    data = result.get("data", [])
    if isinstance(data, list) and data:
        return {"formula": data[0], "success": True, "message": "查询成功"}
    elif isinstance(data, dict):
        return {"formula": data, "success": True, "message": "查询成功"}

    return {"formula": None, "success": False, "message": "未找到该方剂"}


def search_by_doctor(doctor: str = None, doctor_id: str = None, limit: int = 10):
    """按名医名字或ID检索相关医案，与 neo4j_case README.md 中 searchByDoctor/searchByDoctorId 一致"""
    if not doctor and not doctor_id:
        return {"cases": [], "success": False, "message": "doctor 或 doctor_id 至少传一个"}

    if doctor_id:
        result = call_case_kg_service("searchByDoctorId", {
            "doctorId": doctor_id,
            "limit": limit,
        })
    else:
        result = call_case_kg_service("searchByDoctor", {
            "doctor": doctor,
            "limit": limit,
        })

    if not result.get("ok"):
        return {
            "cases": [],
            "success": False,
            "message": result.get("error", "查询失败"),
        }

    return {
        "cases": result.get("data", []),
        "success": True,
        "message": "查询成功",
        "raw": result,
    }


def search_formulas_by_effect(effect: str, limit: int = 5):
    """按功效检索方剂"""
    if not effect:
        return {"formulas": [], "success": False, "message": "功效关键词为空"}

    result = call_kg_action("searchFormulasByEffect", {
        "effect": effect,
        "limit": limit,
    })

    if not result.get("ok"):
        return {
            "formulas": [],
            "success": False,
            "message": result.get("error", "查询失败"),
        }

    return {
        "formulas": result.get("data", []),
        "success": True,
        "message": "查询成功",
    }


def recommend_clinical_options(description=None, symptoms=None, effect=None, formula=None, herb=None, limit=5):
    """综合推荐接口：按症状/功效/方剂/中药召回临床候选方案"""
    params = {"limit": limit}
    if description:
        params["description"] = description
    if symptoms:
        params["symptoms"] = symptoms if isinstance(symptoms, list) else [symptoms]
    if effect:
        params["effect"] = effect
    if formula:
        params["formula"] = formula
    if herb:
        params["herb"] = herb

    if not any([description, symptoms, effect, formula, herb]):
        return {
            "formulas": [],
            "related_herbs": [],
            "success": False,
            "message": "至少需要传入一个查询条件"
        }

    result = call_kg_action("recommendClinicalOptions", params)

    if not result.get("ok"):
        return {
            "formulas": [],
            "related_herbs": [],
            "success": False,
            "message": result.get("error", "查询失败"),
        }

    data = result.get("data", {})
    if isinstance(data, dict):
        return {
            "formulas": data.get("formulas", []),
            "related_herbs": data.get("relatedHerbs", []),
            "note": data.get("note", ""),
            "success": True,
            "message": "查询成功"
        }
    elif isinstance(data, list):
        return {
            "formulas": data,
            "related_herbs": [],
            "success": True,
            "message": "查询成功"
        }

    return {
        "formulas": [],
        "related_herbs": [],
        "success": False,
        "message": "返回数据格式异常"
    }

def query_kg_for_symptoms(symptoms, allergy_herbs=None):
    if not symptoms:
        return {
            "symptoms": [],
            "zheng": [],
            "prescription": [],
            "herbs": [],
            "medical_cases": [],
            "case_summaries": [],
            "departments": [],
            "similar_herbs": [],
            "similar_cases": [],
            "warnings": [],
            "success": False,
            "message": "症状列表为空"
        }

    symptoms = symptoms[:5]

    all_formulas = []
    all_zheng = []
    all_warnings = []
    raw_results = []
    all_raw_herb_names = []
    herb_name_to_index = {}

    def query_single_symptom(symptom):
        try:
            kg_result = call_kg_service(symptom)
            return {"symptom": symptom, "result": kg_result}
        except Exception as exc:
            logger.warning("kg_symptom_query_failed error=%s", type(exc).__name__)
            return {"symptom": symptom, "result": {"error": "知识图谱服务暂不可用"}}

    # 图谱服务自身有全局并发上限；这里顺序调用，避免每个请求临时创建线程池。
    for symptom in symptoms:
        try:
            result = query_single_symptom(symptom)
            raw_results.append(result)
            symptom = result["symptom"]
            kg_result = result["result"]

            if "error" in kg_result:
                all_warnings.append("症状查询失败：知识图谱服务暂不可用")
                continue

            formulas = kg_result.get("data", [])
            for f in formulas:
                formula_name = f.get("name", "")
                if not formula_name:
                    continue

                has_allergy_collision = False
                if allergy_herbs:
                    herbs_in_formula = []
                    prescription = f.get("prescription") or {}
                    for herb in prescription.get("herbs", []):
                        herbs_in_formula.append(herb.get("name", ""))

                    for herb_name in herbs_in_formula:
                        for allergy_herb in allergy_herbs:
                            if allergy_herb in herb_name:
                                has_allergy_collision = True
                                break
                        if has_allergy_collision:
                            break

                indications = f.get("indications", []) or []
                for indication in indications:
                    for symptom_text in symptoms:
                        if symptom_text in indication and indication not in all_zheng:
                            all_zheng.append(indication)

                herbs_raw = []
                for h in (f.get("prescription") or {}).get("herbs", []):
                    raw_name = h.get("name", "")
                    if raw_name and any('\u4e00' <= c <= '\u9fff' for c in raw_name):
                        herbs_raw.append({"raw_name": raw_name, "weight": h.get("weight", "")})
                        if raw_name not in herb_name_to_index:
                            herb_name_to_index[raw_name] = len(all_raw_herb_names)
                            all_raw_herb_names.append(raw_name)

                formula_entry = {
                    "name": formula_name,
                    "matched_symptoms": f.get("matchedSymptoms", []),
                    "_herbs_raw": herbs_raw,
                    "effects": f.get("effects", []),
                    "indications": indications,
                    "usages": f.get("usages", []),
                    "contraindications": f.get("contraindications", []),
                    "sources": f.get("sources", []),
                    "categories": f.get("categories", []),
                    "source_url": f.get("sourceUrl", ""),
                    "allergy_collision": has_allergy_collision,
                }
                all_formulas.append(formula_entry)
        except Exception as exc:
            logger.warning("kg_symptom_result_processing_failed error=%s", type(exc).__name__)
            all_warnings.append("症状查询结果处理失败")

    all_indications = []
    for f in all_formulas:
        indications = f.get("indications", [])
        all_indications.extend(indications)

    if all_indications:
        from langchain_community.chat_models.tongyi import ChatTongyi
        from langchain_core.messages import HumanMessage

        model = os.getenv("LLM_MODEL_32B", "qwen-max")
        llm = ChatTongyi(model=model, temperature=0)

        prompt = f"""你是一位专业的中医师，擅长从中医方剂的主治描述中提取标准证型名称。

        用户症状：{', '.join(symptoms)}

        方剂主治描述列表：
        {chr(10).join([f"{i+1}. {ind}" for i, ind in enumerate(all_indications[:50])])}

        请从上述主治描述中，识别与用户症状最匹配的标准中医证型名称。

        要求：
        1. 只提取一个最匹配的标准证型名称（如：外感风寒表实证、风寒表实证、太阳伤寒证等）
        2. 直接输出证型名称，不要任何解释或额外内容
        3. 证型名称长度在3-12个汉字之间

        示例输出：外感风寒表实证"""

        try:
            response = llm.invoke([HumanMessage(content=prompt)])
            syndrome_text = response.content.strip()
            if syndrome_text:
                all_zheng = [syndrome_text]
                logger.info("kg_syndrome_extracted count=%s", len(all_zheng))
        except Exception as exc:
            logger.warning("kg_syndrome_extraction_failed error=%s", type(exc).__name__)
            syndrome_pattern = re.compile(r'([\u4e00-\u9fff]{3,12}证)')
            for ind in all_indications:
                matches = syndrome_pattern.findall(ind)
                for match in matches:
                    if match not in all_zheng:
                        all_zheng.append(match)

    all_symptoms_str = "、".join(symptoms)
    combined_result = call_kg_service(all_symptoms_str)
    if "error" not in combined_result:
        combined_formulas = combined_result.get("data") or combined_result.get("formulas", [])
        logger.info("kg_combined_query_completed formula_count=%s", len(combined_formulas))
        for f in combined_formulas:
            formula_name = f.get("name", "")
            if formula_name and formula_name not in [existing_f["name"] for existing_f in all_formulas]:
                has_allergy_collision = False
                if allergy_herbs:
                    herbs_in_formula = []
                    prescription = f.get("prescription") or {}
                    for herb in prescription.get("herbs", []):
                        herbs_in_formula.append(herb.get("name", ""))
                    for herb_name in herbs_in_formula:
                        for allergy_herb in allergy_herbs:
                            if allergy_herb in herb_name:
                                has_allergy_collision = True
                                break
                        if has_allergy_collision:
                            break

                herbs_raw = []
                for h in (f.get("prescription") or {}).get("herbs", []):
                    raw_name = h.get("name", "")
                    if raw_name and any('\u4e00' <= c <= '\u9fff' for c in raw_name):
                        herbs_raw.append({"raw_name": raw_name, "weight": h.get("weight", "")})
                        if raw_name not in herb_name_to_index:
                            herb_name_to_index[raw_name] = len(all_raw_herb_names)
                            all_raw_herb_names.append(raw_name)

                formula_entry = {
                    "name": formula_name,
                    "matched_symptoms": f.get("matchedSymptoms", []),
                    "_herbs_raw": herbs_raw,
                    "effects": f.get("effects", []),
                    "indications": f.get("indications", []),
                    "usages": f.get("usages", []),
                    "contraindications": f.get("contraindications", []),
                    "sources": f.get("sources", []),
                    "categories": f.get("categories", []),
                    "source_url": f.get("sourceUrl", ""),
                    "allergy_collision": has_allergy_collision,
                }
                all_formulas.append(formula_entry)

                indications = f.get("indications", [])
                for indication in indications:
                    if any(kw in indication for kw in syndrome_keywords):
                        if indication not in all_zheng:
                            all_zheng.append(indication)

    if all_raw_herb_names:
        try:
            cleaned_names = _clean_herb_name_batch(all_raw_herb_names)
        except Exception as exc:
            logger.warning("herb_name_cleanup_fallback error=%s", type(exc).__name__)
            cleaned_names = all_raw_herb_names

        cleaned_map = {}
        for i, raw_name in enumerate(all_raw_herb_names):
            cleaned = cleaned_names[i] if i < len(cleaned_names) else ""
            if not cleaned:
                cleaned = re.sub(r'^\d+[\u4e00-\u9fff]*\s*', '', raw_name).strip()
            cleaned_map[raw_name] = cleaned

        for f in all_formulas:
            f["herbs"] = []
            for h in f.pop("_herbs_raw", []):
                cleaned = cleaned_map.get(h["raw_name"], "")
                if cleaned:
                    f["herbs"].append({
                        "name": cleaned,
                        "weight": h["weight"],
                    })
    else:
        for f in all_formulas:
            f["herbs"] = []

    seen = set()
    unique_formulas = []
    for f in all_formulas:
        if f["name"] not in seen:
            seen.add(f["name"])
            unique_formulas.append(f)
    all_formulas = unique_formulas

    safe_formulas = [f for f in all_formulas if not f["allergy_collision"]]
    unsafe_formulas = [f for f in all_formulas if f["allergy_collision"]]

    symptom_set = set(symptoms)
    safe_formulas.sort(key=lambda f: -sum(1 for s in symptom_set if any(s in ind for ind in f.get("indications", []))))

    final_prescription = []
    for f in safe_formulas[:5]:
        final_prescription.append({
            "prescription": f["name"],
            "ingredients": [h["name"] for h in f["herbs"]],
            "effects": f["effects"],
            "indications": f["indications"],
            "usages": f["usages"],
            "contraindications": f["contraindications"],
            "sources": f["sources"],
            "categories": f["categories"],
        })

    all_herbs_list = []
    for f in safe_formulas:
        for h in f["herbs"]:
            all_herbs_list.append(h["name"])
    seen_h = set()
    unique_herbs_list = []
    for h in all_herbs_list:
        if h and h not in seen_h:
            seen_h.add(h)
            unique_herbs_list.append(h)

    all_zheng.sort(key=lambda z: (0 if "证" in z else 1, -len(z)))

    result = {
        "symptoms": symptoms,
        "zheng": [{"syndrome": z, "treatment_principle": "", "description": ""} for z in all_zheng[:5]],
        "prescription": final_prescription,
        "herbs": [{"name": h, "effect": "", "taste": "", "channel": ""} for h in unique_herbs_list[:20]],
        "medical_cases": [],
        "case_summaries": [],
        "departments": [],
        "similar_herbs": [],
        "similar_cases": [],
        "contraindicated_formulas": [
            {"name": f["name"], "reason": f"方剂组成含患者过敏药材"}
            for f in unsafe_formulas[:5]
        ],
        "warnings": all_warnings + [
            f"知识图谱包含方剂{len(all_formulas)}条，其中可用{len(safe_formulas)}条，过敏排除{len(unsafe_formulas)}条"
        ],
        "success": True,
        "message": "查询成功",
        "raw": {"symptom": ",".join(symptoms), "formula_count": len(all_formulas)}
    }

    return result

_custom_query_extractor = None

def _get_custom_query_extractor():
    global _custom_query_extractor
    if _custom_query_extractor is None:
        from langchain_community.chat_models.tongyi import ChatTongyi
        from langchain_core.messages import HumanMessage
        model = os.getenv("LLM_MODEL_32B", "qwen-max")
        _custom_query_extractor = ChatTongyi(model=model, temperature=0)
    return _custom_query_extractor


def _extract_query_target(query_text: str) -> dict:
    """用 LLM 提取用户的查询目标（药名/方剂名/证型/症状等）"""
    if not query_text:
        return {"raw": query_text, "keywords": [query_text] if query_text else [], "query_type": "unknown"}

    try:
        extractor = _get_custom_query_extractor()
        prompt = f"""你是中医查询意图分析器。从用户输入中提取关键查询词。

用户输入："{query_text}"

请输出：
- keywords: 核心查询词（药名/方剂名/症状/证型），数组形式，例如["麻黄"]或["川芎茶调散"]
- query_type: 药名查询(herb) / 方剂查询(formula) / 症状查询(symptom) / 证型查询(syndrome) / 未知(unknown)

只输出严格的 JSON："""

        from langchain_core.messages import HumanMessage
        response = extractor.invoke([HumanMessage(content=prompt)])
        result_text = response.content.strip()

        import re
        json_match = re.search(r'\{[^{}]*\}', result_text, re.DOTALL)
        if json_match:
            import json
            data = json.loads(json_match.group())
            return {
                "raw": query_text,
                "keywords": data.get("keywords", [query_text]),
                "query_type": data.get("query_type", "unknown")
            }
    except Exception as exc:
        logger.warning("kg_query_intent_extraction_failed error=%s", type(exc).__name__)

    return {"raw": query_text, "keywords": [query_text], "query_type": "unknown"}


def custom_query_kg(query_text):
    if not query_text:
        return {
            "query": query_text,
            "results": [],
            "success": False,
            "message": "查询内容为空"
        }

    intent_info = _extract_query_target(query_text)
    keywords = intent_info.get("keywords", [query_text])
    query_type = intent_info.get("query_type", "unknown")

    query_input = " ".join(keywords) if isinstance(keywords, list) else str(keywords)

    kg_result = call_kg_service(query_input)

    if "error" in kg_result:
        return {
            "query": query_text,
            "results": [],
            "success": False,
            "message": kg_result["error"],
            "intent": intent_info
        }

    results = []

    if kg_result.get("formulas"):
        for f in kg_result["formulas"]:
            effects = "、".join(f.get("effects", [])) if isinstance(f.get("effects"), list) else f.get("effects", "")
            indications = "、".join(f.get("indications", [])) if isinstance(f.get("indications"), list) else f.get("indications", "")
            desc = f.get("name", "")
            if effects:
                desc += f" - 功效: {effects}"
            if indications:
                desc += f" - 主治: {indications}"
            results.append({
                "labels": f.get("categories", []),
                "name": f.get("name", ""),
                "description": desc
            })

    if not results:
        for k in ["matchedSymptoms", "matchedQueryTerms", "queryTerms"]:
            for item in kg_result.get(k, []) or []:
                results.append({
                    "labels": ["相关实体"],
                    "name": str(item),
                    "description": ""
                })

    return {
        "query": query_text,
        "results": results[:10],
        "success": True,
        "message": "查询成功",
        "intent": intent_info,
        "raw": kg_result
    }

def call_case_kg_service(action: str, params: dict = None, timeout: int = 60):
    """调用 neo4j_case（医案知识图谱）服务"""
    if not action:
        return {"ok": False, "error": "action is required"}

    return _query_kg_service("/case/query", action, params or {}, timeout)


def search_medical_cases(query: str, query_type: str = "auto", limit: int = 5):
    """检索医案，支持按症状/方剂/证型/病名检索

    Args:
        query: 查询关键词
        query_type: auto/symptom/formula/syndrome/disease/keyword
        limit: 返回条数
    """
    if not query:
        return {
            "query": query,
            "query_type": query_type,
            "cases": [],
            "recommended_formulas": [],
            "success": False,
            "message": "查询关键词为空"
        }

    if query_type == "auto":
        query_type = _detect_case_query_type(query)

    action_map = {
        "symptom": ("searchCases", {"keyword": query, "limit": limit}),
        "keyword": ("searchCases", {"keyword": query, "limit": limit}),
        "formula": ("searchByFormula", {"formula": query, "limit": limit}),
        "syndrome": ("searchBySyndrome", {"syndrome": query, "limit": limit}),
        "disease": ("searchByDisease", {"disease": query, "limit": limit}),
    }

    action, params = action_map.get(query_type, action_map["keyword"])
    kg_result = call_case_kg_service(action, params)

    if not kg_result.get("ok"):
        return {
            "query": query,
            "query_type": query_type,
            "cases": [],
            "recommended_formulas": [],
            "success": False,
            "message": kg_result.get("error", "查询失败")
        }

    data = kg_result.get("data", [])
    return {
        "query": query,
        "query_type": query_type,
        "cases": data,
        "recommended_formulas": [],
        "success": True,
        "message": "查询成功",
        "raw": kg_result
    }


def search_medical_cases_by_clinical_options(symptoms=None, syndrome=None, formula=None, disease=None, description=None, limit: int = 5):
    """综合推荐接口：根据症状/证型/方剂/病名查询相似医案"""
    params = {"limit": limit}
    if symptoms:
        params["symptoms"] = symptoms if isinstance(symptoms, list) else [symptoms]
    if syndrome:
        params["syndrome"] = syndrome
    if formula:
        params["formula"] = formula
    if disease:
        params["disease"] = disease
    if description:
        params["description"] = description

    if not any([symptoms, syndrome, formula, disease, description]):
        return {
            "cases": [],
            "recommended_formulas": [],
            "success": False,
            "message": "至少需要传入一个查询条件"
        }

    kg_result = call_case_kg_service("recommendClinicalOptions", params)

    if not kg_result.get("ok"):
        return {
            "cases": [],
            "recommended_formulas": [],
            "success": False,
            "message": kg_result.get("error", "查询失败")
        }

    data = kg_result.get("data", {})
    if isinstance(data, dict):
        cases = data.get("cases", [])
        recommended_formulas = data.get("recommendedFormulas", [])
    elif isinstance(data, list):
        cases = data
        recommended_formulas = []
    else:
        cases = []
        recommended_formulas = []

    return {
        "cases": cases,
        "recommended_formulas": recommended_formulas,
        "success": True,
        "message": "查询成功",
        "raw": kg_result
    }


def get_medical_case_detail(case_id=None, title=None, limit: int = 5):
    """获取医案详情"""
    params = {"limit": limit}
    if case_id:
        params["caseId"] = case_id
    if title:
        params["title"] = title

    if not case_id and not title:
        return {"success": False, "message": "caseId 或 title 至少传一个"}

    kg_result = call_case_kg_service("getCaseDetail", params)

    if not kg_result.get("ok"):
        return {"success": False, "message": kg_result.get("error", "查询失败")}

    return {
        "cases": kg_result.get("data", []),
        "success": True,
        "message": "查询成功"
    }


def add_case(title: str, summary: str = None, raw_text: str = None, source_url: str = None,
             publish_date: str = None, author: str = None, channel: str = None,
             diseases=None, syndromes=None, symptoms=None, formulas=None,
             treatment_methods=None, doctors=None):
    """新增单个医案，并自动建立与病名、证型、症状、方剂、治法、名医、栏目的关联关系

    Args:
        title: 医案标题（必填）
        summary: 医案摘要
        raw_text: 医案原文
        source_url: 来源网页链接
        publish_date: 发布日期，如 "2026-07-12"
        author: 作者；不传默认 "前端录入"
        channel: 所属栏目
        diseases: 关联病名，支持字符串 / 字符串列表 / dict 列表 [{name, id}]
        syndromes: 关联证型，同上
        symptoms: 关联症状，同上
        formulas: 关联方剂，同上
        treatment_methods: 关联治法，同上
        doctors: 关联名医，同上；dict 形式可传 id 指定节点 id

    Returns:
        dict: {caseId, sourceId, linked, success, message} 或 {success: False, message}
    """
    if not title:
        return {"success": False, "message": "title is required"}

    params = {
        "title": title,
        "summary": summary or "",
        "rawText": raw_text or "",
        "sourceUrl": source_url or "",
        "publishDate": publish_date or "",
        "author": author or "",
        "channel": channel or "",
    }

    if diseases:
        params["diseases"] = diseases
    if syndromes:
        params["syndromes"] = syndromes
    if symptoms:
        params["symptoms"] = symptoms
    if formulas:
        params["formulas"] = formulas
    if treatment_methods:
        params["treatmentMethods"] = treatment_methods
    if doctors:
        params["doctors"] = doctors

    kg_result = call_case_kg_service("addCase", params)

    if not kg_result.get("ok"):
        return {"success": False, "message": kg_result.get("error", "写入失败")}

    return {
        "caseId": kg_result.get("caseId"),
        "sourceId": kg_result.get("sourceId"),
        "linked": kg_result.get("linked", {}),
        "success": True,
        "message": "写入成功"
    }


def _detect_case_query_type(query: str) -> str:
    """启发式判断查询类型（auto 模式下使用）"""
    text = (query or "").strip()
    if not text:
        return "keyword"

    if re.search(r"(汤|散|丸|膏|丹|饮|方|剂)$", text):
        return "formula"

    disease_kw = ["炎", "癌", "瘤", "病", "症", "综合征"]
    if any(kw in text for kw in disease_kw) and len(text) <= 8:
        return "disease"

    syndrome_kw = ["虚", "实", "寒", "热", "湿", "瘀", "郁", "结", "不足", "亏损", "壅盛", "失调"]
    if any(kw in text for kw in syndrome_kw) and len(text) <= 8:
        return "syndrome"

    return "symptom"


def save_kg_raw_result(symptoms, allergy_herbs=None, filename="kg_raw_result.txt"):
    """兼容旧调试入口；诊疗数据不再落盘为调试文件。"""
    input_text = ",".join(symptoms)
    if allergy_herbs and len(allergy_herbs) > 0:
        allergy_text = "，并且对" + "、".join(allergy_herbs) + "过敏"
        input_text += allergy_text

    kg_result = call_kg_service(input_text)
    logger.warning("kg_debug_export_disabled")
    return kg_result

if __name__ == "__main__":
    test_symptoms = ["头痛", "发寒", "无汗"]
    test_allergy = ["麻黄", "桂枝"]
    save_kg_raw_result(test_symptoms, test_allergy)

    result = query_kg_for_symptoms(test_symptoms, test_allergy)
    logger.info("kg_manual_check_completed success=%s", bool(result.get("success")))
