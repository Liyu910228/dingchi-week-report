from apps.accounts.public import (
    account_role_name,
    account_role_scope,
    approval_managers,
    report_roles,
    user_profiles,
    visible_user_ids,
)
from apps.approvals.public import approval_history, participated_business_ids, pending_monthly_count

from ... import monthly_plan_change_dao as changes
from ... import monthly_plan_management_dao as dao
from .. import reports
from ..monthly_plan_tasks import list_monthly_plan_tasks, validate_month_key
from .approval_read import list_assigned_approvals
from .policy import approval_requirement_message, readable_plan
from .versions import approved_versions, assigned_root_ids, change_row


def serialize_plan(plan, user_id, profiles=None, role_code=None):
    profile = (profiles or user_profiles([plan.employee_id])).get(int(plan.employee_id), {})
    can_approve = (
        int(plan.id)
        in participated_business_ids(user_id, "monthly_plan", True, role_code=role_code)
        if role_code
        else False
    )
    children = [
        change_row(child, include_snapshots=False) for child in changes.changes_for_plan(plan.id)
    ]
    return {
        "id": str(plan.id),
        "employee_id": str(plan.employee_id),
        "role_code": plan.role_code,
        "role_name": account_role_name(plan.role_code),
        "group_id": str(plan.group_id) if plan.group_id else None,
        "month_key": plan.month_key,
        "summary": plan.summary,
        "template_code": plan.template_code,
        "status": plan.status,
        "revision": plan.revision,
        "rejection_reason": plan.rejection_reason,
        "updated_at": plan.updated_at.isoformat(),
        "created_at": plan.created_at.isoformat(),
        "can_approve": can_approve,
        "children": children,
        "can_create_change": plan.status == "approved"
        and not any(child["status"] in {"draft", "pending", "rejected"} for child in children),
        **profile,
    }


def context(user, role_code):
    warning = ""
    try:
        managers = approval_managers(user.id)
    except ValueError as exc:
        managers, warning = [], str(exc)
    template_code = ""
    if account_role_scope(role_code) != "all":
        try:
            template_code = reports.resolve_role_template(role_code)["template_code"]
        except ValueError as exc:
            warning = str(exc)
    return {
        "managers": managers,
        "warning": warning,
        "template_code": template_code,
        "can_create": bool(template_code and not warning),
        "has_approval_tasks": bool(assigned_root_ids(user.id, role_code)),
        "pending_approval_count": pending_monthly_count(user.id, role_code),
    }


def list_plans(user, role_code, filters):
    if len(str(filters.get("role_code") or "")) > 64:
        raise ValueError("职位筛选编码不能超过64字符。")
    visible = visible_user_ids(user, role_code)
    page, size = int(filters.get("page", 1)), int(filters.get("page_size", 10))
    if page < 1 or not 1 <= size <= 100:
        raise ValueError("分页参数无效。")
    view = filters.get("view", "")
    scope = account_role_scope(role_code)
    if view not in {"", "mine", "members", "approvals"}:
        raise ValueError("月度计划列表类型无效。")
    if (view == "mine" and scope == "all" and not report_roles(user.id)) or (
        view == "members" and scope == "self"
    ):
        raise PermissionError("当前角色无权访问该月度计划列表。")
    if view == "approvals":
        return list_assigned_approvals(user, role_code, filters, page, size)
    total, items = dao.paginated_plans(
        visible_ids=[user.id] if view == "mine" else visible,
        own_role=None,
        pending_ids=participated_business_ids(user.id, "monthly_plan", True, role_code=role_code)
        if not view and filters.get("pending_only") == "true"
        else None,
        filters=filters,
        page=page,
        size=size,
        exclude_employee=user.id if view == "members" and scope == "team" else None,
    )
    profiles = user_profiles([plan.employee_id for plan in items])
    return {
        "items": [
            {
                **serialize_plan(plan, user.id, profiles, role_code),
                **({"can_approve": False} if view else {}),
            }
            for plan in items
        ],
        "approvals": _list_history(items, profiles, user.id, role_code) if not view else [],
        "page": page,
        "page_size": size,
        "total": total,
        "total_pages": (total + size - 1) // size,
        "has_approval_tasks": bool(assigned_root_ids(user.id, role_code)),
        "pending_approval_count": pending_monthly_count(user.id, role_code),
    }


def _list_history(items, profiles, user_id, role_code):
    return [
        {
            **row,
            "plan_id": str(plan.id),
            "month_key": plan.month_key,
            "employee_name": profiles.get(int(plan.employee_id), {}).get("employee_name", ""),
        }
        for plan in items
        for row in approval_history("monthly_plan", int(plan.id), user_id, role_code)
    ]


def detail(user, role_code, plan_id):
    plan = readable_plan(user, role_code, plan_id)
    tasks = list_monthly_plan_tasks(
        employee_id=plan.employee_id, role_code=plan.role_code, month_key=plan.month_key
    )
    from ..monthly_task_live_progress import progress_history

    return {
        "plan": {
            **serialize_plan(plan, user.id, role_code=role_code),
            "role_name": account_role_name(plan.role_code),
        },
        "tasks": tasks,
        "progress_history": progress_history([int(task["id"]) for task in tasks]),
        "approvals": approval_history("monthly_plan", int(plan.id), user.id, role_code),
        "history": approved_versions(plan, user.id),
        "can_edit": int(plan.employee_id) == int(user.id)
        and plan.role_code == role_code
        and plan.status in {"draft", "rejected"},
        "can_create_change": int(plan.employee_id) == int(user.id)
        and plan.role_code == role_code
        and plan.status == "approved"
        and not changes.active_change(plan.id),
    }


def gate(user, role_code, month_key):
    month_key = validate_month_key(month_key)
    plan = dao.find_plan(employee_id=user.id, role_code=role_code, month_key=month_key)
    approved = bool(plan and plan.status == "approved")
    return {
        "approved": approved,
        "message": ""
        if approved
        else approval_requirement_message(role_code, month_key, plan),
        "plan": serialize_plan(plan, user.id, role_code=role_code)
        if plan and plan.status != "deleted"
        else None,
        "tasks": list_monthly_plan_tasks(
            employee_id=user.id, role_code=role_code, month_key=month_key
        )
        if plan
        else [],
    }
