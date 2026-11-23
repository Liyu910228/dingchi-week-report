"""Organization and role administration services."""

from __future__ import annotations

import logging
import re
from collections.abc import Mapping
from typing import Any

from django.db import transaction

from apps.dictionary.public import is_active_dictionary_code

from ..dao import (
    deactivate_role_assignments,
    find_role_by_id,
    insert_role,
    list_roles,
    role_code_exists,
    role_has_users,
    save_role,
)
from ..models import OrganizationGroup, Role, UserAccount, UserGroupMembership
from .customer_assignments import set_role_customers

_logger = logging.getLogger(__name__)
_role_code_pattern = re.compile(r"^[a-z][a-z0-9_]*$")
_group_code_pattern = re.compile(r"^[a-z][a-z0-9_]*$")
_role_statuses = {"active", "inactive"}


class RoleNotFoundError(ValueError):
    """The requested role is missing or has already been deleted."""

    code = "ROLE_NOT_FOUND"


class RoleConflictError(ValueError):
    """The requested role operation would make administration unsafe."""

    code = "ROLE_CONFLICT"


class GroupNotFoundError(ValueError):
    """The requested group is missing or has already been deleted."""

    code = "GROUP_NOT_FOUND"


class GroupConflictError(ValueError):
    """The requested group operation would make the hierarchy unsafe."""

    code = "GROUP_CONFLICT"


@transaction.atomic
def create_role(*, payload: Mapping[str, Any]) -> Role:
    role_code = str(payload.get("role_code") or "").strip()
    role_name = str(payload.get("role_name") or "").strip()
    scope = str(payload.get("scope") or "self").strip()
    description = str(payload.get("description") or "").strip()
    report_template_code = str(payload.get("report_template_code") or "").strip()
    role_group_code = str(payload.get("role_group_code") or "").strip()
    _validate_role_fields(
        role_code=role_code,
        role_name=role_name,
        scope=scope,
        report_template_code=report_template_code,
    )
    if len(description) > 255:
        raise ValueError("角色说明不能超过 255 个字符。")
    _validate_role_group_code(role_group_code)
    if role_code_exists(role_code):
        raise RoleConflictError("角色编码已存在，请使用其他编码。")
    role = insert_role(
        role_code=role_code,
        role_name=role_name,
        scope=scope,
        description=description,
        report_template_code=report_template_code,
        role_group_code=role_group_code,
        sort_order=_parse_sort_order(payload.get("sort_order", 0)),
    )
    set_role_customers(role.id, payload.get("customer_ids", []))
    return role


@transaction.atomic
def update_role(*, role_id: int, payload: Mapping[str, Any]) -> Role:
    role = find_role_by_id(role_id, lock=True)
    if role is None:
        raise RoleNotFoundError("角色不存在或已被删除。")

    role_name = str(payload.get("role_name", role.role_name) or "").strip()
    scope = str(payload.get("scope", role.scope) or "").strip()
    report_template_code = str(
        payload.get("report_template_code", role.report_template_code) or ""
    ).strip()
    role_group_code = str(payload.get("role_group_code", role.role_group_code) or "").strip()
    description = str(payload.get("description", role.description) or "").strip()
    _validate_role_fields(
        role_code=role.role_code,
        role_name=role_name,
        scope=scope,
        report_template_code=report_template_code,
    )
    if len(description) > 255:
        raise ValueError("角色说明不能超过 255 个字符。")
    _validate_role_group_code(role_group_code)

    update_fields: list[str] = []
    for field, value in (
        ("role_name", role_name),
        ("scope", scope),
        ("description", description),
        ("report_template_code", report_template_code),
        ("role_group_code", role_group_code),
    ):
        if getattr(role, field) != value:
            setattr(role, field, value)
            update_fields.append(field)
    if "status" in payload:
        status = str(payload["status"] or "").strip()
        if status not in _role_statuses:
            raise ValueError("角色状态只能是 active 或 inactive。")
        if role.status != status:
            role.status = status
            update_fields.append("status")
    if "sort_order" in payload:
        sort_order = _parse_sort_order(payload["sort_order"])
        if role.sort_order != sort_order:
            role.sort_order = sort_order
            update_fields.append("sort_order")
    if "customer_ids" in payload:
        set_role_customers(role.id, payload["customer_ids"])
    return save_role(role, update_fields=update_fields) if update_fields else role


@transaction.atomic
def delete_role(*, role_id: int, acting_role_code: str) -> Role:
    """Soft-delete one role and disable its logical user assignments."""
    role = find_role_by_id(role_id, lock=True)
    if role is None:
        raise RoleNotFoundError("角色不存在或已被删除。")
    if role.role_code == "system_admin":
        raise RoleConflictError("系统管理员角色是系统保留角色，不能删除。")
    if role.role_code == acting_role_code:
        raise RoleConflictError("当前正在使用的角色不能删除，请先切换到其他角色。")

    if role_has_users(int(role.id)):
        raise RoleConflictError("该职位已挂载用户，不支持删除，请先调整用户职位。")
    role.status = "deleted"
    role.deletion_key = role.id
    save_role(role, update_fields=["status", "deletion_key"])
    assignment_count = deactivate_role_assignments(int(role.id))
    _logger.info(
        "Role soft-deleted",
        extra={
            "action": "delete_role",
            "role_id": str(role.id),
            "role_code": role.role_code,
            "assignment_count": assignment_count,
        },
    )
    return role


def get_role_list() -> list[dict[str, Any]]:
    """Return all role configurations that have not been deleted."""
    return list_roles()


