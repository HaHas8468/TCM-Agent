"""基于 Redis 的网关写接口限流。"""

import os
from math import ceil
from typing import Any

from fastapi import Depends, HTTPException, Request
from fastapi.responses import JSONResponse

from .security import get_redis, require_auth


RATE_WINDOW_SECONDS = max(1, int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60")))
LOGIN_RATE_LIMIT = max(1, int(os.getenv("RATE_LIMIT_LOGIN_PER_MINUTE", "10")))
WRITE_RATE_LIMIT = max(1, int(os.getenv("RATE_LIMIT_WRITE_PER_MINUTE", "30")))
AGENT_RATE_LIMIT = max(1, int(os.getenv("RATE_LIMIT_AGENT_PER_MINUTE", "10")))


def _client_ip(request: Request) -> str:
    """优先使用受反向代理控制的真实来源地址，避免客户端伪造 X-Forwarded-For。"""
    real_ip = request.headers.get("x-real-ip", "").strip()
    if real_ip:
        return real_ip
    forwarded_for = request.headers.get("x-forwarded-for", "")
    if forwarded_for:
        return forwarded_for.split(",", 1)[0].strip() or "unknown"
    return request.client.host if request.client else "unknown"


def _consume(scope: str, subject: str, limit: int) -> None:
    key = f"rate:{scope}:{subject}"
    try:
        client = get_redis()
        count = int(client.incr(key))
        if count == 1:
            client.expire(key, RATE_WINDOW_SECONDS)
        if count <= limit:
            return
        ttl = max(1, int(client.ttl(key)))
    except HTTPException:
        raise
    except Exception as exc:
        # Redis 是启动时强制依赖；不可用时拒绝高成本写请求，避免失去保护后继续放量。
        raise HTTPException(status_code=503, detail="限流服务暂不可用") from exc

    raise HTTPException(
        status_code=429,
        detail="请求过于频繁，请稍后再试",
        headers={"Retry-After": str(ceil(ttl))},
    )


async def limit_login(request: Request) -> None:
    _consume("login", _client_ip(request), LOGIN_RATE_LIMIT)


async def limit_anonymous_write(request: Request) -> None:
    _consume("anonymous-write", _client_ip(request), WRITE_RATE_LIMIT)


async def limit_authenticated_write(
    request: Request, token_info: dict[str, Any] = Depends(require_auth)
) -> dict[str, Any]:
    subject = f"{token_info.get('role', 'unknown')}:{token_info.get('role_id', 'unknown')}"
    _consume("write", subject, WRITE_RATE_LIMIT)
    return token_info


async def limit_agent_request(
    request: Request, token_info: dict[str, Any] = Depends(require_auth)
) -> dict[str, Any]:
    subject = f"{token_info.get('role', 'unknown')}:{token_info.get('role_id', 'unknown')}"
    _consume("agent", subject, AGENT_RATE_LIMIT)
    return token_info


def rate_limit_error_response(exc: HTTPException) -> JSONResponse:
    """供全局 HTTP 异常处理器保留 Retry-After 响应头。"""
    return JSONResponse(
        status_code=exc.status_code,
        content={"code": exc.status_code, "msg": exc.detail},
        headers=exc.headers or {},
    )
