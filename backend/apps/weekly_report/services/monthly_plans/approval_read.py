import json

from apps.accounts.public import account_role_name, account_role_names, user_profiles
from apps.approvals.public import assigned_approval_records, assigned_record, pending_monthly_count

from ... import monthly_plan_change_dao as changes
from ... import monthly_plan_management_dao as dao
from .versions import assigned_root_ids


def list_assigned_approvals(user, role_code, filters, page, size):
    ids = assigned_root_ids(user.id, role_code)
    plans = {int(plan.id): plan for plan in dao.approval_plans(ids, filters)}
    children = {
        int(child.id): child
        for child in changes.changes_for_plans(list(plans), include_deleted=True)
    }
    result = assigned_approval_records(
        user.id,
        ["monthly_plan", "monthly_plan_change"],
        list(plans) + list(children),
        role_code=role_code,
        status=filters.get("status", ""),
        pending_only=filters.get("pending_only") == "true",
        page=page,
        size=size,
    )
    profiles = user_profiles([plan.employee_id for plan in plans.values()])
    names = account_role_names({plan.role_code for plan in plans.values()})
    records = []
    for row in result["items"]:
        child = (
            children.get(int(row["business_id"]))
            if row["business_type"] == "monthly_plan_change"
            else None
        )
        plan = plans[int(child.monthly_plan_id) if child else int(row["business_id"])]
        records.append(
            {
                **row,
                "plan_id": str(plan.id),
                "month_key": plan.month_key,
                "role_code": plan.role_code,
                "role_name": names.get(plan.role_code, plan.role_code),
                "process_type": "change" if child else "initial",
                "change_id": str(child.id) if child else None,
                "base_snapshot": json.loads(child.base_snapshot_json) if child else None,
                **profiles.get(int(plan.employee_id), {}),
            }
        )
    return {
        "items": [],
        "approvals": records,
        "page": page,
        "page_size": size,
        "total": result["total"],
        "total_pages": (result["total"] + size - 1) // size,
        "has_approval_tasks": bool(ids),
        "pending_approval_count": pending_monthly_count(user.id, role_code),
    }


def detail_assigned(user, role_code, approval_id):
    record = assigned_record(user.id, approval_id, role_code)
    if record["business_type"] not in {"monthly_plan", "monthly_plan_change"}:
        raise ValueError("审批类型无效。")
    child = (
        changes.find_change(int(record["business_id"]))
        if record["business_type"] == "monthly_plan_change"
        else None
    )
    if record["business_type"] == "monthly_plan_change" and not child:
        raise ValueError("变更申请不存在。")
    plan_id = child.monthly_plan_id if child else int(record["business_id"])
    plan = dao.find_plan(plan_id)
    if not plan:
        raise ValueError("月度计划不存在。")
    return {
        **record,
        "plan_id": str(plan.id),
        "month_key": plan.month_key,
        "role_code": plan.role_code,
        "role_name": account_role_name(plan.role_code),
        "process_type": "change" if child else "initial",
        "change_id": str(child.id) if child else None,
        "base_snapshot": json.loads(child.base_snapshot_json) if child else None,
        **user_profiles([plan.employee_id]).get(int(plan.employee_id), {}),
    }
