import asyncio
import json
import logging
import re
import time
import uuid
from contextvars import ContextVar

from fastapi import Request


logger = logging.getLogger("luojia.request")
request_id_context: ContextVar[str] = ContextVar("request_id", default="")
_REQUEST_ID = re.compile(r"^[A-Za-z0-9._:-]{1,80}$")


def current_request_id() -> str:
    return request_id_context.get()


async def request_observability_middleware(request: Request, call_next):
    supplied = request.headers.get("x-request-id", "")
    request_id = supplied if _REQUEST_ID.fullmatch(supplied) else uuid.uuid4().hex
    token = request_id_context.set(request_id)
    started = time.perf_counter()
    status_code = 500
    try:
        response = await call_next(request)
        status_code = response.status_code
        response.headers["X-Request-ID"] = request_id
        return response
    finally:
        duration_ms = round((time.perf_counter() - started) * 1000, 2)
        route = request.scope.get("route")
        route_path = getattr(route, "path", request.url.path)
        logger.info(
            json.dumps(
                {
                    "event": "http_request",
                    "request_id": request_id,
                    "method": request.method,
                    "route": route_path,
                    "status_code": status_code,
                    "duration_ms": duration_ms,
                },
                ensure_ascii=False,
                sort_keys=True,
            )
        )
        try:
            from app.main_deps import get_repository

            await asyncio.to_thread(
                get_repository().record_request_metric,
                request_id,
                request.method,
                route_path,
                status_code,
                duration_ms,
            )
        except Exception:
            logger.exception("request metric persistence failed")
        request_id_context.reset(token)
