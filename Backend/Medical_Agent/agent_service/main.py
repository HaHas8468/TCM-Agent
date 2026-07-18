import os
import sys
import logging
import asyncio
import anyio
import secrets
import json
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import uvicorn
from fastapi import FastAPI, HTTPException, Request, Depends, Query
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, AsyncGenerator

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "traditional_medical_agent"))

from knowledge_graph.queries import DiagnosisQueries, FormulaQueries, HerbQueries, MedicalRecordQueries
from knowledge_graph.neo4j_connection import neo4j_conn
from tcm_agent import tcm_agent_chat
from kg_service import get_herb_detail, search_medical_cases


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('agent_service.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


app = FastAPI(title="中医药诊疗智能体 - Agent服务", version="1.0.0")

API_KEY = os.getenv('AGENT_API_KEY', '')
AGENT_TIMEOUT_SECONDS = int(os.getenv("AGENT_TIMEOUT_SECONDS", "90"))
AGENT_STREAM_CHUNK_SIZE = max(1, int(os.getenv("AGENT_STREAM_CHUNK_SIZE", "12")))
AGENT_STREAM_CHUNK_DELAY_SECONDS = max(0.01, float(os.getenv("AGENT_STREAM_CHUNK_DELAY_SECONDS", "0.06")))
agent_limiter = anyio.CapacityLimiter(int(os.getenv("AGENT_MAX_CONCURRENCY", "4")))


async def verify_api_key(request: Request):
    if not API_KEY:
        raise HTTPException(status_code=503, detail="Agent 服务配置不完整")
    api_key = request.headers.get('X-API-Key')
    if not api_key or not secrets.compare_digest(api_key, API_KEY):
        raise HTTPException(status_code=401, detail="Unauthorized")


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = datetime.now()
    logger.info("agent_request method=%s path=%s", request.method, request.url.path)
    
    try:
        response = await call_next(request)
        process_time = (datetime.now() - start_time).total_seconds()
        logger.info(f"Agent Response: {response.status_code} - {process_time:.2f}s")
        return response
    except Exception as e:
        process_time = (datetime.now() - start_time).total_seconds()
        logger.exception("agent_request_failed duration=%.2fs", process_time)
        return JSONResponse(
            status_code=500,
            content={"error": "Internal server error"}
        )


class AgentInput(BaseModel):
    session_id: str = Field(min_length=1, max_length=128)
    patient_id: str = Field(min_length=1, max_length=50)
    user_input: str = Field(min_length=1, max_length=4000)
    mode: str = Field(default="normal", max_length=30)
    scene: str = Field(default="guide", max_length=30)
    patient_profile: Optional[Dict[str, Any]] = None


class DiagnosisInput(BaseModel):
    symptoms: List[str] = Field(min_length=1, max_length=20)
    tongue: Optional[List[str]] = Field(default_factory=list, max_length=20)
    pulse: Optional[List[str]] = Field(default_factory=list, max_length=20)
    other_signs: Optional[str] = Field(default="", max_length=2000)


class KnowledgeQueryInput(BaseModel):
    query_type: str = Field(min_length=1, max_length=50)
    keyword: Optional[str] = Field(default="", max_length=500)
    params: Optional[Dict[str, Any]] = None


async def run_agent_chat(input_data: AgentInput) -> Dict[str, Any]:
    def invoke():
        return tcm_agent_chat(
            session_id=input_data.session_id,
            patient_id=input_data.patient_id,
            user_input=input_data.user_input,
            mode=input_data.mode,
            scene=input_data.scene,
            patient_profile=input_data.patient_profile,
        )
    with anyio.fail_after(AGENT_TIMEOUT_SECONDS):
        return await anyio.to_thread.run_sync(invoke, limiter=agent_limiter)


@app.on_event("startup")
async def startup_event():
    if not API_KEY or not os.getenv("REDIS_URL"):
        raise RuntimeError("AGENT_API_KEY 或 REDIS_URL 未配置")
    try:
        neo4j_conn.connect()
        logger.info("Neo4j connection established successfully")
    except Exception as e:
        logger.exception("Neo4j connection failed")


@app.on_event("shutdown")
async def shutdown_event():
    try:
        neo4j_conn.close()
        logger.info("Neo4j connection closed")
    except Exception:
        logger.exception("neo4j_connection_close_failed")


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "agent"}


