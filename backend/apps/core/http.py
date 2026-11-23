import json
import logging
from typing import Any

from django.http import HttpRequest, JsonResponse

_error_logger = logging.getLogger("apps.core.errors")


def parse_json_object(request: HttpRequest) -> dict[str, Any]:
    """解析 JSON 对象；空请求体保持与现有接口相同的空对象语义。"""
    if not request.body:
        return {}
    try:
        value = json.loads(request.body)
    except UnicodeDecodeError as exc:
        raise ValueError("请求体必须使用 UTF-8 编码。") from exc
    if not isinstance(value, dict):
        raise ValueError("请求体必须是 JSON 对象。")
    return value


def log_unhandled_exception(exc: BaseException, *, context: str = "") -> None:
    """Log the full traceback for an exception converted into a 500 response.

    View functions intentionally convert exceptions into the public JSON error
    contract. Django's exception middleware therefore cannot see the error and
    would otherwise log only a generic ``500 Internal Server Error`` line.
    """
    _error_logger.error(
        "unhandled exception context=%s exception_type=%s detail=%s",
        context or "api",
        type(exc).__name__,
        str(exc) or "<empty>",
        exc_info=(type(exc), exc, exc.__traceback__),
    )


def api_success(data: Any, *, status: int = 200) -> JsonResponse:
    return JsonResponse({"success": True, "data": data}, status=status)


def api_error(
    code: str,
    message: str,
    *,
    status: int,
    details: Any | None = None,
) -> JsonResponse:
    error: dict[str, Any] = {"code": code, "message": message}
    if details is not None:
        error["details"] = details
    return JsonResponse({"success": False, "error": error}, status=status)
