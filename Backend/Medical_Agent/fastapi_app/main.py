import os
import sys
import logging
import time
import uuid
import re
import json
import psutil
from contextvars import ContextVar
from datetime import datetime, timedelta
from typing import Annotated, Optional, List, Dict, Any, Union

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "traditional_medical_agent"))

import uvicorn
from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, Column, Integer, String, Text, Date, DateTime, DECIMAL, JSON, Boolean, ForeignKey, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from sqlalchemy.exc import SQLAlchemyError
from dotenv import load_dotenv

from .remote_agent_client import remote_agent_client
from .security import (
    generate_token,
    get_redis,
    parse_token,
    require_auth,
    revoke_token,
    validate_runtime_config,
)
from .rate_limit import (
    limit_agent_request,
    limit_anonymous_write,
    limit_authenticated_write,
    limit_login,
    rate_limit_error_response,
)
from traditional_medical_agent.kg_service import add_case, search_by_doctor


load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


DB_HOST = os.getenv('MYSQL_HOST', 'localhost')
DB_PORT = int(os.getenv('MYSQL_PORT', 3306))
DB_USER = os.getenv('MYSQL_USER', 'root')
DB_PASSWORD = os.getenv('MYSQL_PASSWORD', '')
DB_NAME = os.getenv('MYSQL_DB', 'traditional_medical')

DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"

engine = create_engine(DATABASE_URL, pool_pre_ping=True, pool_size=5, max_overflow=10)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
request_db_sessions: ContextVar[Optional[List[Session]]] = ContextVar("request_db_sessions", default=None)

Base = declarative_base()


class ApiDepartment(Base):
    __tablename__ = 'api_department'
    id = Column(Integer, primary_key=True, autoincrement=True)
    department_id = Column(String(50), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    parent_department_id = Column(Integer, ForeignKey('api_department.id'))
    created_at = Column(DateTime, default=datetime.now)


class ApiPatient(Base):
    __tablename__ = 'api_patient'
    id = Column(Integer, primary_key=True, autoincrement=True)
    patient_id = Column(String(50), unique=True)
    username = Column(String(150), unique=True, nullable=False)
    password = Column(String(128), nullable=False)
    name = Column(String(100), nullable=False)
    gender = Column(String(10), nullable=False)
    birth_date = Column(Date)
    age = Column(Integer, nullable=False)
    phone = Column(String(20))
    address = Column(String(200))
    id_card = Column(String(20), unique=True)
    blood_type = Column(String(10))
    health_info = Column(Text)
    allergy_history = Column(JSON)
    emergency_contact = Column(String(100))
    emergency_phone = Column(String(20))
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class ApiDoctor(Base):
    __tablename__ = 'api_doctor'
    id = Column(Integer, primary_key=True, autoincrement=True)
    doctor_id = Column(String(50), unique=True, nullable=False)
    username = Column(String(150), unique=True, nullable=False)
    password = Column(String(128), nullable=False)
    name = Column(String(100), nullable=False)
    title = Column(String(50))
    hospital = Column(String(100))
    department_id = Column(Integer, ForeignKey('api_department.id'))
    license_number = Column(String(50))
    specialty = Column(String(100))
    experience = Column(Integer)
    phone = Column(String(20))
    duty_time = Column(String(100))
    bio = Column(Text)
    description = Column(Text)
    default_landing = Column(String(50), nullable=False, default='queue')
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class ApiOrder(Base):
    __tablename__ = 'api_order'
    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(String(50), unique=True, nullable=False)
    patient_id = Column(Integer, ForeignKey('api_patient.id'), nullable=False)
    doctor_id = Column(Integer, ForeignKey('api_doctor.id'))
    department_id = Column(Integer, ForeignKey('api_department.id'))
    department = Column(String(100))
    schedule_id = Column(Integer)
    order_type = Column(String(20), default='online')
    source = Column(String(20), default='direct')
    status = Column(String(20), default='pending')
    visit_time = Column(DateTime)
    date = Column(Date)
    time = Column(String(20))
    waiting_number = Column(Integer)
    amount = Column(DECIMAL(10, 2))
    payment_time = Column(DateTime)
    qr_code = Column(String(200))
    scanned = Column(Boolean, default=False)
    chief_complaint = Column(Text)
    present_illness = Column(Text)
    tongue = Column(String(200))
    pulse = Column(String(200))
    symptoms = Column(JSON)
    signs = Column(String(200))
    other = Column(Text)
    syndrome = Column(String(200))
    prescription = Column(String(200))
    ingredients = Column(JSON)
    advice = Column(Text)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class ApiClinicRecord(Base):
    __tablename__ = 'api_clinicrecord'
    id = Column(Integer, primary_key=True, autoincrement=True)
    record_id = Column(String(50), unique=True, nullable=False)
    patient_id = Column(Integer, ForeignKey('api_patient.id'), nullable=False)
    doctor_id = Column(Integer, ForeignKey('api_doctor.id'))
    order_id = Column(Integer, ForeignKey('api_order.id'))
    visit_date = Column(DateTime, default=datetime.now)
    chief_complaint = Column(Text, nullable=False)
    history_of_present_illness = Column(Text)
    past_history = Column(Text)
    physical_examination = Column(Text)
    tongue = Column(String(200))
    pulse = Column(String(200))
    other_signs = Column(Text)
    zheng_type = Column(String(100))
    zheng_description = Column(Text)
    diagnosis = Column(Text)
    treatment_principle = Column(Text)
    treatment_plan = Column(Text)
    prescription = Column(String(200))
    herbs = Column(JSON)
    ingredients = Column(JSON)
    dosage = Column(Text)
    decoction_method = Column(Text)
    advice = Column(Text)
    notes = Column(Text)
    follow_up = Column(String(100))
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)



class ApiSchedule(Base):
    __tablename__ = 'api_schedule'
    id = Column(Integer, primary_key=True, autoincrement=True)
    schedule_id = Column(String(50), unique=True, nullable=False)
    doctor_id = Column(Integer, ForeignKey('api_doctor.id'), nullable=False)
    department_id = Column(Integer, ForeignKey('api_department.id'), nullable=False)
    date = Column(Date, nullable=False)
    start_time = Column(String(20), nullable=False)
    end_time = Column(String(20), nullable=False)
    morning_afternoon = Column(String(10), nullable=False)
    total_slots = Column(Integer, default=30)
    available_slots = Column(Integer, default=30)
    status = Column(String(20), default='available')
    created_at = Column(DateTime, default=datetime.now)


def get_db():
    db = SessionLocal()
    sessions = request_db_sessions.get()
    if sessions is not None:
        sessions.append(db)
    try:
        yield db
    finally:
        db.close()