@app.post("/agent/chat")
async def agent_chat(input_data: AgentInput, _=Depends(verify_api_key)):
    try:
        result = await run_agent_chat(input_data)
        
        if result.get("status") == "diagnosed" and input_data.scene == "doctor":
            diagnosis_result = result.get("diagnosis_result", {})
            syndrome = diagnosis_result.get("syndrome", "")
            ingredients = diagnosis_result.get("ingredients", [])
            
            if ingredients:
                similar_herbs = []
                for herb_name in ingredients[:3]:
                    herb_detail = get_herb_detail(name=herb_name)
                    if herb_detail.get("success") and herb_detail.get("herb"):
                        similar_herbs.append(herb_name)
                
                if similar_herbs:
                    result["diagnosis_result"]["similar_herbs"] = similar_herbs
            
            if syndrome:
                similar_cases_result = search_medical_cases(
                    query=syndrome,
                    query_type="syndrome",
                    limit=3
                )
                if similar_cases_result.get("success") and similar_cases_result.get("cases"):
                    similar_cases = []
                    for case in similar_cases_result["cases"][:3]:
                        if isinstance(case, dict):
                            case_title = case.get("title", case.get("caseId", ""))
                            if case_title:
                                similar_cases.append(str(case_title))
                    if similar_cases:
                        result["diagnosis_result"]["similar_cases"] = similar_cases
        
        return result
    except Exception:
        logger.exception("agent_chat failed")
        raise HTTPException(status_code=502, detail="智能助手暂不可用")


@app.post("/agent/classify")
async def agent_classify(input_data: AgentInput, _=Depends(verify_api_key)):
    try:
        result = await run_agent_chat(input_data)
        return result
    except Exception:
        logger.exception("agent_classify failed")
        raise HTTPException(status_code=502, detail="智能助手暂不可用")


@app.post("/agent/recommend")
async def agent_recommend(input_data: AgentInput, _=Depends(verify_api_key)):
    try:
        result = await run_agent_chat(input_data)
        return result
    except Exception:
        logger.exception("agent_recommend failed")
        raise HTTPException(status_code=502, detail="智能助手暂不可用")


async def generate_stream_response(input_data: AgentInput) -> AsyncGenerator[str, None]:
    try:
        # 先推送一个可见的执行阶段，避免前端只能等同步 Agent 完成后一次性得到全部摘要。
        initial_trace = {
            "state": "running",
            "steps": [{"title": "症状信息整理", "detail": "正在分析本次描述中的症状信息"}],
            "tools": [],
        }
        yield f"data: {json.dumps({'event': 'trace', 'trace': initial_trace}, ensure_ascii=False)}\n\n"
        result = await run_agent_chat(input_data)
        if result.get("trace"):
            # 同步 Agent 完成后先推送真实摘要，再发送回答正文，避免患者端长期停留在占位步骤。
            yield f"data: {json.dumps({'event': 'trace', 'trace': result['trace']}, ensure_ascii=False)}\n\n"
        response_text = str(result.get("response", str(result)))
        chunks = [response_text[i:i + AGENT_STREAM_CHUNK_SIZE] for i in range(0, len(response_text), AGENT_STREAM_CHUNK_SIZE)]
        for chunk in chunks:
            await asyncio.sleep(AGENT_STREAM_CHUNK_DELAY_SECONDS)
            # 前端 SSE 解析器只处理 data: 帧；裸文本会被静默丢弃并最终视为异常结束。
            payload = {
                "status": result.get("status", "done"),
                "response": chunk,
                "finish": False,
            }
            yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"

        final_payload = {
            "status": result.get("status", "done"),
            "finish": True,
        }
        if result.get("diagnosis_result"):
            final_payload["diagnosis"] = result["diagnosis_result"]
        if result.get("trace"):
            final_payload["trace"] = result["trace"]
        yield f"data: {json.dumps(final_payload, ensure_ascii=False)}\n\n"
        yield "data: [DONE]\n\n"
    except Exception:
        logger.exception("agent_stream failed")
        yield "data: {\"code\":502,\"data\":{\"status\":\"error\",\"response\":\"智能助手暂不可用\"}}\n\n"
        yield "data: [DONE]\n\n"


