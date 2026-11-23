"""Request tracing middleware shared by Django and the outer ASGI app."""

from __future__ import annotations

import logging
import re
import time
from contextvars import ContextVar
from typing import Any
from uuid import uuid4

from django.http import HttpRequest, HttpResponse

TRACE_ID_HEADER = "X-Trace-ID"
_TRACE_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
_trace_id_context: ContextVar[str | None] = ContextVar("trace_id", default=None)
_logger = logging.getLogger("apps.core.request")


def get_trace_id() -> str | None:
    """Return the trace ID bound to the current request context."""
    return _trace_id_context.get()


def create_trace_id() -> str:
    """Create a compact, log-safe trace ID."""
    return uuid4().hex


def resolve_trace_id(candidate: str | None) -> str:
    """Keep a valid caller trace ID, otherwise generate one."""
    value = (candidate or "").strip()
    return value if _TRACE_ID_PATTERN.fullmatch(value) else create_trace_id()


def _scope_header(scope: dict[str, Any], header_name: str) -> str | None:
    header_key = header_name.lower().encode("ascii")
    for key, value in scope.get("headers", []):
        if key.lower() == header_key:
            return value.decode("latin-1")
    return None


def _log_request(
    *,
    trace_id: str,
    method: str,
    path: str,
    status_code: int | None,
    started_at: float,
) -> None:
    duration_ms = round((time.perf_counter() - started_at) * 1000, 2)
    _logger.info(
        "request completed method=%s path=%s status=%s duration_ms=%s",
        method,
        path,
        status_code if status_code is not None else "unknown",
        duration_ms,
        extra={"trace_id": trace_id},
    )


class DjangoTraceIdMiddleware:
    """Bind one trace ID to every Django request and response."""

    def __init__(self, get_response: Any) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        inherited_trace_id = get_trace_id()
        trace_id = inherited_trace_id or resolve_trace_id(request.headers.get(TRACE_ID_HEADER))
        token = _trace_id_context.set(trace_id)
        request.trace_id = trace_id  # type: ignore[attr-defined]
        started_at = time.perf_counter()
        response: HttpResponse | None = None

        try:
            response = self.get_response(request)
        except Exception:
            _logger.exception(
                "request failed method=%s path=%s",
                request.method,
                request.path,
                extra={"trace_id": trace_id},
            )
            raise
        finally:
            if inherited_trace_id is None:
                _log_request(
                    trace_id=trace_id,
                    method=request.method,
                    path=request.path,
                    status_code=response.status_code if response is not None else 500,
                    started_at=started_at,
                )
            _trace_id_context.reset(token)

        response[TRACE_ID_HEADER] = trace_id
        return response


class TraceIdMiddleware:
    """Outer ASGI middleware covering Django, MCP, and other HTTP mounts."""

    def __init__(self, app: Any) -> None:
        self.app = app

    async def __call__(self, scope: dict[str, Any], receive: Any, send: Any) -> None:
        if scope["type"] not in {"http", "websocket"}:
            await self.app(scope, receive, send)
            return

        inherited_trace_id = get_trace_id()
        trace_id = inherited_trace_id or resolve_trace_id(_scope_header(scope, TRACE_ID_HEADER))
        token = _trace_id_context.set(trace_id)
        status_code: int | None = None

        async def send_with_trace(message: dict[str, Any]) -> None:
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = int(message["status"])
                headers = list(message.get("headers", []))
                trace_header = TRACE_ID_HEADER.lower().encode("ascii")
                if not any(name.lower() == trace_header for name, _ in headers):
                    headers.append((trace_header, trace_id.encode("ascii")))
                message = {**message, "headers": headers}
            elif message["type"] == "websocket.accept":
                headers = list(message.get("headers", []))
                trace_header = TRACE_ID_HEADER.lower().encode("ascii")
                if not any(name.lower() == trace_header for name, _ in headers):
                    headers.append((trace_header, trace_id.encode("ascii")))
                message = {**message, "headers": headers}
            await send(message)

        started_at = time.perf_counter()
        try:
            await self.app(scope, receive, send_with_trace)
        except Exception:
            _logger.exception(
                "request failed method=%s path=%s",
                scope.get("method", scope["type"]),
                scope.get("path", ""),
                extra={"trace_id": trace_id},
            )
            raise
        finally:
            if inherited_trace_id is None:
                _log_request(
                    trace_id=trace_id,
                    method=scope.get("method", scope["type"]),
                    path=scope.get("path", ""),
                    status_code=status_code,
                    started_at=started_at,
                )
            _trace_id_context.reset(token)


class TraceIdLogFilter(logging.Filter):
    """Add the current trace ID to every log record, including startup logs."""

    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, "trace_id"):
            record.trace_id = get_trace_id() or "-"
        return True
