import os
import sys
import logging
import time
import uuid
import re
import json
import psutil
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Union

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "traditional_medical_agent"))

import uvicorn
from fastapi import FastAPI, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Text, Date, DateTime, DECIMAL, JSON, Boolean, ForeignKey, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from sqlalchemy.exc import SQLAlchemyError
from dotenv import load_dotenv

from remote_agent_client import remote_agent_client
from traditional_medical_agent.tcm_agent import tcm_agent_chat
from traditional_medical_agent.kg_service import search_by_doctor


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


TOKENS = {}


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def generate_token(username: str, role: str, role_id: str) -> str:
    token = f"token_{uuid.uuid4().hex}"
    TOKENS[token] = {
        'username': username,
        'role': role,
        'role_id': role_id,
        'expire_at': datetime.now() + timedelta(hours=24)
    }
    return token


def parse_token(authorization: str) -> dict:
    if not authorization or not authorization.startswith('Bearer '):
        return None
    token = authorization.replace('Bearer ', '')
    if token not in TOKENS:
        return None
    if TOKENS[token]['expire_at'] < datetime.now():
        del TOKENS[token]
        return None
    return TOKENS[token]


def get_patient_profile(db: Session, patient_id: str) -> Dict[str, Any]:
    patient = db.query(ApiPatient).filter(ApiPatient.patient_id == patient_id).first()
    if patient:
        return {
            "patient_id": patient.patient_id,
            "allergy_history": {"herbs": patient.allergy_history or []}
        }
    return {"patient_id": patient_id, "allergy_history": {"herbs": []}}


class RegisterInput(BaseModel):
    username: str
    password: str
    confirm_password: str
    name: Optional[str] = None
    phone: Optional[str] = None


class LoginInput(BaseModel):
    username: str
    password: str


class PatientProfileInput(BaseModel):
    name: Optional[str] = None
    password: Optional[str] = None
    gender: Optional[str] = None
    birth_date: Optional[str] = None
    age: Optional[int] = None
    phone: Optional[str] = None
    allergy_history: Optional[List[str]] = None


class DoctorProfileInput(BaseModel):
    name: Optional[str] = None
    password: Optional[str] = None
    title: Optional[str] = None
    hospital: Optional[str] = None
    department_id: Optional[int] = None
    license_number: Optional[str] = None
    specialty: Optional[str] = None
    experience: Optional[int] = None
    phone: Optional[str] = None
    duty_time: Optional[str] = None
    bio: Optional[str] = None
    description: Optional[str] = None


class AgentInput(BaseModel):
    session_id: Optional[str] = None
    patient_id: Optional[str] = None
    user_input: str
    mode: str = "normal"
    scene: str = "guide"
    patient_profile: Optional[Dict[str, Any]] = None
    therapy: Optional[str] = None        # 疗法（存入 api_clinicrecord.chief_complaint）
    precautions: Optional[str] = None    # 注意事项（存入 api_clinicrecord.history_of_present_illness）


class CreateOrderInput(BaseModel):
    patient_id: str
    doctor_id: str
    department: str
    date: str
    time: str
    source: str = "direct"


class FinishOrderInput(BaseModel):
    syndrome: str
    prescription: str
    ingredients: List[str]
    advice: str
    therapy: Optional[str] = None        # 疗法（存入 api_clinicrecord.chief_complaint）
    precautions: Optional[str] = None    # 注意事项（存入 api_clinicrecord.history_of_present_illness）


class SaveOrderInput(BaseModel):
    syndrome: Optional[str] = None
    prescription: Optional[str] = None
    ingredients: Optional[List[str]] = None
    advice: Optional[str] = None
    therapy: Optional[str] = None        # 疗法
    precautions: Optional[str] = None    # 注意事项


class DiagnosisInput(BaseModel):
    chief_complaint: str
    present_illness: str
    tongue: str
    pulse: str
    symptoms: List[str]
    signs: str
    other: str


