"""JSON views for authentication and organization administration."""

from __future__ import annotations

import json

from django.http import HttpRequest, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from apps.core.http import api_error, api_success, log_unhandled_exception, parse_json_object

from .dao import find_group_by_id, find_user_by_id, list_groups, list_user_options, list_users
from .services.auth import (
    AuthenticationError,
    AuthorizationError,
    UserConflictError,
    UserNotFoundError,
    change_password,
    create_user,
    delete_user,
    get_user_roles,
    login,
    require_request_user,
    serialize_role,
    serialize_user,
    switch_role,
    update_user,
)
from .services.organization import (
    GroupConflictError,
    GroupNotFoundError,
    RoleConflictError,
    RoleNotFoundError,
    can_manage_directory,
    create_group,
    create_role,
    delete_group,
    delete_role,
    get_role_list,
    serialize_group,
    update_group,
    update_role,
)
from .services.role_options import get_role_options


def _error_from_exception(exc: Exception) -> JsonResponse:
    if isinstance(exc, AuthenticationError):
        return api_error(exc.code, str(exc), status=401)
    if isinstance(exc, AuthorizationError):
        return api_error(exc.code, str(exc), status=403)
    if isinstance(exc, RoleNotFoundError):
        return api_error(exc.code, str(exc), status=404)
    if isinstance(exc, RoleConflictError):
        return api_error(exc.code, str(exc), status=409)
    if isinstance(exc, (GroupNotFoundError, UserNotFoundError)):
        return api_error(exc.code, str(exc), status=404)
    if isinstance(exc, (GroupConflictError, UserConflictError)):
        return api_error(exc.code, str(exc), status=409)
    if isinstance(exc, json.JSONDecodeError):
        return api_error("INVALID_JSON", "请求体不是有效的 JSON。", status=400)
    if isinstance(exc, ValueError):
        return api_error("INVALID_REQUEST", str(exc), status=400)
    log_unhandled_exception(exc, context="accounts")
    return api_error("INTERNAL_ERROR", "服务暂时不可用。", status=500)


@csrf_exempt
@require_POST
def login_view(request: HttpRequest) -> JsonResponse:
    """用户登录并返回当前角色与访问令牌。

    方法/路径：POST /api/v1/auth/login/；认证：公开；幂等：否。
    请求参数：username、password（RSA-OAEP-SHA256 密文）、可选 role_code。
    成功响应：data.access_token、user、roles、active_role、expires_in。
    失败响应：400 INVALID_JSON/INVALID_REQUEST；401 AUTHENTICATION_FAILED。
    安全/追踪/兼容：密码只接受加密值；响应带 X-Trace-ID；新增会话字段向后兼容。
    """
    try:
        payload = parse_json_object(request)
        return api_success(
            login(
                username=str(payload.get("username") or "").strip(),
                password_ciphertext=str(payload.get("password") or ""),
                requested_role_code=str(payload.get("role_code") or "") or None,
            )
        )
    except Exception as exc:
        return _error_from_exception(exc)


@require_GET
def me_view(request: HttpRequest) -> JsonResponse:
    """获取登录用户、上下级关系、所属分组和可切换角色。

    方法/路径：GET /api/v1/auth/me/；认证：Bearer；幂等：是；请求参数：无。
    成功响应：data.user、data.roles、data.active_role；失败：401 AUTHENTICATION_FAILED。
    追踪/兼容：响应带 X-Trace-ID，ID 以字符串返回，字段只增不删。
    """
    try:
        user, role_code = require_request_user(request)
        roles = get_user_roles(user.id)
        role = next(role for role in roles if role.role_code == role_code)
        return api_success(
            {
                "user": serialize_user(user),
                "roles": [serialize_role(item) for item in roles],
                "active_role": serialize_role(role),
            }
        )
    except Exception as exc:
        return _error_from_exception(exc)


