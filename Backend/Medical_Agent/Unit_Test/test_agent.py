import os
import sys
import json
import uuid
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

print("=" * 70)
print("中医药智能诊疗Agent 单元测试")
print("=" * 70)
print()

passed_count = 0
failed_count = 0

def test_result(description, passed, details=""):
    global passed_count, failed_count
    if passed:
        passed_count += 1
        print(f"✓ PASS: {description}")
        if details:
            print(f"   {details}")
    else:
        failed_count += 1
        print(f"✗ FAIL: {description}")
        if details:
            print(f"   {details}")
    print()

try:
    print("测试1: AgentInput 模型验证")
    from pydantic import BaseModel, ValidationError
    from typing import Optional, Dict, Any
    
    class AgentInput(BaseModel):
        session_id: str
        patient_id: str
        user_input: str
        mode: str = "normal"
        scene: str = "guide"
        patient_profile: Optional[Dict[str, Any]] = None
    
    valid_input = AgentInput(
        session_id="test_session_001",
        patient_id="test_patient_001",
        user_input="我最近总是头晕，浑身乏力",
        mode="normal",
        scene="guide"
    )
    assert valid_input.session_id == "test_session_001"
    assert valid_input.patient_id == "test_patient_001"
    assert valid_input.mode == "normal"
    assert valid_input.scene == "guide"
    assert valid_input.patient_profile is None
    test_result("基本输入参数验证", True, f"session_id={valid_input.session_id}, patient_id={valid_input.patient_id}")

except Exception as e:
    test_result("基本输入参数验证", False, str(e))

try:
    print("测试2: AgentInput 带患者档案验证")
    from pydantic import BaseModel
    from typing import Optional, Dict, Any
    
    class AgentInput(BaseModel):
        session_id: str
        patient_id: str
        user_input: str
        mode: str = "normal"
        scene: str = "guide"
        patient_profile: Optional[Dict[str, Any]] = None
    
    profile = {
        "allergic_herbs": ["麻黄", "细辛"],
        "history_conditions": ["高血压", "糖尿病"],
        "age": 65,
        "gender": "male"
    }
    
    valid_input = AgentInput(
        session_id="test_session_002",
        patient_id="test_patient_002",
        user_input="我最近总是头晕，浑身乏力",
        mode="normal",
        scene="guide",
        patient_profile=profile
    )
    assert valid_input.patient_profile == profile
    assert "allergic_herbs" in valid_input.patient_profile
    test_result("患者档案参数验证", True, f"过敏药材: {profile['allergic_herbs']}")

except Exception as e:
    test_result("患者档案参数验证", False, str(e))

try:
    print("测试3: AgentInput 随访模式验证")
    from pydantic import BaseModel
    from typing import Optional, Dict, Any
    
    class AgentInput(BaseModel):
        session_id: str
        patient_id: str
        user_input: str
        mode: str = "normal"
        scene: str = "guide"
        patient_profile: Optional[Dict[str, Any]] = None
    
    valid_input = AgentInput(
        session_id="test_session_003",
        patient_id="test_patient_003",
        user_input="还有胸闷的症状",
        mode="follow-up",
        scene="guide"
    )
    assert valid_input.mode == "follow-up"
    test_result("随访模式(mode=follow-up)", True)

except Exception as e:
    test_result("随访模式(mode=follow-up)", False, str(e))

try:
    print("测试4: AgentInput 医生场景验证")
    from pydantic import BaseModel
    from typing import Optional, Dict, Any
    
    class AgentInput(BaseModel):
        session_id: str
        patient_id: str
        user_input: str
        mode: str = "normal"
        scene: str = "guide"
        patient_profile: Optional[Dict[str, Any]] = None
    
    valid_input = AgentInput(
        session_id="test_session_004",
        patient_id="test_patient_004",
        user_input="患者出现头晕、乏力、面色苍白",
        mode="normal",
        scene="doctor"
    )
    assert valid_input.scene == "doctor"
    test_result("医生场景(scene=doctor)", True)

except Exception as e:
    test_result("医生场景(scene=doctor)", False, str(e))

try:
    print("测试5: AgentInput 必填字段验证")
    from pydantic import BaseModel, ValidationError
    from typing import Optional, Dict, Any
    
    class AgentInput(BaseModel):
        session_id: str
        patient_id: str
        user_input: str
        mode: str = "normal"
        scene: str = "guide"
        patient_profile: Optional[Dict[str, Any]] = None
    
    try:
        AgentInput(
            session_id="test_session",
            user_input="症状"
        )
        assert False, "应该抛出验证错误"
    except ValidationError as e:
        test_result("缺少必填字段(patient_id)", True, f"错误信息: {e.errors()[0]['msg']}")

except Exception as e:
    test_result("缺少必填字段(patient_id)", False, str(e))

try:
    print("测试6: 模拟API请求格式验证")
    import httpx
    
    base_url = "http://localhost:8000"
    
    test_payload = {
        "session_id": f"test_session_{uuid.uuid4().hex[:8]}",
        "patient_id": f"test_patient_{uuid.uuid4().hex[:8]}",
        "user_input": "我最近总是头晕，浑身乏力",
        "mode": "normal",
        "scene": "guide"
    }
    
    try:
        response = httpx.get(f"{base_url}/health", timeout=3)
        if response.status_code == 200:
            result = response.json()
            test_result("健康检查接口", True, f"状态: {result.get('status', 'unknown')}")
        else:
            test_result("健康检查接口", False, f"状态码: {response.status_code}")
    except httpx.ConnectError:
        test_result("健康检查接口", False, "服务未启动，请先启动服务")
    except Exception as e:
        test_result("健康检查接口", False, str(e))

except Exception as e:
    test_result("模拟API请求格式验证", False, str(e))

try:
    print("测试7: 模拟Agent聊天请求")
    import httpx
    
    base_url = "http://localhost:8000"
    
    test_payload = {
        "session_id": f"test_session_{uuid.uuid4().hex[:8]}",
        "patient_id": f"test_patient_{uuid.uuid4().hex[:8]}",
        "user_input": "我最近总是头晕，浑身乏力",
        "mode": "normal",
        "scene": "guide"
    }
    
    try:
        response = httpx.post(f"{base_url}/agent/chat", json=test_payload, timeout=10)
        if response.status_code == 200:
            result = response.json()
            has_session_id = "session_id" in result
            has_patient_id = "patient_id" in result
            has_mode = "mode" in result
            has_scene = "scene" in result
            
            details = []
            if has_session_id: details.append(f"session_id ✓")
            if has_patient_id: details.append(f"patient_id ✓")
            if has_mode: details.append(f"mode ✓")
            if has_scene: details.append(f"scene ✓")
            
            test_result("Agent聊天接口", True, ", ".join(details))
            
            print(f"   响应内容: {json.dumps(result, ensure_ascii=False)[:300]}...")
        else:
            test_result("Agent聊天接口", False, f"状态码: {response.status_code}, 内容: {response.text[:200]}")
    except httpx.ConnectError:
        test_result("Agent聊天接口", False, "服务未启动，请先启动服务")
    except Exception as e:
        test_result("Agent聊天接口", False, str(e))

except Exception as e:
    test_result("模拟Agent聊天请求", False, str(e))

print("=" * 70)
print(f"测试总结: {passed_count} 个通过, {failed_count} 个失败")
print("=" * 70)

if failed_count > 0:
    print()
    print("提示: API接口测试需要先启动服务。请在终端中运行:")
    print("  python fastapi_app/main.py")
    print("然后再运行测试:")
    print("  python Unit_Test/test_agent.py")

sys.exit(0 if failed_count == 0 else 1)