class EntityWithNameId(BaseModel):
    """实体节点，支持 name 和可选的 id"""
    name: str
    id: Optional[str] = None


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
    title: str
    summary: Optional[str] = None
    rawText: Optional[str] = None
    sourceUrl: Optional[str] = None
    publishDate: Optional[str] = None
    author: Optional[str] = None
    channel: Optional[str] = None
    diseases: Optional[Union[str, List[str], List[EntityWithNameId]]] = None
    syndromes: Optional[Union[str, List[str], List[EntityWithNameId]]] = None
    symptoms: Optional[Union[str, List[str], List[EntityWithNameId]]] = None
    formulas: Optional[Union[str, List[str], List[EntityWithNameId]]] = None
    treatmentMethods: Optional[Union[str, List[str], List[EntityWithNameId]]] = None
    doctors: Optional[Union[str, List[str], List[EntityWithNameId]]] = None


app = FastAPI(title="中医药诊疗智能体 API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
async def get_patient_basic_by_patient_id(patient_id: str, authorization: str = Header(None)):
    """通过patient_id（业务ID）查询患者基本信息（gender、age、allergy_history）"""
    token_info = parse_token(authorization)
    if not token_info:
        return {"code": 401, "msg": "Unauthorized"}

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
        return {"code": 500, "msg": f"Database connection failed: {str(e)}"}


@app.post("/api/auth/register")
async def register(input_data: RegisterInput):
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
        return {"code": 500, "msg": str(e)}


@app.post("/api/auth/login")
async def login(input_data: LoginInput):
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


@app.post("/api/doctor/auth/login")
async def doctor_login(input_data: LoginInput):
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
async def get_patient_profile_api(authorization: str = Header(None)):
    token_info = parse_token(authorization)
    if not token_info or token_info.get('role') != 'patient':
        return {"code": 401, "msg": "Unauthorized"}
    
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
async def update_patient_profile(input_data: PatientProfileInput, authorization: str = Header(None)):
    token_info = parse_token(authorization)
    if not token_info or token_info.get('role') != 'patient':
        return {"code": 401, "msg": "Unauthorized"}
    
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
        return {"code": 500, "msg": str(e)}


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
        ApiSchedule.status == 'available'
    ).all()
    
    available_slots = []
    for schedule in schedules:
        if isinstance(schedule.start_time, datetime):
            start_hour = schedule.start_time.hour
            end_hour = schedule.end_time.hour
        elif isinstance(schedule.start_time, timedelta):
            start_hour = schedule.start_time.seconds // 3600
            end_hour = schedule.end_time.seconds // 3600
        else:
            start_str = str(schedule.start_time)
            end_str = str(schedule.end_time)
            start_hour = int(start_str.split(':')[0])
            end_hour = int(end_str.split(':')[0])
        for hour in range(start_hour, end_hour):
            available_slots.append(f"{hour:02d}:00")
    
    return {
        "code": 0,
        "data": {
            "doctor_id": doctor_id,
            "date": date,
            "available_slots": available_slots
        }
    }


