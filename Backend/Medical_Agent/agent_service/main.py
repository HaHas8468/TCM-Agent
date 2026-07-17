import os
import sys
import logging
import asyncio
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import uvicorn
from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel
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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

API_KEY = os.getenv('AGENT_API_KEY', '')


async def verify_api_key(request: Request):
    if not API_KEY:
        return
    api_key = request.headers.get('X-API-Key')
    if api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = datetime.now()
    logger.info(f"Agent Request: {request.method} {request.url}")
    
    try:
        response = await call_next(request)
        process_time = (datetime.now() - start_time).total_seconds()
        logger.info(f"Agent Response: {response.status_code} - {process_time:.2f}s")
        return response
    except Exception as e:
        process_time = (datetime.now() - start_time).total_seconds()
        logger.error(f"Agent Error: {str(e)} - {process_time:.2f}s")
        return JSONResponse(
            status_code=500,
            content={"error": "Internal server error", "detail": str(e)}
        )


class AgentInput(BaseModel):
    session_id: str
    patient_id: str
    user_input: str
    mode: str = "normal"
    scene: str = "guide"
    patient_profile: Optional[Dict[str, Any]] = None


class DiagnosisInput(BaseModel):
    symptoms: List[str]
    tongue: Optional[List[str]] = []
    pulse: Optional[List[str]] = []
    other_signs: Optional[str] = ""


class KnowledgeQueryInput(BaseModel):
    query_type: str
    keyword: Optional[str] = ""
    params: Optional[Dict[str, Any]] = {}


@app.on_event("startup")
async def startup_event():
    try:
        neo4j_conn.connect()
        logger.info("Neo4j connection established successfully")
    except Exception as e:
        logger.error(f"Failed to connect to Neo4j: {str(e)}")


@app.on_event("shutdown")
async def shutdown_event():
    try:
        neo4j_conn.close()
        logger.info("Neo4j connection closed")
    except Exception as e:
        logger.error(f"Failed to close Neo4j connection: {str(e)}")


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "agent"}


@app.post("/agent/chat")
async def agent_chat(input_data: AgentInput, _=Depends(verify_api_key)):
    try:
        logger.info(f"Agent chat request: session={input_data.session_id}, patient={input_data.patient_id}")
        result = tcm_agent_chat(
            session_id=input_data.session_id,
            patient_id=input_data.patient_id,
            user_input=input_data.user_input,
            mode=input_data.mode,
            scene=input_data.scene,
            patient_profile=input_data.patient_profile
        )
        
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
    except Exception as e:
        logger.error(f"agent_chat error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/agent/classify")
async def agent_classify(input_data: AgentInput, _=Depends(verify_api_key)):
    try:
        logger.info(f"Agent classify request: session={input_data.session_id}")
        result = tcm_agent_chat(
            session_id=input_data.session_id,
            patient_id=input_data.patient_id,
            user_input=input_data.user_input,
            mode=input_data.mode,
            scene=input_data.scene,
            patient_profile=input_data.patient_profile
        )
        return result
    except Exception as e:
        logger.error(f"agent_classify error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/agent/recommend")
async def agent_recommend(input_data: AgentInput, _=Depends(verify_api_key)):
    try:
        logger.info(f"Agent recommend request: session={input_data.session_id}")
        result = tcm_agent_chat(
            session_id=input_data.session_id,
            patient_id=input_data.patient_id,
            user_input=input_data.user_input,
            mode=input_data.mode,
            scene=input_data.scene,
            patient_profile=input_data.patient_profile
        )
        return result
    except Exception as e:
        logger.error(f"agent_recommend error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


async def generate_stream_response(user_input: str) -> AsyncGenerator[str, None]:
    try:
        result = tcm_agent_chat(
            session_id="stream_session",
            patient_id="stream_patient",
            user_input=user_input,
            mode="normal",
            scene="guide"
        )
        response_text = str(result.get("response", str(result)))
        chunks = [response_text[i:i+100] for i in range(0, len(response_text), 100)]
        for chunk in chunks:
            await asyncio.sleep(0.05)
            yield chunk
    except Exception as e:
        yield f"Error: {str(e)}"


@app.post("/agent/stream")
async def agent_stream(input_data: AgentInput, _=Depends(verify_api_key)):
    try:
        logger.info(f"Agent stream request: session={input_data.session_id}")
        return StreamingResponse(
            generate_stream_response(input_data.user_input),
            media_type="text/event-stream"
        )
    except Exception as e:
        logger.error(f"agent_stream error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/diagnosis/classify")
async def classify_zheng(input_data: DiagnosisInput, _=Depends(verify_api_key)):
    try:
        kg_results = DiagnosisQueries.get_zheng_by_symptoms(input_data.symptoms)
        
        result = tcm_agent_chat(
            session_id="diagnosis_classify",
            patient_id="classify_patient",
            user_input=f"症状：{', '.join(input_data.symptoms)}，舌象：{', '.join(input_data.tongue)}，脉象：{', '.join(input_data.pulse)}，其他体征：{input_data.other_signs}",
            mode="normal",
            scene="guide"
        )
        
        diagnosis_result = result.get("diagnosis_result", {})
        
        return {
            "zheng_type": diagnosis_result.get('zheng_type', '未确定'),
            "confidence": diagnosis_result.get('confidence', 0),
            "description": diagnosis_result.get('description', ''),
            "reasoning": diagnosis_result.get('reasoning', ''),
            "knowledge_graph_matches": kg_results
        }
    except Exception as e:
        logger.error(f"classify_zheng error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/diagnosis/extract-entities")
async def extract_entities(text: str, _=Depends(verify_api_key)):
    try:
        result = tcm_agent_chat(
            session_id="extract_entities",
            patient_id="entity_patient",
            user_input=f"请从以下文本中提取中医实体：{text}",
            mode="normal",
            scene="guide"
        )
        return result
    except Exception as e:
        logger.error(f"extract_entities error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


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
    except Exception as e:
        logger.error(f"knowledge_query error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    port = int(os.getenv('AGENT_PORT', 8001))
    uvicorn.run(app, host="0.0.0.0", port=port)