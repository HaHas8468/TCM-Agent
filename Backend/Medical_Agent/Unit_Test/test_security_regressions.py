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