@app.post("/api/orders")
async def create_order(input_data: CreateOrderInput, authorization: str = Header(None)):
    token_info = parse_token(authorization)
    logger.info(f"create_order: authorization={authorization}, token_info={token_info}, patient_id={input_data.patient_id}")
    if not token_info:
        logger.error(f"create_order: token not found or invalid, authorization={authorization}")
        return {"code": 401, "msg": "Unauthorized"}
    if token_info.get('role') != 'patient':
        logger.error(f"create_order: role is not patient, role={token_info.get('role')}")
        return {"code": 401, "msg": "Unauthorized"}
    
    db = next(get_db())
    patient = db.query(ApiPatient).filter(ApiPatient.patient_id == input_data.patient_id).first()
    if not patient:
        return {"code": 404, "msg": "Patient not found"}
    
    doctor = db.query(ApiDoctor).filter(ApiDoctor.doctor_id == input_data.doctor_id).first()
    if not doctor:
        return {"code": 404, "msg": "Doctor not found"}
    
    try:
        order_id = f'O{datetime.now().strftime("%Y%m%d%H%M%S")}{uuid.uuid4().hex[:8]}'
        
        order = ApiOrder(
            order_id=order_id,
            patient_id=patient.id,
            doctor_id=doctor.id,
            department=input_data.department,
            date=datetime.strptime(input_data.date, '%Y-%m-%d').date(),
            time=input_data.time,
            source=input_data.source,
            status='pending'
        )
        db.add(order)
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
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Create order error: {str(e)}")
        return {"code": 500, "msg": str(e)}


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
    orders = db.query(ApiOrder).filter(ApiOrder.doctor_id == doctor.id).all()
    
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
async def start_order(order_id: str, authorization: str = Header(None)):
    token_info = parse_token(authorization)
    if not token_info:
        return {"code": 401, "msg": "Unauthorized"}
    
    db = next(get_db())
    
    order = db.query(ApiOrder).filter(ApiOrder.order_id == order_id).first()
    if not order:
        return {"code": 404, "msg": "Order not found"}
    
    if order.status != 'pending':
        return {"code": 400, "msg": "Order is not pending"}
    
    try:
        order.status = 'ongoing'
        db.commit()
        return {"code": 0, "data": {"order_id": order_id, "status": "ongoing"}}
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Start order error: {str(e)}")
        return {"code": 500, "msg": str(e)}


@app.put("/api/orders/{order_id}/finish")
async def finish_order(order_id: str, input_data: FinishOrderInput, authorization: str = Header(None)):
    token_info = parse_token(authorization)
    if not token_info:
        return {"code": 401, "msg": "Unauthorized"}
    
    db = next(get_db())
    
    order = db.query(ApiOrder).filter(ApiOrder.order_id == order_id).first()
    if not order:
        return {"code": 404, "msg": "Order not found"}
    
    if order.status not in ['pending', 'ongoing']:
        return {"code": 400, "msg": "Order cannot be finished"}
    
    try:
        order.status = 'finished'
        order.syndrome = input_data.syndrome
        order.prescription = input_data.prescription
        order.ingredients = input_data.ingredients
        order.advice = input_data.advice
        db.commit()
        
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
        return {"code": 500, "msg": str(e)}


@app.put("/api/orders/{order_id}/save")
async def save_order(order_id: str, input_data: SaveOrderInput, authorization: str = Header(None)):
    token_info = parse_token(authorization)
    if not token_info:
        return {"code": 401, "msg": "Unauthorized"}
    
    db = next(get_db())
    
    order = db.query(ApiOrder).filter(ApiOrder.order_id == order_id).first()
    if not order:
        return {"code": 404, "msg": "Order not found"}
    
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
        return {"code": 500, "msg": str(e)}


@app.post("/api/orders/{order_id}/diagnosis")
async def submit_diagnosis(order_id: str, input_data: DiagnosisInput, authorization: str = Header(None)):
    token_info = parse_token(authorization)
    if not token_info:
        return {"code": 401, "msg": "Unauthorized"}
    
    db = next(get_db())
    
    order = db.query(ApiOrder).filter(ApiOrder.order_id == order_id).first()
    if not order:
        return {"code": 404, "msg": "Order not found"}
    
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
        return {"code": 500, "msg": str(e)}



@app.get("/api/orders/{order_id}/patient")
async def get_order_patient(order_id: str, authorization: str = Header(None)):
    """通过order_id查询订单关联的patient_id"""
    token_info = parse_token(authorization)
    if not token_info:
        return {"code": 401, "msg": "Unauthorized"}

    db = next(get_db())
    order = db.query(ApiOrder).filter(ApiOrder.order_id == order_id).first()
    if not order:
        return {"code": 404, "msg": "Order not found"}

    return {"code": 0, "data": {"order_id": order_id, "patient_id": order.patient_id}}