def _validate_role_fields(
    *, role_code: str, role_name: str, scope: str, report_template_code: str
) -> None:
    if not role_code or not role_name:
        raise ValueError("职位编码和职位名称不能为空。")
    if len(role_code) > 64 or not _role_code_pattern.fullmatch(role_code):
        raise ValueError("角色编码必须以小写字母开头，只能包含小写字母、数字和下划线。")
    if len(role_name) > 128 or len(report_template_code) > 64:
        raise ValueError("角色名称或模板编码超过允许长度。")
    if not is_active_dictionary_code("role_scope", scope):
        raise ValueError("数据范围不是有效的字典项。")
    if report_template_code and not is_active_dictionary_code(
        "report_template", report_template_code
    ):
        raise ValueError("周报模板不是有效的字典项。")


def _parse_sort_order(value: Any) -> int:
    try:
        sort_order = int(value or 0)
    except (TypeError, ValueError) as exc:
        raise ValueError("角色排序值必须是非负整数。") from exc
    if sort_order < 0:
        raise ValueError("角色排序值必须是非负整数。")
    return sort_order


@transaction.atomic
def create_group(*, payload: Mapping[str, Any]) -> OrganizationGroup:
    group_code = str(payload.get("group_code") or "").strip()
    group_name = str(payload.get("group_name") or "").strip()
    if not group_code or not group_name:
        raise ValueError("分组编码和分组名称不能为空。")
    if len(group_code) > 64 or not _group_code_pattern.fullmatch(group_code):
        raise ValueError("分组编码必须以小写字母开头，只能包含小写字母、数字和下划线。")
    if len(group_name) > 128:
        raise ValueError("分组名称超过允许长度。")
    if OrganizationGroup.objects.filter(group_code=group_code).exists():
        raise GroupConflictError("分组编码已存在，请使用其他编码。")
    parent_group_id = payload.get("parent_group_id")
    parsed_parent_id = int(parent_group_id) if parent_group_id else None
    if (
        parsed_parent_id is not None
        and not OrganizationGroup.objects.filter(id=parsed_parent_id, status="active").exists()
    ):
        raise GroupConflictError("上级分组不存在或已停用。")
    return OrganizationGroup.objects.create(
        group_code=group_code,
        group_name=group_name,
        description=str(payload.get("description") or "").strip(),
        parent_group_id=parsed_parent_id,
    )


@transaction.atomic
def update_group(*, group: OrganizationGroup, payload: Mapping[str, Any]) -> OrganizationGroup:
    for field in ("group_name", "description", "status"):
        if field in payload:
            setattr(group, field, str(payload[field] or "").strip())
    if "parent_group_id" in payload:
        parsed_parent_id = int(payload["parent_group_id"]) if payload["parent_group_id"] else None
        if parsed_parent_id == int(group.id):
            raise GroupConflictError("分组不能将自己设置为上级分组。")
        if (
            parsed_parent_id is not None
            and not OrganizationGroup.objects.filter(id=parsed_parent_id, status="active").exists()
        ):
            raise GroupConflictError("上级分组不存在或已停用。")
        if parsed_parent_id is not None and _is_descendant(
            group_id=int(group.id), candidate_parent_id=parsed_parent_id
        ):
            raise GroupConflictError("分组不能移动到自己的下级分组中。")
        group.parent_group_id = parsed_parent_id
    group.save()
    return group


@transaction.atomic
def delete_group(*, group_id: int) -> OrganizationGroup:
    """Soft-delete an empty group while preserving historical report links."""
    group = OrganizationGroup.objects.exclude(status="deleted").filter(id=group_id).first()
    if group is None:
        raise GroupNotFoundError("分组不存在或已被删除。")
    if OrganizationGroup.objects.filter(parent_group_id=group.id, status="active").exists():
        raise GroupConflictError("该分组包含下级分组，请先移动或删除下级分组。")
    if UserAccount.objects.filter(group_id=group.id, status="active").exists():
        raise GroupConflictError("该分组仍有在职用户，不能删除。")
    if UserGroupMembership.objects.filter(group_id=group.id, status="active").exists():
        raise GroupConflictError("该分组仍有用户成员，不能删除。")
    if Role.objects.filter(role_group_code=group.group_code).exclude(status="deleted").exists():
        raise GroupConflictError("该分组仍有关联角色，不能删除。")
    if group.is_system:
        raise GroupConflictError("系统预设分组不能删除。")
    group.status = "deleted"
    group.save(update_fields=["status", "updated_at"])
    return group


def can_manage_directory(role_code: str) -> bool:
    return role_code in {"president", "system_admin"}


def serialize_group(group: OrganizationGroup) -> dict[str, Any]:
    return {
        "id": str(group.id),
        "group_code": group.group_code,
        "group_name": group.group_name,
        "description": group.description,
        "parent_group_id": str(group.parent_group_id) if group.parent_group_id else None,
        "is_system": group.is_system,
        "status": group.status,
    }


def _is_descendant(*, group_id: int, candidate_parent_id: int) -> bool:
    """Return whether candidate_parent_id is below group_id in the logical tree."""
    visited: set[int] = set()
    current_id: int | None = candidate_parent_id
    while current_id is not None and current_id not in visited:
        if current_id == group_id:
            return True
        visited.add(current_id)
        current_id = (
            OrganizationGroup.objects.filter(id=current_id)
            .values_list("parent_group_id", flat=True)
            .first()
        )
    return False


def _validate_role_group_code(role_group_code: str) -> None:
    if not role_group_code:
        return
    if not OrganizationGroup.objects.filter(
        group_code=role_group_code,
        status="active",
    ).exists():
        raise ValueError("角色分组不存在或已停用。")
