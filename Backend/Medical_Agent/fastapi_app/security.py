"""网关认证、配置校验及敏感信息脱敏工具。"""

import hashlib
import json
import os
import secrets
from datetime import datetime, timezone
from typing import Any, Optional

import redis
from fastapi import Header, HTTPException


TOKEN_TTL_SECONDS = int(os.getenv("AUTH_TOKEN_TTL_SECONDS", "86400"))
_redis_client: Optional[redis.Redis] = None


def get_redis() -> redis.Redis:
    """延迟创建 Redis 客户端，便于测试替换且不在 import 时连接网络。"""
    global _redis_client
    if _redis_client is None:
        redis_url = os.getenv("REDIS_URL")
        if not redis_url:
            raise RuntimeError("REDIS_URL 未配置")
        _redis_client = redis.Redis.from_url(redis_url, decode_responses=True, socket_connect_timeout=2)
    return _redis_client


def validate_runtime_config() -> None:
    """生产环境必须显式提供所有基础设施凭据，禁止回退到示例值。"""
    if os.getenv("APP_ENV", "development").lower() != "production":
        return
    required = ("MYSQL_HOST", "MYSQL_DB", "MYSQL_USER", "MYSQL_PASSWORD", "REDIS_URL", "AGENT_BASE_URL", "AGENT_API_KEY", "KG_SERVICE_BASE_URL", "CORS_ORIGINS")
    missing = [name for name in required if not os.getenv(name)]
    if missing:
        raise RuntimeError(f"生产配置缺失: {', '.join(missing)}")
    get_redis().ping()


def _token_key(token: str) -> str:
    digest = hashlib.sha256(token.encode("utf-8")).hexdigest()
    return f"auth:token:{digest}"


def generate_token(username: str, role: str, role_id: str) -> str:
    token = secrets.token_urlsafe(32)
    payload = {
        "username": username,
        "role": role,
        "role_id": role_id,
        "issued_at": datetime.now(timezone.utc).isoformat(),
    }
    get_redis().setex(_token_key(token), TOKEN_TTL_SECONDS, json.dumps(payload, ensure_ascii=False))
    return token


def parse_token(authorization: Optional[str]) -> Optional[dict[str, Any]]:
    if not authorization or not authorization.startswith("Bearer "):
        return None
    token = authorization.removeprefix("Bearer ").strip()
    if not token:
        return None
    payload = get_redis().get(_token_key(token))
    return json.loads(payload) if payload else None


def revoke_token(authorization: Optional[str]) -> None:
    if authorization and authorization.startswith("Bearer "):
        get_redis().delete(_token_key(authorization.removeprefix("Bearer ").strip()))


def require_auth(authorization: Optional[str] = Header(default=None)) -> dict[str, Any]:
    try:
        token_info = parse_token(authorization)
    except Exception as exc:
        raise HTTPException(status_code=503, detail="认证服务暂不可用") from exc
    if not token_info:
        raise HTTPException(status_code=401, detail="未认证或登录已失效")
    return token_info


def redact_headers(headers: dict[str, str]) -> dict[str, str]:
    """仅用于安全日志；令牌和 Cookie 永不写入日志。"""
    return {key: ("***" if key.lower() in {"authorization", "cookie", "x-api-key"} else value) for key, value in headers.items()}