@csrf_exempt
@require_POST
def switch_role_view(request: HttpRequest) -> JsonResponse:
    """切换当前用户的工作角色并签发带新角色声明的令牌。

    方法/路径：POST /api/v1/auth/switch-role/；认证：Bearer；幂等：是。
    请求参数：role_code；成功响应：同登录会话结构；失败：401/403/400。
    安全/追踪/兼容：仅允许已分配角色；响应带 X-Trace-ID；旧令牌仍可自然过期。
    """
    try:
        user, _ = require_request_user(request)
        payload = parse_json_object(request)
        return api_success(
            switch_role(user=user, role_code=str(payload.get("role_code") or "").strip())
        )
    except Exception as exc:
        return _error_from_exception(exc)


@csrf_exempt
@require_POST
def change_password_view(request: HttpRequest) -> JsonResponse:
    """当前登录用户修改自己的登录密码，并自动签发新令牌以"无感续期"。

    方法/路径：POST /api/v1/auth/change-password/；认证：Bearer；幂等：否。
    请求参数：old_password、new_password（均为 RSA-OAEP-SHA256 密文，新密码至少 8 位
    且不能与旧密码相同）。
    成功响应：data 与登录会话同构（access_token、token_type、expires_in、user、roles、
    active_role），客户端应整体替换本地会话以使用新令牌继续访问；
    失败：400 INVALID_REQUEST（旧密码不正确、密码不合规）、
    401 AUTHENTICATION_FAILED（未登录 / 当前角色不可用）。
    安全/追踪/兼容：密码只接受加密值，不写日志、不回传明文；响应带 X-Trace-ID；
    由于 token 为 stateless 签名令牌，旧令牌按 AUTH_TOKEN_MAX_AGE_SECONDS 自然过期，
    不会立即吊销其他设备的旧会话。
    """
    try:
        user, role_code = require_request_user(request)
        payload = parse_json_object(request)
        return api_success(
            change_password(
                user=user,
                old_password_ciphertext=str(payload.get("old_password") or ""),
                new_password_ciphertext=str(payload.get("new_password") or ""),
                current_role_code=role_code,
            )
        )
    except Exception as exc:
        return _error_from_exception(exc)


@csrf_exempt
@require_POST
def logout_view(request: HttpRequest) -> JsonResponse:
    """结束浏览器当前会话（客户端删除令牌，服务端令牌按时效自然失效）。

    方法/路径：POST /api/v1/auth/logout/；认证：Bearer；请求参数：无；幂等：是。
    成功响应：data.logged_out=true；失败：401 AUTHENTICATION_FAILED；响应带 X-Trace-ID。
    """
    try:
        require_request_user(request)
        return api_success({"logged_out": True})
    except Exception as exc:
        return _error_from_exception(exc)


@require_GET
def roles_view(request: HttpRequest) -> JsonResponse:
    """查询角色管理列表。

    方法/路径：GET /api/v1/roles/；认证：总裁或系统管理员；请求参数：无；幂等：是。
    成功响应：data.items 为角色数组；失败：401/403；响应带 X-Trace-ID。
    """
    try:
        _, role_code = require_request_user(request)
        if not can_manage_directory(role_code):
            raise AuthorizationError("仅总裁和系统管理员可以管理角色。")
        return api_success({"items": get_role_list()})
    except Exception as exc:
        return _error_from_exception(exc)


@csrf_exempt
@require_POST
def role_create_view(request: HttpRequest) -> JsonResponse:
    """新增角色定义，供系统管理员维护角色模板映射。

    方法/路径：POST /api/v1/roles/new/；认证：总裁或系统管理员；幂等：否。
    请求体：role_code、role_name、scope 必填；report_template_code、role_group_code 可为空字符串，
    description 可为空；
    scope 必须是 role_scope 字典中的启用编码，report_template_code 非空时必须是
    report_template 字典中的启用编码；role_code 使用小写字母、数字和下划线。
    成功响应：201 角色对象，ID 为字符串；失败：400 INVALID_REQUEST、401、403，
    编码重复返回 409 ROLE_CONFLICT；响应带 X-Trace-ID，新增字段保持向后兼容。
    """
    try:
        _, role_code = require_request_user(request)
        if not can_manage_directory(role_code):
            raise AuthorizationError("无权维护角色。")
        created = create_role(payload=parse_json_object(request))
        return api_success(serialize_role(created), status=201)
    except Exception as exc:
        return _error_from_exception(exc)


