"""第二阶段稳定性与安全回归测试，不依赖外部数据库或模型服务。"""

from pathlib import Path


BACKEND = Path(__file__).resolve().parents[1]


def test_rate_limit_uses_redis_counter_and_retry_after_contract():
    source = (BACKEND / "fastapi_app" / "rate_limit.py").read_text(encoding="utf-8")

    assert "client.incr(key)" in source
    assert "client.expire(key, RATE_WINDOW_SECONDS)" in source
    assert 'headers={"Retry-After": str(ceil(ttl))}' in source
    assert "限流服务暂不可用" in source


def test_runtime_paths_do_not_spawn_node_or_log_raw_consultation_data():
    kg_source = (BACKEND / "traditional_medical_agent" / "kg_service.py").read_text(encoding="utf-8")
    agent_source = (BACKEND / "traditional_medical_agent" / "tcm_agent.py").read_text(encoding="utf-8")

    assert "subprocess.run" not in kg_source
    assert "ThreadPoolExecutor" not in kg_source
    assert "print(" not in kg_source
    assert "print(" not in agent_source
    assert "user_input={user_input" not in agent_source
    assert "session_id={session_id}" not in agent_source
    assert '"response": f"处理失败：{str(e)}"' not in agent_source


def test_sync_chat_does_not_shadow_human_message_before_message_creation():
    source = (BACKEND / "traditional_medical_agent" / "tcm_agent.py").read_text(encoding="utf-8")
    start = source.index("def tcm_agent_chat(")
    body = source[start:]

    assert "from langchain_core.messages import SystemMessage, HumanMessage" not in body


def test_diagnosis_follow_up_uses_algorithm_style_history_extraction_and_merge():
    source = (BACKEND / "traditional_medical_agent" / "tcm_agent.py").read_text(encoding="utf-8")

    assert 'if intent == "diagnosis":' in source
    assert "new_si = _extract_symptoms_llm(state[\"user_input\"], history_str)" in source
    assert "merged_symptoms = list(set((existing_si.symptoms or []) + (new_si.symptoms or [])))" in source
    assert "对话历史：" in source
    assert "decision.user_explicit_stop or decision.user_refused or decision.force_diagnosis" in source


def test_knowledge_graph_is_an_internal_compose_service():
    compose = (BACKEND / "docker-compose.yml").read_text(encoding="utf-8")
    server = (BACKEND / "knowledge_graph_service" / "server.js").read_text(encoding="utf-8")

    assert "  kg:" in compose
    assert "expose: [\"3000\"]" in compose
    assert "ports: [\"3000:3000\"]" not in compose
    assert 'request.url === "/main/query"' in server
    assert 'request.url === "/case/query"' in server
    assert "MAX_CONCURRENCY" in server


def test_gateway_streaming_uses_a_dedicated_read_timeout():
    source = (BACKEND / "fastapi_app" / "remote_agent_client.py").read_text(encoding="utf-8")
    env_example = (BACKEND / ".env.example").read_text(encoding="utf-8")

    assert 'AGENT_STREAM_READ_TIMEOUT_SECONDS' in source
    assert 'httpx.Timeout(self.timeout, read=self.stream_read_timeout)' in source
    assert 'AGENT_STREAM_READ_TIMEOUT_SECONDS=120' in env_example


def test_gateway_declares_limits_and_generic_exception_response():
    source = (BACKEND / "fastapi_app" / "main.py").read_text(encoding="utf-8")

    assert "Depends(limit_login)" in source
    assert "Depends(limit_agent_request)" in source
    assert "Depends(limit_authenticated_write)" in source
    assert '"msg": "服务暂时不可用，请稍后再试"' in source
    assert 'Field(min_length=1, max_length=4000)' in source


def test_patient_trace_uses_real_agent_summary_and_keeps_internal_details_private():
    agent_source = (BACKEND / "traditional_medical_agent" / "tcm_agent.py").read_text(encoding="utf-8")
    service_source = (BACKEND / "agent_service" / "main.py").read_text(encoding="utf-8")
    patient_source = (BACKEND.parents[1] / "frontend" / "ChineseMedicine" / "src" / "pages" / "register" / "smart.vue").read_text(encoding="utf-8")

    assert "def _build_public_trace" in agent_source
    assert '"state": "completed"' in agent_source
    assert '"知识图谱检索"' in agent_source
    assert 'payload["trace"] = _build_public_trace(state)' in agent_source
    assert '"state": "running"' in service_source
    assert "yield f\"data: {json.dumps({'event': 'trace', 'trace': result['trace']}" in service_source
    assert "trace.state === 'running'" in patient_source
