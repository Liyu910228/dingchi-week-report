"""统一主单列表，筛选后分页；审批记录保持节点顺序。"""

from apps.accounts.public import account_role_scope, shared_report_owner_ids, visible_user_ids
from apps.approvals.public import (
    assigned_approval_records,
    assigned_submission_ids_for_position,
    participated_business_ids,
    pending_monthly_count,
)

from .. import monthly_plan_change_dao as old_changes
from .. import submission_dao as dao
from . import reports
from . import submission_approvals as approvals
from . import submission_read as read
from .monthly_plan_tasks import validate_month_key


def list_submissions(user, role_code, kind, filters):
    validate_filters(kind, filters)
    page, size = int(filters.get("page") or 1), int(filters.get("page_size") or 10)
    if page < 1 or not 1 <= size <= 100 or len(str(filters.get("role_code") or "")) > 64:
        raise ValueError("筛选或分页参数无效。")
    view = filters.get("view") or ("mine" if filters.get("employee_scope") == "self" else "members")
    if view not in {"mine", "members", "approvals", "shared"}:
        raise ValueError("列表类型无效。")
    if view == "approvals":
        return list_approvals(user, role_code, filters, page, size)
    visible = [user.id] if view == "mine" else visible_user_ids(user, role_code)
    if view == "members" and account_role_scope(role_code) == "self":
        visible = [user.id]
    if filters.get("employee_scope") == "team" or (
        kind == "monthly" and view == "members" and account_role_scope(role_code) == "team"
    ):
        visible = [value for value in visible if value != user.id]
    if view == "shared":
        visible = shared_report_owner_ids(user.id)
    rows = dao.query(kind, visible, filters)
    total = rows.count()
    return {
        "items": [
            read.serialize(row, user, role_code) for row in rows[(page - 1) * size : page * size]
        ],
        "approvals": [],
        "page": page,
        "page_size": size,
        "total": total,
        "total_pages": (total + size - 1) // size,
        "pending_approval_count": pending_monthly_count(user.id, role_code),
        "has_approval_tasks": has_tasks(user, role_code),
    }


def assigned_ids(user, role_code):
    types = [
        "monthly_submission",
        "monthly_submission_change",
        "monthly_plan",
        "monthly_plan_change",
    ]
    ids = {kind: participated_business_ids(user.id, kind, role_code=role_code) for kind in types}
    parents = set(
        ids["monthly_submission"] + dao.change_parent_ids(ids["monthly_submission_change"])
    )
    legacy_changes = old_changes.changes_by_ids(ids["monthly_plan_change"])
    parents.update(
        dao.parent_ids_for_parts(
            "monthly", ids["monthly_plan"] + [row.monthly_plan_id for row in legacy_changes]
        )
    )
    return ids, parents


def has_tasks(user, role_code):
    return bool(assigned_ids(user, role_code)[1])


def list_approvals(user, role_code, filters, page, size):
    ids, parent_ids = assigned_ids(user, role_code)
    root_filters = {key: value for key, value in filters.items() if key != "status"}
    roots = {
        row.id: row
        for row in dao.query(
            "monthly",
            [],
            root_filters,
            list(parent_ids),
            include_deleted=True,
        )
    }
    if root_filters.get("role_code"):
        # 同月重新创建计划时会复用职位明细，旧的已删除主单因此不再关联明细。
        # 处理过的审批仍按提交时的快照匹配职位，而不是从新计划推断。
        candidates = dao.query(
            "monthly",
            [],
            {key: value for key, value in root_filters.items() if key != "role_code"},
            list(parent_ids),
            include_deleted=True,
        )
        missing = {
            row.id: row for row in candidates if row.status == "deleted" and row.id not in roots
        }
        matched = assigned_submission_ids_for_position(user.id, missing, root_filters["role_code"])
        roots.update({submission_id: missing[submission_id] for submission_id in matched})
    allowed_ids = set(roots)
    for root in roots.values():
        allowed_ids.update(dao.merged_source_ids(root.id))
        allowed_ids.update(row.id for row in dao.part_rows(root, include_deleted=True))
        allowed_ids.update(row.id for row in dao.changes(root.id, include_deleted=True))
        allowed_ids.update(
            row.id
            for row in old_changes.changes_for_plans(
                [part.id for part in dao.part_rows(root, include_deleted=True)],
                include_deleted=True,
            )
        )
    result = assigned_approval_records(
        user.id,
        list(ids),
        list(allowed_ids),
        role_code=role_code,
        status=filters.get("status", ""),
        pending_only=filters.get("pending_only") == "true",
        page=page,
        size=size,
    )
    return {
        "items": [],
        "approvals": [approvals.detail(user, role_code, int(row["id"])) for row in result["items"]],
        "page": page,
        "page_size": size,
        "total": result["total"],
        "total_pages": (result["total"] + size - 1) // size,
        "has_approval_tasks": bool(parent_ids),
        "pending_approval_count": pending_monthly_count(user.id, role_code),
    }


def validate_filters(kind, filters):
    if len(str(filters.get("employee_name") or "")) > 128:
        raise ValueError("姓名筛选不能超过128个字符。")
    if filters.get("month_key"):
        validate_month_key(filters["month_key"])
    for field in ["period_start", "period_end"]:
        if filters.get(field):
            reports._parse_optional_date(filters[field])
    for field in ["employee_id", "group_id"]:
        if filters.get(field) and (not str(filters[field]).isdigit() or int(filters[field]) <= 0):
            raise ValueError("人员或分组ID无效。")
    if filters.get("employee_scope") and filters["employee_scope"] not in {"self", "team"}:
        raise ValueError("人员范围无效。")
    if kind == "weekly" and filters.get("view") == "approvals":
        raise ValueError("周报不支持月度审批视图。")