@app.post("/agent/stream")
async def agent_stream(input_data: AgentInput, _=Depends(verify_api_key)):
    try:
        return StreamingResponse(
            generate_stream_response(input_data),
            media_type="text/event-stream"
        )
    except Exception:
        logger.exception("agent_stream initialization failed")
        raise HTTPException(status_code=502, detail="智能助手暂不可用")


@app.post("/diagnosis/classify")
async def classify_zheng(input_data: DiagnosisInput, _=Depends(verify_api_key)):
    try:
        kg_results = DiagnosisQueries.get_zheng_by_symptoms(input_data.symptoms)
        
        result = await run_agent_chat(AgentInput(
            session_id="diagnosis_classify",
            patient_id="classify_patient",
            user_input=f"症状：{', '.join(input_data.symptoms)}，舌象：{', '.join(input_data.tongue)}，脉象：{', '.join(input_data.pulse)}，其他体征：{input_data.other_signs}",
        ))
        
        diagnosis_result = result.get("diagnosis_result", {})
        
        return {
            "zheng_type": diagnosis_result.get('zheng_type', '未确定'),
            "confidence": diagnosis_result.get('confidence', 0),
            "description": diagnosis_result.get('description', ''),
            "reasoning": diagnosis_result.get('reasoning', ''),
            "knowledge_graph_matches": kg_results
        }
    except Exception:
        logger.exception("classify_zheng failed")
        raise HTTPException(status_code=502, detail="诊断服务暂不可用")


@app.post("/diagnosis/extract-entities")
async def extract_entities(text: str = Query(min_length=1, max_length=4000), _=Depends(verify_api_key)):
    try:
        result = await run_agent_chat(AgentInput(
            session_id="extract_entities",
            patient_id="entity_patient",
            user_input=f"请从以下文本中提取中医实体：{text}",
        ))
        return result
    except Exception:
        logger.exception("extract_entities failed")
        raise HTTPException(status_code=502, detail="实体提取服务暂不可用")


@app.post("/knowledge/query")
async def knowledge_query(input_data: KnowledgeQueryInput, _=Depends(verify_api_key)):
    try:
        query_type = input_data.query_type
        keyword = input_data.keyword
        params = input_data.params or {}
        
        if query_type == "herb_search":
            result = HerbQueries.search_herbs(keyword)
        elif query_type == "herb_detail":
            result = HerbQueries.get_herb_details(keyword)
        elif query_type == "herb_by_property":
            result = HerbQueries.get_herbs_by_property(keyword)
        elif query_type == "herb_by_meridian":
            result = HerbQueries.get_herbs_by_meridian(keyword)
        elif query_type == "herb_compatibility":
            result = HerbQueries.get_compatibility_relations(keyword)
        elif query_type == "formula_search":
            result = FormulaQueries.search_formulas(keyword)
        elif query_type == "formula_detail":
            result = FormulaQueries.get_formula_details(keyword)
        elif query_type == "formula_by_zheng":
            result = FormulaQueries.get_formulas_by_zheng(keyword)
        elif query_type == "formula_by_herb":
            result = FormulaQueries.get_formulas_by_herb(keyword)
        elif query_type == "zheng_search":
            result = DiagnosisQueries.get_zheng_by_symptoms([keyword])
        elif query_type == "zheng_detail":
            result = DiagnosisQueries.get_zheng_details(keyword)
        elif query_type == "zheng_list":
            result = DiagnosisQueries.get_all_zheng_types()
        elif query_type == "record_search":
            result = MedicalRecordQueries.search_records(
                params.get('disease_name', ''),
                params.get('zheng_type', ''),
                params.get('formula_name', '')
            )
        elif query_type == "record_detail":
            result = MedicalRecordQueries.get_record_details(keyword)
        elif query_type == "record_by_herb":
            result = MedicalRecordQueries.search_records_by_herb(keyword)
        else:
            raise HTTPException(status_code=400, detail=f"Unknown query type: {query_type}")
        
        return {"query_type": query_type, "data": result}
    except HTTPException:
        raise
    except Exception:
        logger.exception("knowledge_query failed")
        raise HTTPException(status_code=502, detail="知识图谱服务暂不可用")


if __name__ == "__main__":
    port = int(os.getenv('AGENT_PORT', 8001))
    uvicorn.run(app, host="0.0.0.0", port=port)