@app.get("/api/patients/{patient_id}/basic")
async def get_patient_basic(patient_id: int, authorization: str = Header(None)):
    """通过患者id查询基本信息（gender、age、allergy_history）"""
    token_info = parse_token(authorization)
    if not token_info:
        return {"code": 401, "msg": "Unauthorized"}

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
                         date_from: str = "", date_to: str = "", page: int = 1, page_size: int = 20):
    db = next(get_db())
    
    records = db.query(ApiClinicRecord).all()
    
    filtered = []
    for record in records:
        patient = db.query(ApiPatient).filter(ApiPatient.id == record.patient_id).first()
        
        if name and patient and name not in patient.name:
            continue
        if patient_id:
            p = db.query(ApiPatient).filter(ApiPatient.patient_id == patient_id).first()
            if p and record.patient_id != p.id:
                continue
        if syndrome and syndrome not in (record.zheng_type or ""):
            continue
        
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
    
    total = len(filtered)
    start = (page - 1) * page_size
    end = start + page_size
    
    return {
        "code": 0,
        "data": {
            "list": filtered[start:end],
            "total": total,
            "page": page,
            "page_size": page_size
        }
    }


@app.get("/api/records/{record_id}")
async def get_record_detail(record_id: str):
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
async def get_patient_history(patient_id: str):
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
    
    orders = db.query(ApiOrder).filter(ApiOrder.patient_id == patient.id).all()
    
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
            'date': order.created_at.isoformat() if order.created_at else "",
            'status': order.status,
            'symptoms_summary': ', '.join(order.symptoms) if order.symptoms else '',
            'diagnosis_summary': f"{order.syndrome}, {order.prescription}" if order.syndrome else '',
            'advice_list': advice_list
        })
    
    return {"code": 0, "data": result}


@app.get("/api/orders/{order_id}")
async def get_order_detail(order_id: str):
    db = next(get_db())
    
    order = db.query(ApiOrder).filter(ApiOrder.order_id == order_id).first()
    if not order:
        return {"code": 404, "msg": "Order not found"}
    
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
        'date': order.created_at.isoformat() if order.created_at else ""
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
            "password": doctor.password,
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
async def update_doctor_profile(input_data: DoctorProfileInput, authorization: str = Header(None)):
    token_info = parse_token(authorization)
    if not token_info or token_info.get('role') != 'doctor':
        return {"code": 401, "msg": "Unauthorized"}
    
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
        return {"code": 500, "msg": str(e)}


@app.get("/api/admin/users")
async def get_users(authorization: str = Header(None)):
    token_info = parse_token(authorization)
    if not token_info or token_info.get('role') != 'doctor':
        return {"code": 401, "msg": "Unauthorized"}
    
    db = next(get_db())
    doctor = db.query(ApiDoctor).filter(ApiDoctor.doctor_id == token_info['role_id']).first()
    if not doctor:
        return {"code": 401, "msg": "Unauthorized"}
    
    result = []
    
    patients = db.query(ApiPatient).all()
    for p in patients:
        result.append({
            'id': p.id,
            'username': p.username,
            'role': 'patient',
            'patient_id': p.patient_id,
            'name': p.name
        })
    
    doctors = db.query(ApiDoctor).all()
    for d in doctors:
        dept_name = ""
        if d.department_id:
            dept = db.query(ApiDepartment).filter(ApiDepartment.id == d.department_id).first()
            if dept:
                dept_name = dept.name
        result.append({
            'id': d.id,
            'username': d.username,
            'role': 'doctor',
            'doctor_id': d.doctor_id,
            'name': d.name,
            'department': dept_name
        })
    
    return {"code": 0, "data": result}



