"""旧变更经主单授权后适配，不改变旧任务或审批ID。"""

from apps.accounts.public import approval_managers

from .. import monthly_plan_change_dao as changes
from .. import monthly_plan_management_dao as plans
from . import submission_read as read
from .monthly_plans import change_read, change_write


def candidate(change_id):
    change = changes.find_change(change_id)
    return change if change and change.status != "deleted" else None


def adapt(user, role_code, data):
    parent = read.accessible(user, role_code, int(data["plan"]["id"]))
    part = read.parts(parent, user, role_code)[0]
    result = {
        **data,
        "managers": approval_managers(parent.employee_id) if parent.employee_id == user.id else [],
        "plan": read.serialize(parent, user, role_code),
        "can_edit": parent.employee_id == user.id
        and data["change"]["status"] in {"draft", "rejected"},
    }
    result["change"] = {**data["change"], "plan_id": str(parent.id)}
    for key in ["snapshot", "base_snapshot"]:
        snapshot = data[key]
        result[key] = {
            "month_key": parent.month_key,
            "summary": snapshot["summary"],
            "change_reason": snapshot.get("change_reason", ""),
            "parts": [
                {**part, "payload": {"summary": snapshot["summary"], "tasks": snapshot["tasks"]}}
            ],
        }
    return result


def dispatch(user, role_code, change_id, action, payload=None):
    change = candidate(change_id)
    if not change:
        raise LookupError("变更申请不存在。")
    plan = plans.find_plan(change.monthly_plan_id)
    read.accessible(user, role_code, plan.id, editable=action != "detail")
    if action == "detail":
        return adapt(user, role_code, change_read.detail(user, role_code, change_id))
    if action == "save":
        parts = payload.get("parts", [])
        if len(parts) != 1 or parts[0].get("role_code") != plan.role_code:
            raise ValueError("历史变更必须保留原职位。")
        data = change_write.save(
            user,
            plan.role_code,
            change_id,
            {
                **parts[0]["payload"],
                "revision": payload.get("revision"),
                "change_reason": payload.get("change_reason", ""),
            },
        )
    elif action == "submit":
        data = change_write.submit(user, plan.role_code, change_id)
    else:
        return change_write.delete(user, plan.role_code, change_id)
    return adapt(user, role_code, data)