def schedule_time_to_minutes(value: Any) -> int:
    """将数据库 TIME / 字符串时间统一转换为当天的分钟数。"""
    if isinstance(value, datetime):
        return value.hour * 60 + value.minute
    if isinstance(value, timedelta):
        return (value.seconds // 60) % (24 * 60)
    if hasattr(value, "hour") and hasattr(value, "minute"):
        return int(value.hour) * 60 + int(value.minute)

    parts = str(value).strip().split(":")
    if len(parts) < 2:
        raise ValueError("排班时间格式无效")
    hour, minute = int(parts[0]), int(parts[1])
    if not (0 <= hour < 24 and 0 <= minute < 60):
        raise ValueError("排班时间超出范围")
    return hour * 60 + minute


def schedule_slot_times(schedule: ApiSchedule, interval_minutes: int = 30) -> List[str]:
    """按排班起止时间生成固定间隔的可预约时段。"""
    start_minutes = schedule_time_to_minutes(schedule.start_time)
    end_minutes = schedule_time_to_minutes(schedule.end_time)
    if end_minutes <= start_minutes:
        return []
    return [
        f"{minute // 60:02d}:{minute % 60:02d}"
        for minute in range(start_minutes, end_minutes, interval_minutes)
    ]


def get_patient_profile(db: Session, patient_id: str) -> Dict[str, Any]:
    patient = db.query(ApiPatient).filter(ApiPatient.patient_id == patient_id).first()
    if patient:
        return {
            "patient_id": patient.patient_id,
            "allergy_history": {"herbs": patient.allergy_history or []}
        }
    return {"patient_id": patient_id, "allergy_history": {"herbs": []}}


def require_role(token_info: Dict[str, Any], *roles: str) -> None:
    if token_info.get("role") not in roles:
        raise HTTPException(status_code=403, detail="无权访问该资源")


def current_doctor(db: Session, token_info: Dict[str, Any]) -> ApiDoctor:
    require_role(token_info, "doctor")
    doctor = db.query(ApiDoctor).filter(ApiDoctor.doctor_id == token_info["role_id"]).first()
    if not doctor:
        raise HTTPException(status_code=401, detail="医生账号不存在")
    return doctor


def current_patient(db: Session, token_info: Dict[str, Any]) -> ApiPatient:
    require_role(token_info, "patient")
    patient = db.query(ApiPatient).filter(ApiPatient.patient_id == token_info["role_id"]).first()
    if not patient:
        raise HTTPException(status_code=401, detail="患者账号不存在")
    return patient


def require_order_access(db: Session, order_id: str, token_info: Dict[str, Any], *, write: bool = False) -> ApiOrder:
    order = db.query(ApiOrder).filter(ApiOrder.order_id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    if token_info.get("role") == "patient":
        if write or str(order.patient_id) != str(current_patient(db, token_info).id):
            raise HTTPException(status_code=403, detail="无权操作该订单")
    elif token_info.get("role") == "doctor":
        if order.doctor_id != current_doctor(db, token_info).id:
            raise HTTPException(status_code=403, detail="无权操作该订单")
    else:
        raise HTTPException(status_code=403, detail="无权访问该订单")
    return order


def require_agent_patient_access(db: Session, patient_id: str, token_info: Dict[str, Any]) -> ApiPatient:
    patient = db.query(ApiPatient).filter(ApiPatient.patient_id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="患者不存在")
    if token_info.get("role") == "patient":
        if patient.patient_id != token_info.get("role_id"):
            raise HTTPException(status_code=403, detail="无权访问其他患者信息")
    elif token_info.get("role") == "doctor":
        doctor = current_doctor(db, token_info)
        assigned = db.query(ApiOrder.id).filter(
            ApiOrder.patient_id == patient.id,
            ApiOrder.doctor_id == doctor.id,
            ApiOrder.status.in_(["pending", "ongoing"]),
        ).first()
        if not assigned:
            raise HTTPException(status_code=403, detail="仅可为当前接诊患者调用智能助手")
    else:
        raise HTTPException(status_code=403, detail="无权访问患者信息")
    return patient


ShortText = Annotated[str, Field(min_length=1, max_length=100)]
IdentifierText = Annotated[str, Field(min_length=1, max_length=50)]
ClinicalText = Annotated[str, Field(max_length=4000)]
IngredientText = Annotated[str, Field(min_length=1, max_length=100)]


class RegisterInput(BaseModel):
    username: Annotated[str, Field(min_length=1, max_length=150)]
    password: Annotated[str, Field(min_length=1, max_length=256)]
    confirm_password: Annotated[str, Field(min_length=1, max_length=256)]
    name: Optional[ShortText] = None
    phone: Optional[Annotated[str, Field(max_length=20)]] = None


class LoginInput(BaseModel):
    username: Annotated[str, Field(min_length=1, max_length=150)]
    password: Annotated[str, Field(min_length=1, max_length=256)]


class PatientProfileInput(BaseModel):
    name: Optional[ShortText] = None
    password: Optional[Annotated[str, Field(min_length=1, max_length=256)]] = None
    gender: Optional[Annotated[str, Field(max_length=10)]] = None
    birth_date: Optional[Annotated[str, Field(pattern=r"^\d{4}-\d{2}-\d{2}$")]] = None
    age: Optional[Annotated[int, Field(ge=0, le=150)]] = None
    phone: Optional[Annotated[str, Field(max_length=20)]] = None
    allergy_history: Optional[Annotated[List[IngredientText], Field(max_length=50)]] = None


class DoctorProfileInput(BaseModel):
    name: Optional[ShortText] = None
    password: Optional[Annotated[str, Field(min_length=1, max_length=256)]] = None
    title: Optional[Annotated[str, Field(max_length=50)]] = None
    hospital: Optional[Annotated[str, Field(max_length=100)]] = None
    department_id: Optional[Annotated[int, Field(ge=1)]] = None
    license_number: Optional[Annotated[str, Field(max_length=50)]] = None
    specialty: Optional[ShortText] = None
    experience: Optional[Annotated[int, Field(ge=0, le=100)]] = None
    phone: Optional[Annotated[str, Field(max_length=20)]] = None
    duty_time: Optional[ShortText] = None
    bio: Optional[ClinicalText] = None
    description: Optional[ClinicalText] = None


class AgentInput(BaseModel):
    session_id: Optional[Annotated[str, Field(min_length=1, max_length=128)]] = None
    patient_id: Optional[IdentifierText] = None
    user_input: Annotated[str, Field(min_length=1, max_length=4000)]
    mode: Annotated[str, Field(max_length=30)] = "normal"
    scene: Annotated[str, Field(max_length=30)] = "guide"
    patient_profile: Optional[Dict[str, Any]] = None
    therapy: Optional[ClinicalText] = None        # 疗法（存入 api_clinicrecord.chief_complaint）
    precautions: Optional[ClinicalText] = None    # 注意事项（存入 api_clinicrecord.history_of_present_illness）


class CreateOrderInput(BaseModel):
    patient_id: IdentifierText
    doctor_id: IdentifierText
    department: ShortText
    date: Annotated[str, Field(pattern=r"^\d{4}-\d{2}-\d{2}$")]
    time: Annotated[str, Field(pattern=r"^([01]\d|2[0-3]):[0-5]\d$")]
    source: Annotated[str, Field(max_length=20)] = "direct"


class FinishOrderInput(BaseModel):
    syndrome: ShortText
    prescription: ShortText
    ingredients: Annotated[List[IngredientText], Field(max_length=50)]
    advice: ClinicalText
    therapy: Optional[ClinicalText] = None        # 疗法（存入 api_clinicrecord.chief_complaint）
    precautions: Optional[ClinicalText] = None    # 注意事项（存入 api_clinicrecord.history_of_present_illness）


class SaveOrderInput(BaseModel):
    syndrome: Optional[ShortText] = None
    prescription: Optional[ShortText] = None
    ingredients: Optional[Annotated[List[IngredientText], Field(max_length=50)]] = None
    advice: Optional[ClinicalText] = None
    therapy: Optional[ClinicalText] = None        # 疗法
    precautions: Optional[ClinicalText] = None    # 注意事项


class DiagnosisInput(BaseModel):
    chief_complaint: ClinicalText
    present_illness: ClinicalText
    tongue: Annotated[str, Field(max_length=200)]
    pulse: Annotated[str, Field(max_length=200)]
    symptoms: Annotated[List[IngredientText], Field(min_length=1, max_length=20)]
    signs: Annotated[str, Field(max_length=200)]
    other: ClinicalText


class EntityWithNameId(BaseModel):
    """实体节点，支持 name 和可选的 id"""
    name: ShortText
    id: Optional[IdentifierText] = None


def _convert_entity_list(entities):
    """将前端传入的实体列表转换为 addCase 兼容格式。

    实体可以是字符串 / 字符串列表 / 含 {name, id?} 的对象列表。
    Pydantic 模型对象会被转为纯 dict，None / 空列表原样返回。
    """
    if entities is None:
        return None
    if isinstance(entities, str):
        return entities
    if not isinstance(entities, (list, tuple)):
        return entities

    result = []
    for item in entities:
        if item is None:
            continue
        if isinstance(item, str):
            result.append(item)
        elif hasattr(item, "name"):
            # Pydantic 模型对象 / 有 name 属性的对象 → 转 dict
            entry = {"name": item.name}
            item_id = getattr(item, "id", None)
            if item_id:
                entry["id"] = item_id
            result.append(entry)
        elif isinstance(item, dict):
            # 已经是 dict，直接保留
            if item.get("name"):
                result.append(item)
        else:
            # 兜底转字符串
            result.append(str(item))

    return result if result else None


class AddCaseInput(BaseModel):
    title: Annotated[str, Field(min_length=1, max_length=200)]
    summary: Optional[ClinicalText] = None
    rawText: Optional[Annotated[str, Field(max_length=20000)]] = None
    sourceUrl: Optional[Annotated[str, Field(max_length=500)]] = None
    publishDate: Optional[Annotated[str, Field(max_length=30)]] = None
    author: Optional[ShortText] = None
    channel: Optional[ShortText] = None
    diseases: Optional[Union[ShortText, Annotated[List[ShortText], Field(max_length=50)], Annotated[List[EntityWithNameId], Field(max_length=50)]]] = None
    syndromes: Optional[Union[ShortText, Annotated[List[ShortText], Field(max_length=50)], Annotated[List[EntityWithNameId], Field(max_length=50)]]] = None
    symptoms: Optional[Union[ShortText, Annotated[List[ShortText], Field(max_length=50)], Annotated[List[EntityWithNameId], Field(max_length=50)]]] = None
    formulas: Optional[Union[ShortText, Annotated[List[ShortText], Field(max_length=50)], Annotated[List[EntityWithNameId], Field(max_length=50)]]] = None
    treatmentMethods: Optional[Union[ShortText, Annotated[List[ShortText], Field(max_length=50)], Annotated[List[EntityWithNameId], Field(max_length=50)]]] = None
    doctors: Optional[Union[ShortText, Annotated[List[ShortText], Field(max_length=50)], Annotated[List[EntityWithNameId], Field(max_length=50)]]] = None


app = FastAPI(title="中医药诊疗智能体 API", version="1.0.0")


@app.middleware("http")
async def close_request_db_sessions(request: Request, call_next):
    """兼容旧接口的手工 Session 获取方式，确保请求结束后归还连接。"""
    token = request_db_sessions.set([])
    try:
        return await call_next(request)
    finally:
        for db in request_db_sessions.get() or []:
            db.close()
        request_db_sessions.reset(token)


@app.on_event("startup")
async def startup_event():
    validate_runtime_config()


@app.on_event("shutdown")
async def shutdown_event():
    remote_agent_client.close()


@app.exception_handler(HTTPException)
async def http_exception_handler(_: Request, exc: HTTPException):
    return rate_limit_error_response(exc)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_: Request, __: RequestValidationError):
    return JSONResponse(status_code=422, content={"code": 422, "msg": "请求参数无效"})


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    request_id = request.headers.get("x-request-id", "-")
    logger.exception("unhandled_request_error request_id=%s path=%s", request_id, request.url.path)
    return JSONResponse(status_code=500, content={"code": 500, "msg": "服务暂时不可用，请稍后再试"})

cors_origins = [item.strip() for item in os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:8080").split(",") if item.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_memory_usage():
    process = psutil.Process()
    mem_info = process.memory_info()
    return {
        "rss": f"{mem_info.rss / 1024 / 1024:.2f} MB",
        "vms": f"{mem_info.vms / 1024 / 1024:.2f} MB",
        "percent": f"{process.memory_percent():.2f}%"
    }


@app.get("/api/patients/bypatientid/{patient_id}/basic")
async def get_patient_basic_by_patient_id(patient_id: str, token_info: Dict[str, Any] = Depends(require_auth)):
    """通过patient_id（业务ID）查询患者基本信息（gender、age、allergy_history）"""
    require_role(token_info, "doctor")

    db = next(get_db())
    patient = db.query(ApiPatient).filter(ApiPatient.patient_id == patient_id).first()
    if not patient:
        return {"code": 404, "msg": "Patient not found"}

    return {
        "code": 0,
        "data": {
            "patient_id": patient_id,
            "gender": patient.gender,
            "age": patient.age,
            "allergy_history": patient.allergy_history,
        }
    }


@app.middleware("http")
async def log_memory_usage(request, call_next):
    response = await call_next(request)
    mem_usage = get_memory_usage()
    logger.info(f"Memory usage after request: RSS={mem_usage['rss']}, VMS={mem_usage['vms']}, Percent={mem_usage['percent']}")
    return response


@app.get("/health")
async def health_check():
    try:
        db = next(get_db())
        db.query(ApiDepartment).first()
        return {"code": 0, "data": {"status": "healthy", "database": "connected"}}
    except Exception as e:
        logger.error(f"Database connection error: {str(e)}")
        return {"code": 500, "msg": "数据库连接失败"}


@app.get("/health/live")
async def liveness_check():
    return {"code": 0, "data": {"status": "live"}}


@app.get("/health/ready")
async def readiness_check():
    try:
        get_redis().ping()
        db = next(get_db())
        db.execute(text("SELECT 1"))
        if not remote_agent_client.is_available():
            raise RuntimeError("agent unavailable")
        return {"code": 0, "data": {"status": "ready"}}
    except Exception:
        logger.exception("readiness check failed")
        raise HTTPException(status_code=503, detail="依赖服务暂不可用")


@app.post("/api/auth/register")
async def register(input_data: RegisterInput, _: None = Depends(limit_anonymous_write)):
    db = next(get_db())
    
    if input_data.password != input_data.confirm_password:
        return {"code": 400, "msg": "Passwords do not match"}
    
    if db.query(ApiPatient).filter(ApiPatient.username == input_data.username).first():
        return {"code": 400, "msg": "Username already exists"}
    
    try:
        patient_id = f'P{datetime.now().strftime("%Y%m%d%H%M%S")}{uuid.uuid4().hex[:4]}'
        
        patient = ApiPatient(
            patient_id=patient_id,
            username=input_data.username,
            password=input_data.password,
            name=input_data.name or input_data.username,
            gender='男',
            age=0,
            phone=input_data.phone
        )
        db.add(patient)
        db.commit()
        
        return {"code": 0, "data": {"patient_id": patient_id}}
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Register error: {str(e)}")
        return {"code": 500, "msg": "注册失败，请稍后重试"}


@app.post("/api/auth/login")
async def login(input_data: LoginInput, _: None = Depends(limit_login)):
    db = next(get_db())
    
    patient = db.query(ApiPatient).filter(ApiPatient.username == input_data.username).first()
    if not patient or patient.password != input_data.password:
        return {"code": 401, "msg": "Invalid credentials"}
    
    token = generate_token(input_data.username, 'patient', patient.patient_id)
    return {
        "code": 0,
        "data": {
            "token": token,
            "patient_id": patient.patient_id,
            "name": patient.name
        }
    }


@app.post("/api/auth/logout")
async def logout(authorization: str = Header(None), _: Dict[str, Any] = Depends(limit_authenticated_write)):
    revoke_token(authorization)
    return {"code": 0, "data": None}


@app.post("/api/doctor/auth/login")
async def doctor_login(input_data: LoginInput, _: None = Depends(limit_login)):
    db = next(get_db())
    
    doctor = db.query(ApiDoctor).filter(ApiDoctor.username == input_data.username).first()
    if not doctor or doctor.password != input_data.password:
        return {"code": 401, "msg": "Invalid credentials"}
    
    department_name = ""
    if doctor.department_id:
        dept = db.query(ApiDepartment).filter(ApiDepartment.id == doctor.department_id).first()
        if dept:
            department_name = dept.name
    
    token = generate_token(input_data.username, 'doctor', doctor.doctor_id)
    return {
        "code": 0,
        "data": {
            "token": token,
            "doctor_id": doctor.doctor_id,
            "name": doctor.name,
            "department": department_name,
            "default_landing": "queue"
        }
    }


@app.get("/api/patient/profile")
async def get_patient_profile_api(token_info: Dict[str, Any] = Depends(require_auth)):
    require_role(token_info, "patient")
    
    db = next(get_db())
    patient = db.query(ApiPatient).filter(ApiPatient.patient_id == token_info['role_id']).first()
    if not patient:
        return {"code": 404, "msg": "Patient profile not found"}
    
    return {
        "code": 0,
        "data": {
            "patient_id": patient.patient_id,
            "name": patient.name,
            "gender": patient.gender,
            "birth_date": patient.birth_date.isoformat() if patient.birth_date else "",
            "age": patient.age,
            "phone": patient.phone or "",
            "allergy_history": patient.allergy_history or []
        }
    }


@app.put("/api/patient/profile")
async def update_patient_profile(input_data: PatientProfileInput, token_info: Dict[str, Any] = Depends(limit_authenticated_write)):
    require_role(token_info, "patient")
    
    db = next(get_db())
    patient = db.query(ApiPatient).filter(ApiPatient.patient_id == token_info['role_id']).first()
    if not patient:
        return {"code": 404, "msg": "Patient profile not found"}
    
    try:
        update_data = input_data.dict(exclude_unset=True)
        for key, value in update_data.items():
            if key == 'birth_date' and value:
                setattr(patient, key, datetime.strptime(value, '%Y-%m-%d').date())
            else:
                setattr(patient, key, value)
        db.commit()
        return {"code": 0, "data": None}
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Update patient profile error: {str(e)}")
        return {"code": 500, "msg": "资料更新失败，请稍后重试"}


@app.get("/api/departments")
async def get_departments():
    db = next(get_db())
    
    departments = db.query(ApiDepartment).all()
    result = []
    
    for dept in departments:
        doctors = db.query(ApiDoctor).filter(ApiDoctor.department_id == dept.id).all()
        doctor_list = []
        for doc in doctors:
            doctor_list.append({
                'doctor_id': doc.doctor_id,
                'name': doc.name,
                'specialty': doc.specialty or ""
            })
        
        if doctor_list:
            result.append({
                'department': dept.name,
                'doctors': doctor_list
            })
    
    return {"code": 0, "data": result}


@app.get("/api/doctors/{doctor_id}/slots")
async def get_doctor_slots(doctor_id: str, date: str = None):
    db = next(get_db())
    
    if date is None:
        date = datetime.now().date().isoformat()
    
    doctor = db.query(ApiDoctor).filter(ApiDoctor.doctor_id == doctor_id).first()
    if not doctor:
        return {"code": 404, "msg": "Doctor not found"}
    
    target_date = datetime.strptime(date, '%Y-%m-%d').date()
    schedules = db.query(ApiSchedule).filter(
        ApiSchedule.doctor_id == doctor.id,
        ApiSchedule.date == target_date,
        ApiSchedule.status == 'available',
        ApiSchedule.available_slots > 0,
    ).order_by(ApiSchedule.start_time.asc(), ApiSchedule.id.asc()).all()
    
    available_slots = []
    seen_slots = set()
    for schedule in schedules:
        for slot in schedule_slot_times(schedule):
            if slot not in seen_slots:
                available_slots.append(slot)
                seen_slots.add(slot)
    
    return {
        "code": 0,
        "data": {
            "doctor_id": doctor_id,
            "date": date,
            "available_slots": available_slots
        }
    }


@app.post("/api/orders")
async def create_order(input_data: CreateOrderInput, token_info: Dict[str, Any] = Depends(limit_authenticated_write)):
    require_role(token_info, "patient")
    
    db = next(get_db())
    patient = current_patient(db, token_info)
    
    doctor = db.query(ApiDoctor).filter(ApiDoctor.doctor_id == input_data.doctor_id).first()
    if not doctor:
        return {"code": 404, "msg": "Doctor not found"}
    
    try:
        visit_date = datetime.strptime(input_data.date, '%Y-%m-%d').date()
        schedule = db.query(ApiSchedule).filter(
            ApiSchedule.doctor_id == doctor.id,
            ApiSchedule.date == visit_date,
            ApiSchedule.status == 'available',
            ApiSchedule.available_slots > 0,
        ).order_by(ApiSchedule.start_time.asc(), ApiSchedule.id.asc()).with_for_update().all()
        schedule = next((item for item in schedule if input_data.time in schedule_slot_times(item)), None)
        if not schedule:
            db.rollback()
            return JSONResponse(status_code=409, content={"code": 409, "msg": "该时段不可预约或余号不足"})

        order_id = f'O{datetime.now().strftime("%Y%m%d%H%M%S")}{uuid.uuid4().hex[:8]}'
        
        order = ApiOrder(
            order_id=order_id,
            patient_id=patient.id,
            doctor_id=doctor.id,
            department_id=schedule.department_id,
            schedule_id=schedule.id,
            department=input_data.department,
            date=visit_date,
            time=input_data.time,
            source=input_data.source,
            status='pending'
        )
        db.add(order)
        schedule.available_slots -= 1
        db.commit()
        
        return {
            "code": 0,
            "data": {
                "order_id": order_id,
                "status": "pending",
                "doctor_id": input_data.doctor_id,
                "date": input_data.date,
                "time": input_data.time
            }
        }
    except (SQLAlchemyError, ValueError) as e:
        db.rollback()
        logger.error(f"Create order error: {str(e)}")
        return {"code": 500, "msg": "创建订单失败，请稍后重试"}


@app.get("/api/doctor/queue")
async def get_doctor_queue(authorization: str = Header(None), date: str = None, department: str = "", period: str = "all"):
    token_info = parse_token(authorization)
    if not token_info or token_info.get('role') != 'doctor':
        return {"code": 401, "msg": "Unauthorized"}
    
    db = next(get_db())
    doctor = db.query(ApiDoctor).filter(ApiDoctor.doctor_id == token_info['role_id']).first()
    if not doctor:
        return {"code": 404, "msg": "Doctor not found"}
    
    if date is None:
        date = datetime.now().date().isoformat()
    
    target_date = datetime.strptime(date, '%Y-%m-%d').date()
    orders_query = db.query(ApiOrder).filter(ApiOrder.doctor_id == doctor.id, ApiOrder.date == target_date)
    if department:
        orders_query = orders_query.filter(ApiOrder.department == department)
    # 前端接口使用 morning/afternoon，历史及初始化排班数据则使用“上午/下午”。
    # 同时兼容两种写法，避免时段筛选因存储值与接口值不一致而返回空队列。
    period_values = {
        "morning": ("morning", "上午"),
        "上午": ("morning", "上午"),
        "afternoon": ("afternoon", "下午"),
        "下午": ("afternoon", "下午"),
    }.get(period)
    if period_values:
        schedules = db.query(ApiSchedule.id).filter(
            ApiSchedule.doctor_id == doctor.id,
            ApiSchedule.date == target_date,
            ApiSchedule.morning_afternoon.in_(period_values),
        )
        orders_query = orders_query.filter(ApiOrder.schedule_id.in_(schedules))
    orders = orders_query.order_by(ApiOrder.time.asc()).all()
    
    result = []
    for order in orders:
        patient = db.query(ApiPatient).filter(ApiPatient.id == order.patient_id).first()
        dept_name = order.department
        if order.department_id:
            dept = db.query(ApiDepartment).filter(ApiDepartment.id == order.department_id).first()
            if dept:
                dept_name = dept.name
        
        result.append({
            'order_id': order.order_id,
            'patient_id': patient.patient_id if patient else "",
            'patient_name': patient.name if patient else "",
            'department': dept_name or "",
            'time': order.time or "",
            'status': order.status
        })
    
    today_total = len(orders)
    pending = sum(1 for o in orders if o.status == 'pending')
    ongoing = sum(1 for o in orders if o.status == 'ongoing')
    finished = sum(1 for o in orders if o.status == 'finished')
    
    return {
        "code": 0,
        "data": result,
        "kpi": {
            "today_total": today_total,
            "pending": pending,
            "ongoing": ongoing,
            "finished": finished
        }
    }


@app.put("/api/orders/{order_id}/start")
async def start_order(order_id: str, token_info: Dict[str, Any] = Depends(limit_authenticated_write)):
    db = next(get_db())
    order = require_order_access(db, order_id, token_info, write=True)
    
    if order.status != 'pending':
        return {"code": 400, "msg": "Order is not pending"}
    
    try:
        order.status = 'ongoing'
        db.commit()
        return {"code": 0, "data": {"order_id": order_id, "status": "ongoing"}}
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Start order error: {str(e)}")
        return {"code": 500, "msg": "更新订单失败，请稍后重试"}


@app.put("/api/orders/{order_id}/finish")
async def finish_order(order_id: str, input_data: FinishOrderInput, token_info: Dict[str, Any] = Depends(limit_authenticated_write)):
    db = next(get_db())
    order = require_order_access(db, order_id, token_info, write=True)
    
    if order.status not in ['pending', 'ongoing']:
        return {"code": 400, "msg": "Order cannot be finished"}
    
    try:
        order.status = 'finished'
        order.syndrome = input_data.syndrome
        order.prescription = input_data.prescription
        order.ingredients = input_data.ingredients
        order.advice = input_data.advice
        record_id = f'R{datetime.now().strftime("%Y%m%d%H%M%S")}{uuid.uuid4().hex[:8]}'
        record = ApiClinicRecord(
            record_id=record_id,
            patient_id=order.patient_id,
            doctor_id=order.doctor_id,
            order_id=order.id,
            chief_complaint=input_data.therapy or order.chief_complaint or "",
            history_of_present_illness=input_data.precautions or order.present_illness or "",
            tongue=order.tongue or "",
            pulse=order.pulse or "",
            zheng_type=input_data.syndrome,
            prescription=input_data.prescription,
            ingredients=input_data.ingredients,
            advice=input_data.advice
        )
        db.add(record)
        db.commit()
        
        return {"code": 0, "data": {"order_id": order_id, "status": "finished"}}
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Finish order error: {str(e)}")
        return {"code": 500, "msg": "完成订单失败，请稍后重试"}


@app.put("/api/orders/{order_id}/save")
async def save_order(order_id: str, input_data: SaveOrderInput, token_info: Dict[str, Any] = Depends(limit_authenticated_write)):
    db = next(get_db())
    order = require_order_access(db, order_id, token_info, write=True)
    
    if order.status not in ['pending', 'ongoing']:
        return {"code": 400, "msg": "Order cannot be saved"}
    
    try:
        if order.status == 'pending':
            order.status = 'ongoing'
        
        update_data = input_data.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(order, key, value)
        
        db.commit()
        return {"code": 0, "data": {"order_id": order_id, "status": order.status}}
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Save order error: {str(e)}")
        return {"code": 500, "msg": "保存订单失败，请稍后重试"}


@app.post("/api/orders/{order_id}/diagnosis")
async def submit_diagnosis(order_id: str, input_data: DiagnosisInput, token_info: Dict[str, Any] = Depends(limit_authenticated_write)):
    db = next(get_db())
    order = require_order_access(db, order_id, token_info, write=True)
    
    try:
        order.chief_complaint = input_data.chief_complaint
        order.present_illness = input_data.present_illness
        order.tongue = input_data.tongue
        order.pulse = input_data.pulse
        order.symptoms = input_data.symptoms
        order.signs = input_data.signs
        order.other = input_data.other
        db.commit()
        
        return {"code": 0, "data": {"order_id": order_id}}
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Submit diagnosis error: {str(e)}")
        return {"code": 500, "msg": "提交诊断失败，请稍后重试"}



@app.get("/api/orders/{order_id}/patient")
async def get_order_patient(order_id: str, token_info: Dict[str, Any] = Depends(require_auth)):
    """通过order_id查询订单关联的patient_id"""
    db = next(get_db())
    order = require_order_access(db, order_id, token_info)

    return {"code": 0, "data": {"order_id": order_id, "patient_id": order.patient_id}}


@app.get("/api/patients/{patient_id}/basic")
async def get_patient_basic(patient_id: int, token_info: Dict[str, Any] = Depends(require_auth)):
    """通过患者id查询基本信息（gender、age、allergy_history）"""
    require_role(token_info, "doctor")

    db = next(get_db())
    patient = db.query(ApiPatient).filter(ApiPatient.id == patient_id).first()
    if not patient:
        return {"code": 404, "msg": "Patient not found"}

    return {
        "code": 0,
        "data": {
            "id": patient_id,
            "gender": patient.gender,
            "age": patient.age,
            "allergy_history": patient.allergy_history,
        }
    }


@app.get("/api/records")
async def search_records(name: str = "", patient_id: str = "", syndrome: str = "", 
                         date_from: str = "", date_to: str = "", page: int = 1, page_size: int = 20,
                         token_info: Dict[str, Any] = Depends(require_auth)):
    require_role(token_info, "doctor")
    if page < 1 or not 1 <= page_size <= 100:
        raise HTTPException(status_code=422, detail="分页参数无效")
    db = next(get_db())
    query = db.query(ApiClinicRecord, ApiPatient).join(ApiPatient, ApiPatient.id == ApiClinicRecord.patient_id)
    if name:
        query = query.filter(ApiPatient.name.contains(name[:100]))
    if patient_id:
        query = query.filter(ApiPatient.patient_id == patient_id[:50])
    if syndrome:
        query = query.filter(ApiClinicRecord.zheng_type.contains(syndrome[:100]))
    if date_from:
        query = query.filter(ApiClinicRecord.visit_date >= datetime.strptime(date_from, "%Y-%m-%d"))
    if date_to:
        query = query.filter(ApiClinicRecord.visit_date < datetime.strptime(date_to, "%Y-%m-%d") + timedelta(days=1))
    total = query.count()
    rows = query.order_by(ApiClinicRecord.visit_date.desc()).offset((page - 1) * page_size).limit(page_size).all()
    filtered = []
    for record, patient in rows:
        filtered.append({
            'record_id': record.record_id,
            'patient': {
                'patient_id': patient.patient_id if patient else "",
                'name': patient.name if patient else ""
            },
            'syndrome': record.zheng_type or "",
            'prescription': record.prescription or "",
            'therapy': record.chief_complaint or "",
            'precautions': record.history_of_present_illness or "",
            'date': record.visit_date.isoformat() if record.visit_date else ""
        })
    
    return {
        "code": 0,
        "data": {
            "list": filtered,
            "total": total,
            "page": page,
            "page_size": page_size
        }
    }


@app.get("/api/records/{record_id}")
async def get_record_detail(record_id: str, token_info: Dict[str, Any] = Depends(require_auth)):
    require_role(token_info, "doctor")
    db = next(get_db())
    
    record = db.query(ApiClinicRecord).filter(ApiClinicRecord.record_id == record_id).first()
    if not record:
        return {"code": 404, "msg": "Record not found"}
    
    patient = db.query(ApiPatient).filter(ApiPatient.id == record.patient_id).first()
    doctor = db.query(ApiDoctor).filter(ApiDoctor.id == record.doctor_id).first()
    
    data = {
        'record_id': record.record_id,
        'patient': {
            'patient_id': patient.patient_id if patient else "",
            'name': patient.name if patient else "",
            'gender': patient.gender if patient else "",
            'age': patient.age if patient else 0
        },
        'doctor': {
            'doctor_id': doctor.doctor_id if doctor else "",
            'name': doctor.name if doctor else ""
        },
        'chief_complaint': record.chief_complaint or "",
        'present_illness': record.history_of_present_illness or "",
        'tongue': record.tongue or "",
        'pulse': record.pulse or "",
        'syndrome': record.zheng_type or "",
        'treatment_principle': record.treatment_principle or "",
        'prescription': record.prescription or "",
        'ingredients': record.ingredients or [],
        'advice': record.advice or "",
        'date': record.visit_date.isoformat() if record.visit_date else ""
    }
    
    return {"code": 0, "data": data}


@app.get("/api/patient/{patient_id}/history")
async def get_patient_history(patient_id: str, token_info: Dict[str, Any] = Depends(require_auth)):
    require_role(token_info, "doctor")
    db = next(get_db())
    
    patient = db.query(ApiPatient).filter(ApiPatient.patient_id == patient_id).first()
    if not patient:
        return {"code": 404, "msg": "Patient not found"}
    
    records = db.query(ApiClinicRecord).filter(ApiClinicRecord.patient_id == patient.id).all()
    
    history_syndromes = []
    for record in records:
        history_syndromes.append({
            'date': record.visit_date.strftime('%Y-%m-%d') if record.visit_date else "",
            'syndrome': record.zheng_type or "",
            'prescription': record.prescription or ""
        })
    
    return {
        "code": 0,
        "data": {
            "patient_id": patient_id,
            "history_syndromes": history_syndromes,
            "allergy_history": patient.allergy_history or []
        }
    }


@app.get("/api/patient/diagnosis-history")
async def get_diagnosis_history(authorization: str = Header(None), status: str = "all"):
    token_info = parse_token(authorization)
    if not token_info or token_info.get('role') != 'patient':
        return {"code": 401, "msg": "Unauthorized"}
    
    db = next(get_db())
    patient = db.query(ApiPatient).filter(ApiPatient.patient_id == token_info['role_id']).first()
    if not patient:
        return {"code": 404, "msg": "Patient not found"}
    
    orders = db.query(ApiOrder).filter(ApiOrder.patient_id == patient.id).order_by(
        ApiOrder.created_at.desc(), ApiOrder.id.desc()
    ).all()
    
    if status != 'all':
        orders = [o for o in orders if o.status == status]
    
    result = []
    for order in orders:
        doctor = db.query(ApiDoctor).filter(ApiDoctor.id == order.doctor_id).first()
        advice_list = order.advice.split(',') if order.advice else []
        
        result.append({
            'order_id': order.order_id,
            'doctor': {
                'doctor_id': doctor.doctor_id if doctor else "",
                'name': doctor.name if doctor else ""
            },
            'department': order.department or "",
            # 保留 date 兼容旧前端；新增字段明确区分下单时间与预约时间。
            'date': order.created_at.isoformat() if order.created_at else "",
            'created_at': order.created_at.isoformat() if order.created_at else "",
            'appointment_date': order.date.isoformat() if order.date else "",
            'appointment_time': order.time or "",
            'status': order.status,
            'symptoms_summary': ', '.join(order.symptoms) if order.symptoms else '',
            'diagnosis_summary': f"{order.syndrome}, {order.prescription}" if order.syndrome else '',
            'advice_list': advice_list
        })
    
    return {"code": 0, "data": result}


@app.get("/api/orders/{order_id}")
async def get_order_detail(order_id: str, token_info: Dict[str, Any] = Depends(require_auth)):
    db = next(get_db())
    order = require_order_access(db, order_id, token_info)
    
    patient = db.query(ApiPatient).filter(ApiPatient.id == order.patient_id).first()
    doctor = db.query(ApiDoctor).filter(ApiDoctor.id == order.doctor_id).first()
    
    data = {
        'order_id': order.order_id,
        'patient': {
            'patient_id': patient.patient_id if patient else "",
            'name': patient.name if patient else "",
            'gender': patient.gender if patient else "",
            'age': patient.age if patient else 0
        },
        'doctor': {
            'doctor_id': doctor.doctor_id if doctor else "",
            'name': doctor.name if doctor else ""
        },
        'chief_complaint': order.chief_complaint or "",
        'present_illness': order.present_illness or "",
        'tongue': order.tongue or "",
        'pulse': order.pulse or "",
        'syndrome': order.syndrome or "",
        'prescription': order.prescription or "",
        'ingredients': order.ingredients or [],
        'advice': order.advice or "",
        'date': order.created_at.isoformat() if order.created_at else "",
        'created_at': order.created_at.isoformat() if order.created_at else "",
        'appointment_date': order.date.isoformat() if order.date else "",
        'appointment_time': order.time or "",
    }
    
    return {"code": 0, "data": data}


@app.get("/api/patient/latest-diagnosis")
async def get_latest_diagnosis(authorization: str = Header(None)):
    token_info = parse_token(authorization)
    if not token_info or token_info.get('role') != 'patient':
        return {"code": 401, "msg": "Unauthorized"}
    
    db = next(get_db())
    patient = db.query(ApiPatient).filter(ApiPatient.patient_id == token_info['role_id']).first()
    if not patient:
        return {"code": 404, "msg": "Patient not found"}
    
    finished_orders = db.query(ApiOrder).filter(
        ApiOrder.patient_id == patient.id,
        ApiOrder.status == 'finished'
    ).order_by(ApiOrder.updated_at.desc()).all()
    
    if not finished_orders:
        return {"code": 0, "data": None}
    
    latest_order = finished_orders[0]
    advice_list = latest_order.advice.split(',') if latest_order.advice else []
    
    data = {
        'order_id': latest_order.order_id,
        'syndrome': latest_order.syndrome or "",
        'prescription': latest_order.prescription or "",
        'department': latest_order.department or "",
        'diagnosis_basis': f"根据您症状，辨证为{latest_order.syndrome}" if latest_order.syndrome else "",
        'advice_list': advice_list,
        'sync_time': latest_order.updated_at.isoformat() if latest_order.updated_at else ""
    }
    
    return {"code": 0, "data": data}


@app.get("/api/doctor/profile")
async def get_doctor_profile(authorization: str = Header(None)):
    token_info = parse_token(authorization)
    if not token_info or token_info.get('role') != 'doctor':
        return {"code": 401, "msg": "Unauthorized"}
    
    db = next(get_db())
    doctor = db.query(ApiDoctor).filter(ApiDoctor.doctor_id == token_info['role_id']).first()
    if not doctor:
        return {"code": 404, "msg": "Doctor profile not found"}
    
    department_name = ""
    if doctor.department_id:
        dept = db.query(ApiDepartment).filter(ApiDepartment.id == doctor.department_id).first()
        if dept:
            department_name = dept.name
    
    return {
        "code": 0,
        "data": {
            "doctor_id": doctor.doctor_id,
            "name": doctor.name,
            "role": "doctor",
            "username": doctor.username,
            "phone": doctor.phone or "",
            "department": department_name,
            "duty_time": doctor.duty_time or "",
            "specialty": doctor.specialty or "",
            "bio": doctor.bio or ""
        }
    }


@app.put("/api/doctor/profile")
async def update_doctor_profile(input_data: DoctorProfileInput, token_info: Dict[str, Any] = Depends(limit_authenticated_write)):
    require_role(token_info, "doctor")
    
    db = next(get_db())
    doctor = db.query(ApiDoctor).filter(ApiDoctor.doctor_id == token_info['role_id']).first()
    if not doctor:
        return {"code": 404, "msg": "Doctor profile not found"}
    
    try:
        update_data = input_data.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(doctor, key, value)
        db.commit()
        return {"code": 0, "data": None}
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Update doctor profile error: {str(e)}")
        return {"code": 500, "msg": "资料更新失败，请稍后重试"}


@app.get("/api/admin/users")
async def get_users(_: Dict[str, Any] = Depends(require_auth)):
    """管理后台尚未实现独立管理员角色，默认关闭，避免普通医生越权。"""
    raise HTTPException(status_code=403, detail="管理功能暂未开放")



@app.post("/api/agent/chat")
async def agent_chat(input_data: AgentInput, token_info: Dict[str, Any] = Depends(limit_agent_request)):
    try:
        if not input_data.user_input or len(input_data.user_input) > 4000:
            raise HTTPException(status_code=422, detail="问诊文本长度必须为 1-4000 个字符")
        db = next(get_db())
        patient_id = input_data.patient_id or token_info.get("role_id")
        patient = require_agent_patient_access(db, patient_id, token_info)
        patient_profile = get_patient_profile(db, patient.patient_id)
        sid = input_data.session_id or f"S_{patient_id}_{int(time.time())}"
        raw = await remote_agent_client.chat_async(
            session_id=sid,
            patient_id=patient_id,
            user_input=input_data.user_input,
            mode=input_data.mode,
            scene=input_data.scene,
            patient_profile=patient_profile,
        )
        
        response_data = {
            "status": raw.get("status", "done"),
            "response": raw.get("response", ""),
            "session_id": sid,
            "finish": raw.get("finish", False),
        }
        
        if raw.get("status") == "diagnosed" and "diagnosis_result" in raw:
            response_data["diagnosis"] = raw["diagnosis_result"]
        elif raw.get("status") == "asking":
            response_data["ask_round"] = raw.get("ask_round", 1)
        if isinstance(raw.get("trace"), dict):
            response_data["trace"] = raw["trace"]
        
        return {"code": 0, "data": response_data}
    except HTTPException:
        raise
    except Exception:
        logger.exception("agent_chat failed")
        raise HTTPException(status_code=502, detail="智能助手暂不可用")


@app.post("/api/agent/chat/stream")
async def agent_chat_stream(input_data: AgentInput, token_info: Dict[str, Any] = Depends(limit_agent_request)):
    try:
        if not input_data.user_input or len(input_data.user_input) > 4000:
            raise HTTPException(status_code=422, detail="问诊文本长度必须为 1-4000 个字符")
        db = next(get_db())
        patient_id = input_data.patient_id or token_info.get("role_id")
        patient = require_agent_patient_access(db, patient_id, token_info)
        patient_profile = get_patient_profile(db, patient.patient_id)
        sid = input_data.session_id or f"S_{patient_id}_{int(time.time())}"
        async def generate():
            try:
                async for chunk in remote_agent_client.stream_chat(
                    session_id=sid,
                    patient_id=patient_id,
                    user_input=input_data.user_input,
                    mode=input_data.mode,
                    scene=input_data.scene,
                    patient_profile=patient_profile,
                ):
                    yield chunk
            except Exception:
                logger.exception("agent_chat_stream failed")
                yield f"data: {json.dumps({'code': 502, 'data': {'status': 'error', 'response': '智能助手暂不可用', 'finish': False}}, ensure_ascii=False)}\n\n"
                yield "data: [DONE]\n\n"
        
        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Content-Type": "text/event-stream",
                "X-Accel-Buffering": "no",
            }
        )
    except HTTPException:
        raise
    except Exception:
        logger.exception("agent_chat_stream initialization failed")
        raise HTTPException(status_code=502, detail="智能助手暂不可用")


