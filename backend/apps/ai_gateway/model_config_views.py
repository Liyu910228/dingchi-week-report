"""System-admin views for OpenAI-compatible provider settings."""

from __future__ import annotations

import json

from asgiref.sync import sync_to_async
from django.http import HttpRequest, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods, require_POST

from apps.accounts.public import AuthenticationError, require_user
from apps.core.http import api_error, api_success, log_unhandled_exception
from apps.dictionary.services.customers import is_system_admin

from .services.model_config import (
    AIConnectionTestError,
    record_test_result,
    save_model_config,
    serialize_model_config,
    test_model_connection,
)
from .services.ocr_keys import create_ocr_key, delete_ocr_key, list_ocr_keys, update_ocr_key


def _ensure_admin(request: HttpRequest):
    user, role_code = require_user(request)
    if not is_system_admin(role_code):
        raise PermissionError("仅系统管理员可以维护模型配置。")
    return user


def _error(exc: Exception) -> JsonResponse:
    if isinstance(exc, AuthenticationError):
        return api_error(exc.code, str(exc), status=401)
    if isinstance(exc, PermissionError):
        return api_error("FORBIDDEN", str(exc), status=403)
    if isinstance(exc, json.JSONDecodeError):
        return api_error("INVALID_JSON", "请求体不是有效的 JSON。", status=400)
    if isinstance(exc, ValueError):
        return api_error("INVALID_REQUEST", str(exc), status=400)
    log_unhandled_exception(exc, context="ai-model-config")
    return api_error("INTERNAL_ERROR", "服务暂时不可用。", status=500)


@csrf_exempt
@require_http_methods(["GET", "PUT"])
def model_config_view(request: HttpRequest) -> JsonResponse:
    try:
        user = _ensure_admin(request)
        if request.method == "GET":
            return api_success(serialize_model_config())
        payload = json.loads(request.body)
        if not isinstance(payload, dict):
            raise ValueError("请求体必须是 JSON 对象。")
        return api_success(save_model_config(payload, int(user.id)))
    except Exception as exc:
        return _error(exc)


@csrf_exempt
@require_http_methods(["PUT"])
def model_config_save_view(request: HttpRequest) -> JsonResponse:
    try:
        user = _ensure_admin(request)
        payload = json.loads(request.body)
        if not isinstance(payload, dict):
            raise ValueError("请求体必须是 JSON 对象。")
        return api_success(save_model_config(payload, int(user.id)))
    except Exception as exc:
        return _error(exc)


@csrf_exempt
@require_POST
async def model_config_test_view(request: HttpRequest) -> JsonResponse:
    try:
        await sync_to_async(_ensure_admin, thread_sensitive=True)(request)
        payload = json.loads(request.body)
        if not isinstance(payload, dict):
            raise ValueError("请求体必须是 JSON 对象。")
        result = await test_model_connection(payload)
        await sync_to_async(record_test_result, thread_sensitive=True)(True, result["message"])
        return api_success(result)
    except AIConnectionTestError as exc:
        message = f"连接失败：{exc}"
        await sync_to_async(record_test_result, thread_sensitive=True)(False, message)
        return api_error("AI_CONNECTION_FAILED", message, status=502)
    except Exception as exc:
        return _error(exc)


@csrf_exempt
@require_http_methods(["GET", "POST"])
def ocr_key_collection_view(request: HttpRequest) -> JsonResponse:
    try:
        user = _ensure_admin(request)
        if request.method == "GET":
            return api_success(list_ocr_keys())
        payload = json.loads(request.body)
        if not isinstance(payload, dict):
            raise ValueError("请求体必须是 JSON 对象。")
        return api_success(create_ocr_key(payload, int(user.id)))
    except Exception as exc:
        return _error(exc)


@csrf_exempt
@require_http_methods(["PATCH", "DELETE"])
def ocr_key_detail_view(request: HttpRequest, key_id: str) -> JsonResponse:
    try:
        _ensure_admin(request)
        if request.method == "DELETE":
            delete_ocr_key(key_id)
            return api_success({"deleted": True})
        payload = json.loads(request.body)
        if not isinstance(payload, dict):
            raise ValueError("请求体必须是 JSON 对象。")
        return api_success(update_ocr_key(key_id, payload))
    except Exception as exc:
        return _error(exc)
