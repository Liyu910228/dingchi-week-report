"""JSON views for static dictionary options and customer administration."""

from __future__ import annotations

import json
from typing import Any

from django.http import HttpRequest, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from apps.accounts.public import AuthenticationError, require_user
from apps.core.http import api_error, api_success, log_unhandled_exception, parse_json_object

from .services.customers import (
    CustomerConflictError,
    CustomerNotFoundError,
    create_customer,
    is_system_admin,
    list_customers,
    soft_delete_customer,
    update_customer,
)
from .services.items import InvalidDictionaryTypeError, get_active_items


def _ensure_system_admin(request: HttpRequest) -> tuple[Any, str]:
    """Return the (user, role_code) for a system administrator request."""
    user, role_code = require_user(request)
    if not is_system_admin(role_code):
        raise PermissionError("仅系统管理员可以维护客户配置。")
    return user, role_code


def _error_from_exception(exc: Exception) -> JsonResponse:
    if isinstance(exc, AuthenticationError):
        return api_error(exc.code, str(exc), status=401)
    if isinstance(exc, CustomerNotFoundError):
        return api_error(exc.code, str(exc), status=404)
    if isinstance(exc, CustomerConflictError):
        return api_error(exc.code, str(exc), status=409)
    if isinstance(exc, InvalidDictionaryTypeError):
        return api_error(exc.code, str(exc), status=400)
    if isinstance(exc, PermissionError):
        return api_error("FORBIDDEN", str(exc), status=403)
    if isinstance(exc, json.JSONDecodeError):
        return api_error("INVALID_JSON", "请求体不是有效的 JSON。", status=400)
    if isinstance(exc, ValueError):
        return api_error("INVALID_REQUEST", str(exc), status=400)
    log_unhandled_exception(exc, context="dictionary")
    return api_error("INTERNAL_ERROR", "服务暂时不可用。", status=500)


@require_GET
def dictionary_items_view(request: HttpRequest, dict_type: str) -> JsonResponse:
    """查询指定类型的启用字典项，供页面下拉框和配置校验使用。

    方法/路径：GET /api/v1/dictionaries/{dict_type}/；认证：Bearer；幂等：是。
    路径参数：dict_type 为小写 snake_case 类型，如 role_scope、report_template；无请求体。
    成功响应：data.items 为选项数组，每项包含字符串 id、dict_type、dict_code、dict_name、
    dict_value、description、status 和非负 sort_order；未知类型返回空数组。
    失败响应：401 AUTHENTICATION_FAILED；400 INVALID_DICTIONARY_TYPE；响应带 X-Trace-ID。
    兼容性：字典编码稳定，新增选项向后兼容；下游不得依赖数据库表结构。
    """
    try:
        require_user(request)
        return api_success({"items": get_active_items(dict_type=dict_type)})
    except InvalidDictionaryTypeError as exc:
        return api_error(exc.code, str(exc), status=400)
    except Exception as exc:
        if hasattr(exc, "code") and str(exc.code) == "AUTHENTICATION_FAILED":
            return api_error("AUTHENTICATION_FAILED", str(exc), status=401)
        log_unhandled_exception(exc, context="dictionary")
        return api_error("INTERNAL_ERROR", "服务暂时不可用。", status=500)


@require_GET
def customer_list_view(request: HttpRequest) -> JsonResponse:
    """查询客户配置列表，供系统管理员维护客户编号与名称。

    方法/路径：GET /api/v1/dictionaries/customers/；认证：Bearer；权限：仅系统管理员。
    请求参数：无。成功响应：data.items 为客户数组，每项包含字符串 id、dict_code（客户编号）、
    dict_name（客户名称）、status、sort_order、description、dict_type=customer；按 sort_order 升序。
    失败响应：401 AUTHENTICATION_FAILED；403 FORBIDDEN；响应带 X-Trace-ID。
    """
    try:
        _ensure_system_admin(request)
        return api_success({"items": list_customers()})
    except Exception as exc:
        return _error_from_exception(exc)


@csrf_exempt
@require_POST
def customer_create_view(request: HttpRequest) -> JsonResponse:
    """新增客户配置。

    方法/路径：POST /api/v1/dictionaries/customers/new/；权限：仅系统管理员。
    请求体：dict_code 必填，仅英文字母和数字，1–64 字符；dict_name 必填，1–128 字符；
    sort_order、description 可选。
    成功响应：201 客户对象；失败：400 INVALID_REQUEST、401、403、409 CUSTOMER_CONFLICT。
    """
    try:
        _ensure_system_admin(request)
        created = create_customer(payload=parse_json_object(request))
        return api_success(created, status=201)
    except Exception as exc:
        return _error_from_exception(exc)


@csrf_exempt
@require_http_methods(["PATCH", "DELETE"])
def customer_detail_view(request: HttpRequest, customer_id: str) -> JsonResponse:
    """修改或删除一个客户配置。

    方法/路径：PATCH、DELETE /api/v1/dictionaries/customers/{id}/；权限：仅系统管理员。
    PATCH 请求体：dict_name（1–128 字符）、sort_order、status、description 任选；
    dict_code 不可修改。
    DELETE 无请求体；执行软删除，历史周报引用保留；响应包含 id 与 deleted=true。
    失败响应：400 INVALID_REQUEST、401、403、404 CUSTOMER_NOT_FOUND、409 CUSTOMER_CONFLICT。
    """
    try:
        _ensure_system_admin(request)
    except Exception as exc:
        return _error_from_exception(exc)
    try:
        parsed_id = int(customer_id)
    except ValueError:
        return api_error("INVALID_REQUEST", "客户 ID 必须是数字。", status=400)
    try:
        if request.method == "DELETE":
            deleted = soft_delete_customer(customer_id=parsed_id)
            return api_success({"id": deleted["id"], "deleted": True})
        updated = update_customer(customer_id=parsed_id, payload=parse_json_object(request))
        return api_success(updated)
    except Exception as exc:
        return _error_from_exception(exc)