@app.post("/api/agent/chat")
def agent_chat(input_data: AgentInput, authorization: str = Header(None)):
    try:
        db = next(get_db())
        token_info = parse_token(authorization)
        
        patient_id = input_data.patient_id
        if not patient_id and token_info and token_info.get('role') == 'patient':
            patient = db.query(ApiPatient).filter(ApiPatient.patient_id == token_info['role_id']).first()
            if patient:
                patient_id = patient.patient_id
        
        if not patient_id:
            patient_id = 'P001'
        
        if not input_data.patient_profile:
            input_data.patient_profile = get_patient_profile(db, patient_id)
        
        sid = input_data.session_id or f"S_{patient_id}_{int(time.time())}"
        
        logger.info(f"Using tcm_agent for chat, session: {sid}")
        raw = tcm_agent_chat(
            session_id=sid,
            patient_id=patient_id,
            user_input=input_data.user_input,
            mode=input_data.mode,
            scene=input_data.scene,
            patient_profile=input_data.patient_profile
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
        
        return {"code": 0, "data": response_data}
    except Exception as e:
        logger.error(f"agent_chat error: {str(e)}")
        return {"code": 500, "msg": str(e)}


@app.post("/api/agent/chat/stream")
def agent_chat_stream(input_data: AgentInput, authorization: str = Header(None)):
    try:
        db = next(get_db())
        token_info = parse_token(authorization)
        
        patient_id = input_data.patient_id
        if not patient_id and token_info and token_info.get('role') == 'patient':
            patient = db.query(ApiPatient).filter(ApiPatient.patient_id == token_info['role_id']).first()
            if patient:
                patient_id = patient.patient_id
        
        if not patient_id:
            patient_id = 'P001'
        
        if not input_data.patient_profile:
            input_data.patient_profile = get_patient_profile(db, patient_id)
        
        sid = input_data.session_id or f"S_{patient_id}_{int(time.time())}"
        
        logger.info(f"Using tcm_agent for streaming chat, session: {sid}")
        
        def generate():
            try:
                from traditional_medical_agent.tcm_agent import tcm_agent_stream_chat
                
                for chunk in tcm_agent_stream_chat(
                    session_id=sid,
                    patient_id=patient_id,
                    user_input=input_data.user_input,
                    mode=input_data.mode,
                    scene=input_data.scene,
                    patient_profile=input_data.patient_profile
                ):
                    yield chunk
            except Exception as e:
                logger.error(f"agent_chat_stream error: {str(e)}")
                yield f"data: {json.dumps({'code': 500, 'data': {'status': 'error', 'response': f'处理失败：{str(e)}', 'finish': False}}, ensure_ascii=False)}\n\n"
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
    except Exception as e:
        logger.error(f"agent_chat_stream init error: {str(e)}")
        return {"code": 500, "msg": str(e)}


@app.post("/api/knowledge/case")
async def add_case_api(input_data: AddCaseInput):
    try:
        from traditional_medical_agent.kg_service import add_case

        result = add_case(
            title=input_data.title,
            summary=input_data.summary,
            raw_text=input_data.rawText,
            source_url=input_data.sourceUrl,
            publish_date=input_data.publishDate,
            author=input_data.author,
            channel=input_data.channel,
            diseases=_convert_entity_list(input_data.diseases),
            syndromes=_convert_entity_list(input_data.syndromes),
            symptoms=_convert_entity_list(input_data.symptoms),
            formulas=_convert_entity_list(input_data.formulas),
            treatment_methods=_convert_entity_list(input_data.treatmentMethods),
            doctors=_convert_entity_list(input_data.doctors)
        )

        if result.get("success"):
            return {
                "code": 0,
                "data": {
                    "caseId": result.get("caseId"),
                    "sourceId": result.get("sourceId"),
                    "linked": result.get("linked", {})
                }
            }
        else:
            return {"code": 400, "msg": result.get("message", "写入失败")}
    except Exception as e:
        logger.error(f"add_case_api error: {str(e)}")
        return {"code": 500, "msg": str(e)}


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
        return {"code": 500, "msg": str(e)}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)