@csrf_exempt
@require_http_methods(["PATCH", "DELETE"])
def role_detail_view(request: HttpRequest, role_id: str) -> JsonResponse:
    """修改或删除一个角色配置。

    方法/路径：PATCH、DELETE /api/v1/roles/{id}/；认证：总裁或系统管理员。
    PATCH 请求体：可选 role_name、scope、description、report_template_code、role_group_code、
    status、sort_order；模板与分组传空字符串表示清空，省略时保留原配置；
    role_code 不可修改。响应为更新后的角色对象。
    DELETE 请求体：无；执行软删除并停用用户角色分配，历史周报保留；响应包含字符串 id 和
    deleted=true。系统管理员角色及调用方当前角色禁止删除。
    失败响应：400 INVALID_REQUEST、401、403、404 ROLE_NOT_FOUND、409 ROLE_CONFLICT；
    响应带 X-Trace-ID，删除操作不自动迁移或改表。
    """
    try:
        _, role_code = require_request_user(request)
        if not can_manage_directory(role_code):
            raise AuthorizationError("无权维护角色。")
        parsed_role_id = int(role_id)
        if request.method == "DELETE":
            deleted_role = delete_role(role_id=parsed_role_id, acting_role_code=role_code)
            return api_success({"id": str(deleted_role.id), "deleted": True})
        updated_role = update_role(role_id=parsed_role_id, payload=parse_json_object(request))
        return api_success(serialize_role(updated_role))
    except Exception as exc:
        return _error_from_exception(exc)


@require_GET
def groups_view(request: HttpRequest) -> JsonResponse:
    """查询组织分组列表。

    方法/路径：GET /api/v1/groups/；认证：Bearer；请求参数：无；幂等：是。
    成功响应：data.items 为分组数组；失败：401；响应带 X-Trace-ID。
    """
    try:
        require_request_user(request)
        return api_success({"items": list_groups()})
    except Exception as exc:
        return _error_from_exception(exc)


@csrf_exempt
@require_POST
def group_create_view(request: HttpRequest) -> JsonResponse:
    """新增组织分组。

    方法/路径：POST /api/v1/groups/new/；认证：总裁或系统管理员；
    请求参数：group_code、group_name 必填，description 可为空，parent_group_id 可为空；
    group_code 使用小写字母、数字和下划线且不能重复。成功响应：201 分组对象；
    失败：400/401/403/409；响应带 X-Trace-ID。
    """
    try:
        _, role_code = require_request_user(request)
        if not can_manage_directory(role_code):
            raise AuthorizationError("无权维护组织分组。")
        return api_success(
            serialize_group(create_group(payload=parse_json_object(request))), status=201
        )
    except Exception as exc:
        return _error_from_exception(exc)


@csrf_exempt
@require_http_methods(["PATCH", "DELETE"])
def group_update_view(request: HttpRequest, group_id: str) -> JsonResponse:
    """修改或删除组织分组。

    方法/路径：PATCH、DELETE /api/v1/groups/{id}/；认证：总裁或系统管理员。
    PATCH 请求参数：部分分组字段；DELETE 无请求体，要求分组没有下级和在职成员。
    成功响应：更新后的分组，或 id/deleted=true；失败：400/401/403/404/409；响应带 X-Trace-ID。
    """
    try:
        _, role_code = require_request_user(request)
        if not can_manage_directory(role_code):
            raise AuthorizationError("无权维护组织分组。")
        parsed_group_id = int(group_id)
        if request.method == "DELETE":
            deleted_group = delete_group(group_id=parsed_group_id)
            return api_success({"id": str(deleted_group.id), "deleted": True})
        group = find_group_by_id(parsed_group_id)
        if group is None:
            raise GroupNotFoundError("分组不存在或已被删除。")
        return api_success(
            serialize_group(update_group(group=group, payload=parse_json_object(request)))
        )
    except Exception as exc:
        return _error_from_exception(exc)


