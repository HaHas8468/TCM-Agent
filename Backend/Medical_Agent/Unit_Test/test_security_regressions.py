"""无需连接外部服务的安全回归检查。"""

from pathlib import Path


BACKEND = Path(__file__).resolve().parents[1]


def test_gateway_no_longer_imports_agent_in_process():
    source = (BACKEND / "fastapi_app" / "main.py").read_text(encoding="utf-8")
    assert "from traditional_medical_agent.tcm_agent import" not in source
    assert "remote_agent_client.chat_async" in source


def test_order_writes_use_resource_authorization():
    source = (BACKEND / "fastapi_app" / "main.py").read_text(encoding="utf-8")
    for endpoint in ("start_order", "finish_order", "save_order", "submit_diagnosis"):
        start = source.index(f"def {endpoint}")
        body = source[start:start + 900]
        assert "require_order_access" in body


def test_neo4j_scripts_have_no_embedded_credentials():
    for relative in (
        "traditional_medical_agent/neo4j_main/knowledge_graph_query.js",
        "traditional_medical_agent/neo4j_case/neo4j_agent_api.js",
    ):
        source = (BACKEND / relative).read_text(encoding="utf-8")
        assert "DEFAULT_NEO4J_CONFIG" not in source
        assert "NEO4J_" in source


def test_agent_sessions_are_redis_backed_without_memory_saver():
    source = (BACKEND / "traditional_medical_agent" / "tcm_agent.py").read_text(encoding="utf-8")
    assert "from langgraph.checkpoint.memory import" not in source
    assert "class RedisSessionStore" in source


def test_case_write_is_limited_to_authenticated_doctors_and_uses_server_identity():
    source = (BACKEND / "fastapi_app" / "main.py").read_text(encoding="utf-8")
    kg_server = (BACKEND / "knowledge_graph_service" / "server.js").read_text(encoding="utf-8")
    env_example = (BACKEND / ".env.example").read_text(encoding="utf-8")

    start = source.index("async def add_case_api")
    body = source[start:start + 1800]
    assert 'require_role(token_info, "doctor")' in body
    assert "doctor = current_doctor(db, token_info)" in body
    assert "author=doctor.name" in body
    assert 'doctors=[{"name": doctor.name, "id": doctor.doctor_id}]' in body
    assert 'KG_ALLOW_CASE_WRITE=false' in env_example
    assert 'process.env.KG_ALLOW_CASE_WRITE === "true"' in kg_server
