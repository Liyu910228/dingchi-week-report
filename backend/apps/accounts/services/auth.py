"""Authentication and role-switching services."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from django.conf import settings
from django.contrib.auth.hashers import constant_time_compare
from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.core.authentication.token import create_access_token
from apps.core.security.passwords import CryptoPayloadError, decrypt_client_password

from ..customer_assignment_dao import role_customer_ids
from ..manager_dao import ordered_manager_ids
from ..models import Role, UserAccount, UserGroupMembership, UserManager, UserRole
from ..monthly_approver_dao import has_applicants, ordered_ids
from ..report_share_dao import recipients as shared_recipients
from .customer_assignments import set_user_customers, user_assignments
from .managers import set_managers
from .monthly_approvers import set_monthly_approvers
from .report_sharing import set_shared_users


class AuthenticationError(ValueError):
    """A safe, user-facing authentication failure."""

    code = "AUTHENTICATION_FAILED"


class AuthorizationError(ValueError):
    """The identity is valid but is not allowed to perform an operation."""

    code = "FORBIDDEN"


class UserNotFoundError(ValueError):
    """The requested directory user is missing or has already been deleted."""

    code = "USER_NOT_FOUND"


class UserConflictError(ValueError):
    """The requested user operation would invalidate the active session."""

    code = "USER_CONFLICT"


def login(
    *, username: str, password_ciphertext: str, requested_role_code: str | None = None
) -> dict[str, Any]:
    """Decrypt the transport password, verify it and issue a signed token."""
    if not username or not password_ciphertext:
        raise AuthenticationError("用户名和密码不能为空。")
    try:
        password = decrypt_client_password(password_ciphertext)
    except CryptoPayloadError as exc:
        raise AuthenticationError("密码加密格式无效，请刷新页面后重试。") from exc

    user = UserAccount.objects.filter(username=username, status="active").first()
    if user is None:
        raise AuthenticationError("用户名或密码错误。")
    # EncryptedPasswordField decrypts only in request-local memory.  The value
    # remains RSA ciphertext in the database.
    stored_password = str(user.password_ciphertext or "")
    if not constant_time_compare(stored_password, password):
        raise AuthenticationError("用户名或密码错误。")

    roles = get_user_roles(user.id)
    if not roles:
        raise AuthenticationError("当前用户尚未分配可用角色。")
    role = _choose_role(roles, requested_role_code)
    user.last_login_at = timezone.now()
    user.save(update_fields=["last_login_at", "updated_at"])
    return build_session(user, roles, role.role_code)


MIN_PASSWORD_LENGTH = 8


def change_password(
    *,
    user: UserAccount,
    old_password_ciphertext: str,
    new_password_ciphertext: str,
    current_role_code: str,
) -> dict[str, Any]:
    """Verify the caller's old password and replace it with a new encrypted one.

    改完密码后立刻按当前角色签发新会话（access_token + user + roles + active_role），
    实现"无感续期"——前端收到响应后用新令牌替换本地凭证，不需要用户重新登录。
    由于当前 token 是 stateless 签名 token（见 apps/core/authentication/token.py），
    旧令牌按配置自然过期，不在本接口强制吊销；其他设备的旧会话将持续到
    AUTH_TOKEN_MAX_AGE_SECONDS 到期为止。

    旧密码校验失败按请求参数错误处理（ValueError -> 400），避免复用 401 语义
    触发前端"会话失效跳登录"的逻辑；密码明文只在请求内存短暂存在。
    """
    if not old_password_ciphertext or not new_password_ciphertext:
        raise ValueError("旧密码和新密码不能为空。")
    try:
        old_password = decrypt_client_password(old_password_ciphertext)
        new_password = decrypt_client_password(new_password_ciphertext)
    except CryptoPayloadError as exc:
        raise ValueError("密码必须使用 RSA-OAEP-SHA256 加密。") from exc
    stored_password = str(user.password_ciphertext or "")
    if not constant_time_compare(stored_password, old_password):
        raise ValueError("旧密码不正确。")
    if old_password == new_password:
        raise ValueError("新密码不能与旧密码相同。")
    if len(new_password) < MIN_PASSWORD_LENGTH:
        raise ValueError(f"新密码长度至少 {MIN_PASSWORD_LENGTH} 位。")
    user.password_ciphertext = new_password
    user.save(update_fields=["password_ciphertext", "updated_at"])
    roles = get_user_roles(user.id)
    if not any(role.role_code == current_role_code for role in roles):
        raise AuthenticationError("当前角色不可用，请重新登录。")
    return build_session(user, roles, current_role_code)


def build_session(user: UserAccount, roles: list[Role], active_role_code: str) -> dict[str, Any]:
    """Return the public session contract used by the browser store."""
    active_role = next(role for role in roles if role.role_code == active_role_code)
    return {
        "access_token": create_access_token(user_id=int(user.id), role_code=active_role.role_code),
        "token_type": "Bearer",
        "expires_in": settings.AUTH_TOKEN_MAX_AGE_SECONDS,
        "user": serialize_user(user),
        "roles": [serialize_role(role) for role in roles],
        "active_role": serialize_role(active_role),
    }


def get_user_roles(user_id: int) -> list[Role]:
    """Resolve assigned roles without a database foreign key."""
    assignments = list(
        UserRole.objects.filter(user_id=user_id, status="active")
        .order_by("-is_default", "id")
        .values_list("role_id", flat=True)
    )
    role_ids = list(assignments)
    if not role_ids:
        return []
    role_map = {role.id: role for role in Role.objects.filter(id__in=role_ids, status="active")}
    return [role_map[role_id] for role_id in role_ids if role_id in role_map]


def resolve_request_user(request: Any) -> tuple[UserAccount | None, str | None]:
    """Resolve the middleware claims into an active user and role."""
    claims = getattr(request, "auth_claims", None)
    if not isinstance(claims, Mapping):
        return None, None
    try:
        user_id = int(str(claims.get("user_id")))
    except (TypeError, ValueError):
        return None, None
    user = UserAccount.objects.filter(id=user_id, status="active").first()
    if user is None:
        return None, None
    roles = get_user_roles(user.id)
    role_code = str(claims.get("role_code") or "")
    if not any(role.role_code == role_code for role in roles):
        return None, None
    return user, role_code


def require_request_user(request: Any) -> tuple[UserAccount, str]:
    """验证原会话，按有效职位合并数据范围；填写职位由报告业务单独校验。

    all/team/self的数据集合嵌套，取最大范围即可合并；管理入口仍要求实际分配system_admin。
    不修改Token或用户默认职位，保留旧会话契约。
    """
    user, role_code = resolve_request_user(request)
    if user is None or role_code is None:
        raise AuthenticationError("请先登录后再访问该资源。")
    roles = get_user_roles(user.id)
    priority = {"self": 0, "team": 1, "all": 2}
    role = max(
        roles, key=lambda item: (item.role_code == "system_admin", priority.get(item.scope, 0))
    )
    return user, role.role_code


def switch_role(*, user: UserAccount, role_code: str) -> dict[str, Any]:
    roles = get_user_roles(user.id)
    if not any(role.role_code == role_code for role in roles):
        raise AuthorizationError("当前用户未分配该角色。")
    return build_session(user, roles, role_code)


def create_user(*, payload: Mapping[str, Any]) -> UserAccount:
    """并发新增仍由数据库唯一约束兜底，返回可识别的账号冲突。"""
    try:
        return _create_user(payload=payload)
    except IntegrityError as exc:
        username = str(payload.get("username") or "").strip()
        if UserAccount.objects.filter(username=username).exclude(status="deleted").exists():
            raise UserConflictError("登录账号已存在，请使用其他账号。") from exc
        raise


def _create_user(*, payload: Mapping[str, Any]) -> UserAccount:
    """Create a user and logical role memberships in one transaction."""
    username = str(payload.get("username") or "").strip()
    display_name = str(payload.get("display_name") or "").strip()
    password_ciphertext = str(payload.get("password") or "")
    if not username or not display_name or not password_ciphertext:
        raise ValueError("用户名、姓名和加密密码均不能为空。")
    try:
        plaintext = decrypt_client_password(password_ciphertext)
    except CryptoPayloadError as exc:
        raise ValueError("密码必须使用 RSA-OAEP-SHA256 加密。") from exc
    role_codes = _normalise_role_codes(payload.get("role_codes"))
    if not role_codes:
        raise ValueError("至少分配一个角色。")
    roles = list(Role.objects.filter(role_code__in=role_codes, status="active"))
    if len(roles) != len(set(role_codes)):
        raise ValueError("存在不可用的角色编码。")
    group_id = _optional_int(payload.get("group_id"))
    manager_id = _optional_int(payload.get("manager_id"))
    with transaction.atomic():
        roles = list(
            Role.objects.select_for_update().filter(role_code__in=role_codes, status="active")
        )
        if len(roles) != len(set(role_codes)):
            raise ValueError("存在不可用的角色编码。")
        if UserAccount.objects.filter(username=username).exclude(status="deleted").exists():
            raise UserConflictError("登录账号已存在，请使用其他账号。")
        employee_no = _next_employee_no()
        user = UserAccount.objects.create(
            username=username,
            employee_no=employee_no,
            display_name=display_name,
            email=str(payload.get("email") or "").strip(),
            phone=str(payload.get("phone") or "").strip(),
            password_ciphertext=plaintext,
            group_id=group_id,
            manager_id=manager_id,
            avatar_color=str(payload.get("avatar_color") or "#2f80ed"),
            # Super administrators are provisioned only by database scripts;
            # UI/API-created users are always ordinary users.
            is_super=False,
        )
        if "manager_ids" in payload:
            ids = set_managers(int(user.id), payload["manager_ids"])
            user.manager_id = ids[0] if ids else None
        elif manager_id:
            set_managers(int(user.id), [manager_id])
        if "monthly_approver_ids" in payload:
            set_monthly_approvers(int(user.id), payload["monthly_approver_ids"])
        set_shared_users(user.id, payload.get("shared_user_ids", []))
        for index, role in enumerate(roles):
            UserRole.objects.create(user_id=user.id, role_id=role.id, is_default=index == 0)
        set_user_customers(user.id, payload.get("role_customer_ids", {}))
    return user


def _next_employee_no() -> str:
    """Generate the next employee number in the ``DC000001`` sequence.

    User creation locks the current user rows before calling this helper.  The
    number is derived from the largest existing DC sequence, so deleted users
    do not cause a previously issued number to be reused.
    """
    employee_numbers = list(
        UserAccount.objects.select_for_update().values_list("employee_no", flat=True)
    )
    max_sequence = 0
    for value in employee_numbers:
        employee_no = str(value or "")
        if not employee_no.startswith("DC"):
            continue
        suffix = employee_no[2:]
        if suffix.isdigit():
            max_sequence = max(max_sequence, int(suffix))
    if max_sequence >= 999999:
        raise ValueError("工号序号已达到上限，无法自动生成新的工号。")
    return f"DC{max_sequence + 1:06d}"


@transaction.atomic
def update_user(*, user: UserAccount, payload: Mapping[str, Any]) -> UserAccount:
    """Update profile/hierarchy and optionally replace the encrypted password."""
    if user.is_super:
        raise UserConflictError("超级管理员账号只能通过数据库维护。")
    allowed = {"display_name", "email", "phone", "group_id", "manager_id", "avatar_color", "status"}
    if "status" in payload and payload["status"] not in {"active", "inactive"}:
        raise ValueError("账号状态只能是在职或停用。")
    for field in allowed:
        if field in payload:
            value = payload[field]
            if field in {"group_id", "manager_id"}:
                value = _optional_int(value)
            elif field in {"display_name", "email", "phone", "avatar_color", "status"}:
                value = str(value or "").strip()
            setattr(user, field, value)
    if payload.get("password"):
        try:
            user.password_ciphertext = decrypt_client_password(str(payload["password"]))
        except CryptoPayloadError as exc:
            raise ValueError("密码必须使用 RSA-OAEP-SHA256 加密。") from exc
    user.save()
    if "manager_ids" in payload or "manager_id" in payload:
        ids = set_managers(
            int(user.id), payload.get("manager_ids", [user.manager_id] if user.manager_id else [])
        )
        user.manager_id = ids[0] if ids else None
    if "monthly_approver_ids" in payload:
        set_monthly_approvers(int(user.id), payload["monthly_approver_ids"])
    if "shared_user_ids" in payload:
        set_shared_users(user.id, payload["shared_user_ids"])
    if "role_codes" in payload:
        role_codes = _normalise_role_codes(payload.get("role_codes"))
        roles = list(
            Role.objects.select_for_update().filter(role_code__in=role_codes, status="active")
        )
        if len(roles) != len(set(role_codes)):
            raise ValueError("存在不可用的角色编码。")
        with transaction.atomic():
            UserRole.objects.filter(user_id=user.id).update(status="inactive")
            for index, role in enumerate(roles):
                UserRole.objects.update_or_create(
                    user_id=user.id,
                    role_id=role.id,
                    defaults={"status": "active", "is_default": index == 0},
                )
    if "role_customer_ids" in payload or "role_codes" in payload:
        set_user_customers(user.id, payload.get("role_customer_ids"))
    return user


@transaction.atomic
def delete_user(*, user_id: int, acting_user_id: int) -> UserAccount:
    """Soft-delete a directory user and disable logical memberships."""
    user = UserAccount.objects.exclude(status="deleted").filter(id=user_id).first()
    if user is None:
        raise UserNotFoundError("用户不存在或已被删除。")
    if user.is_super:
        raise UserConflictError("超级管理员账号只能通过数据库维护。")
    if int(user.id) == int(acting_user_id):
        raise UserConflictError("当前登录用户不能删除，请先切换到其他管理员账号。")
    if (
        UserAccount.objects.filter(manager_id=user.id, status="active").exists()
        or UserManager.objects.filter(manager_id=user.id).exists()
    ):
        raise UserConflictError("该用户仍有直属下属，请先调整下属的直属上级。")
    if has_applicants(user.id):
        raise UserConflictError("该用户仍为月报审批人，请先调整月报审批人配置。")
    user.status = "deleted"
    user.deletion_key = user.id
    user.save(update_fields=["status", "deletion_key", "updated_at"])
    UserRole.objects.filter(user_id=user.id, status="active").update(
        status="inactive", is_default=False
    )
    UserGroupMembership.objects.filter(user_id=user.id, status="active").update(status="inactive")
    return user


def serialize_user(user: UserAccount) -> dict[str, Any]:
    return {
        "id": str(user.id),
        "role_customer_ids": user_assignments(user.id),
        "username": user.username,
        "employee_no": user.employee_no,
        "display_name": user.display_name,
        "email": user.email,
        "phone": user.phone,
        "manager_ids": [str(value) for value in ordered_manager_ids(int(user.id))],
        "monthly_approver_ids": [str(value) for value in ordered_ids(int(user.id))],
        "shared_user_ids": [str(value) for value in shared_recipients(int(user.id))],
        "manager_id": str(user.manager_id) if user.manager_id is not None else None,
        "group_id": str(user.group_id) if user.group_id is not None else None,
        "avatar_color": user.avatar_color,
        "status": user.status,
    }


def serialize_role(role: Role) -> dict[str, Any]:
    return {
        "id": str(role.id),
        "role_code": role.role_code,
        "role_name": role.role_name,
        "customer_ids": [str(value) for value in role_customer_ids(role.id)],
        "scope": role.scope,
        "description": role.description,
        "report_template_code": role.report_template_code,
        "role_group_code": role.role_group_code,
        "status": role.status,
        "sort_order": role.sort_order,
    }


def _choose_role(roles: list[Role], requested_role_code: str | None) -> Role:
    if requested_role_code:
        selected = next((role for role in roles if role.role_code == requested_role_code), None)
        if selected is None:
            raise AuthenticationError("当前用户未分配所选角色。")
        return selected
    return roles[0]


def _normalise_role_codes(value: Any) -> list[str]:
    if isinstance(value, str):
        values = [value]
    elif isinstance(value, list):
        values = value
    else:
        values = []
    return list(dict.fromkeys(str(item).strip() for item in values if str(item).strip()))


def _optional_int(value: Any) -> int | None:
    if value in (None, "", 0, "0"):
        return None
    try:
        return int(str(value))
    except (TypeError, ValueError) as exc:
        raise ValueError("组织关系 ID 必须是数字字符串。") from exc