@require_GET
def users_view(request: HttpRequest) -> JsonResponse:
    """查询用户、上下级和分组信息，供组织管理页面使用。

    方法/路径：GET /api/v1/users/；认证：总裁或系统管理员；参数：可选 role_code、group_id、keyword。
    keyword 会在登录账号、工号、姓名、邮箱和手机号字段中执行模糊匹配。
    成功响应：data.items 为用户数组；失败：401/403；响应带 X-Trace-ID；ID 均为字符串。
    """
    try:
        _, role_code = require_request_user(request)
        if not can_manage_directory(role_code):
            raise AuthorizationError("仅总裁和系统管理员可以查看全量用户。")
        return api_success(
            {
                "items": list_users(
                    role_code=request.GET.get("role_code"),
                    group_id=request.GET.get("group_id"),
                    keyword=request.GET.get("keyword"),
                )
            }
        )
    except Exception as exc:
        return _error_from_exception(exc)


@require_GET
def user_options_view(request: HttpRequest) -> JsonResponse:
    """查询周报责任人和协作人下拉选项。

    方法/路径：GET /api/v1/users/options/；认证：Bearer；参数：无；幂等：是。
    成功响应：data.items 为在职用户数组，含字符串 id、employee_no、display_name、username、
    group_id、group_name（未分组使用“未分组”），供人员公共组件分组搜索；新增字段向后兼容。
    不返回密码或其他敏感字段；失败：401 AUTHENTICATION_FAILED；响应带 X-Trace-ID。
    """
    try:
        require_request_user(request)
        return api_success({"items": list_user_options()})
    except Exception as exc:
        return _error_from_exception(exc)


@csrf_exempt
@require_POST
def user_create_view(request: HttpRequest) -> JsonResponse:
    """新增用户并一次性分配角色、上级和主分组。

    方法/路径：POST /api/v1/users/new/；认证：总裁或系统管理员；
    参数：用户 JSON，password 必须 RSA 密文；employee_no 由服务端按 DC 加六位序号自动生成，
    客户端无需传入。
    成功响应：201 用户对象；失败：400/401/403；响应带 X-Trace-ID，绝不返回密码。
    """
    try:
        _, role_code = require_request_user(request)
        if not can_manage_directory(role_code):
            raise AuthorizationError("无权维护用户。")
        created = create_user(payload=parse_json_object(request))
        return api_success(serialize_user(created), status=201)
    except Exception as exc:
        return _error_from_exception(exc)


@csrf_exempt
@require_http_methods(["PATCH", "DELETE"])
def user_update_view(request: HttpRequest, user_id: str) -> JsonResponse:
    """修改或删除用户资料、上下级、分组、状态和角色集合。

    方法/路径：PATCH、DELETE /api/v1/users/{id}/；认证：总裁或系统管理员。
    PATCH 参数：部分用户字段，shared_user_ids为只读共享接收人ID数组；省略保留，[]清空。
    共享仅允许接收人查看该用户全部月度计划/周报，不授予编辑/提交/审批，撤销立即失效。
    DELETE 无请求体，执行软删除并停用角色/分组成员关系。
    成功响应：更新后的用户对象，或 id/deleted=true；失败：400/401/403/404/409；响应带 X-Trace-ID。
    """
    try:
        acting_user, role_code = require_request_user(request)
        if not can_manage_directory(role_code):
            raise AuthorizationError("无权维护用户。")
        parsed_user_id = int(user_id)
        if request.method == "DELETE":
            deleted_user = delete_user(user_id=parsed_user_id, acting_user_id=int(acting_user.id))
            return api_success({"id": str(deleted_user.id), "deleted": True})
        user = find_user_by_id(parsed_user_id)
        if user is None:
            raise UserNotFoundError("用户不存在或已被删除。")
        updated = update_user(user=user, payload=parse_json_object(request))
        return api_success(serialize_user(updated))
    except Exception as exc:
        return _error_from_exception(exc)


@require_GET
def role_options_view(request: HttpRequest) -> JsonResponse:
    """GET /api/v1/roles/options/：已登录用户的职位筛选字典，无请求参数。

    响应items仅含role_code/role_name字符串，启用项按配置排序；不暴露管理配置。
    Bearer认证401 AUTHENTICATION_FAILED，未知错误500；幂等、统一包络/X-Trace-ID。
    独立新增v1接口，不扩大职位管理权限；职位筛选仍与业务数据权限取交集。
    """
    try:
        require_request_user(request)
        return api_success({"items": get_role_options()})
    except Exception as exc:
        return _error_from_exception(exc)
