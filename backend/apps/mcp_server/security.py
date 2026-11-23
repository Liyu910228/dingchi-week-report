"""MCP 调用方鉴权与数据范围解析。

通过 user_account.mcp_api_key 定位调用用户，再依据其角色 scope
（self=个人 / team=团队 / all=领导）计算可见的 employee_id 集合。
本模块仅做读取，不修改任何其它模块的代码。
"""
from __future__ import annotations

from typing import Any

from django.db import connection
from django.db.models import Q

from apps.accounts.models import Role, UserAccount, UserRole

# role_scope 字典编码 -> 对外标签
_SCOPE_LABELS = {"self": "personal", "team": "team", "all": "leader"}


def get_caller_by_api_key(api_key: str) -> dict[str, Any] | None:
    """按 mcp_api_key 定位调用用户；非 active 或不存在返回 None。"""
    if not api_key:
        return None
    with connection.cursor() as cur:
        cur.execute(
            "SELECT id, username, employee_no, display_name, status "
            "FROM user_account WHERE mcp_api_key = %s LIMIT 1",
            [api_key],
        )
        row = cur.fetchone()
    if not row:
        return None
    cols = ["id", "username", "employee_no", "display_name", "status"]
    data = dict(zip(cols, row, strict=False))
    if data.get("status") != "active":
        return None
    return data


def _max_scope(scopes: set[str]) -> str:
    """取调用用户多个角色中的最宽数据范围。"""
    if "all" in scopes:
        return "all"
    if "team" in scopes:
        return "team"
    return "self"


def resolve_visible_employee_ids(caller_id: int) -> tuple[str, str, list[int]]:
    """返回 (scope_code, scope_label, employee_ids)。"""
    role_ids = UserRole.objects.filter(
        user_id=caller_id, status="active"
    ).values("role_id")
    roles = Role.objects.filter(id__in=role_ids, status="active")
    scope = _max_scope({r.scope for r in roles})
    label = _SCOPE_LABELS[scope]

    if scope == "self":
        ids = [int(caller_id)]
    elif scope == "all":
        ids = [int(u["id"]) for u in UserAccount.objects.filter(status="active").values("id")]
    else:  # team：本人 + 逻辑下属（manager_id 递归，与 REST 端 visible_employee_ids 一致）
        all_users = list(
            UserAccount.objects.filter(status="active").values("id", "manager_id")
        )
        children: dict[int, list[int]] = {}
        for u in all_users:
            mgr = u["manager_id"]
            if mgr is not None:
                children.setdefault(int(mgr), []).append(int(u["id"]))
        ids = [int(caller_id)]
        pending = [int(caller_id)]
        while pending:
            current = pending.pop()
            for child in children.get(current, []):
                if child not in ids:
                    ids.append(child)
                    pending.append(child)
    return scope, label, ids


def resolve_owner_id(owner: str) -> int | None:
    """按 username / employee_no / display_name 定位用户 id（active）。"""
    owner = (owner or "").strip()
    if not owner:
        return None
    row = (
        UserAccount.objects.filter(
            Q(username=owner) | Q(employee_no=owner) | Q(display_name=owner),
            status="active",
        )
        .values("id")
        .first()
    )
    return int(row["id"]) if row else None