@app.post("/api/knowledge/case")
async def add_case_api(input_data: AddCaseInput, token_info: Dict[str, Any] = Depends(limit_authenticated_write)):
    """由当前登录医生创建医案，并写入独立的 case_neo4j 图谱。"""
    require_role(token_info, "doctor")
    db = next(get_db())
    doctor = current_doctor(db, token_info)

    result = add_case(
        title=input_data.title,
        summary=input_data.summary,
        raw_text=input_data.rawText,
        source_url=input_data.sourceUrl,
        publish_date=input_data.publishDate,
        # 录入人和关联医生必须由认证上下文决定，不能信任前端传值。
        author=doctor.name,
        channel=input_data.channel,
        diseases=_convert_entity_list(input_data.diseases),
        syndromes=_convert_entity_list(input_data.syndromes),
        symptoms=_convert_entity_list(input_data.symptoms),
        formulas=_convert_entity_list(input_data.formulas),
        treatment_methods=_convert_entity_list(input_data.treatmentMethods),
        doctors=[{"name": doctor.name, "id": doctor.doctor_id}],
    )
    if not result.get("success"):
        logger.warning("case_write_failed doctor_id=%s", doctor.doctor_id)
        raise HTTPException(status_code=502, detail="医案写入失败，请稍后重试")

    return {
        "code": 0,
        "data": {
            "caseId": result.get("caseId"),
            "sourceId": result.get("sourceId"),
            "linked": result.get("linked", {}),
        },
    }


@app.get("/api/knowledge/case/doctor")
def get_doctor_cases(
    doctor: str = None,
    doctor_id: str = None,
    limit: int = 10,
    authorization: str = Header(None)
):
    """按名医名字或ID检索相关医案，与 neo4j_case README.md 中 searchByDoctor/searchByDoctorId 一致"""
    try:
        token_info = parse_token(authorization)
        if not token_info or token_info.get('role') != 'doctor':
            return {"code": 401, "msg": "Unauthorized"}
        
        if not doctor and not doctor_id:
            return {"code": 400, "msg": "doctor 或 doctor_id 至少传一个"}
        
        result = search_by_doctor(doctor=doctor, doctor_id=doctor_id, limit=min(limit, 50))
        
        if result.get("success"):
            return {"code": 0, "data": result["cases"]}
        else:
            return {"code": 400, "msg": result.get("message", "查询失败")}
    except Exception as e:
        logger.error(f"get_doctor_cases error: {str(e)}")
        return {"code": 500, "msg": "医案查询失败，请稍后重试"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
