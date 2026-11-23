import json

from apps.accounts.public import account_role_name
from apps.approvals.public import approval_history

from ... import monthly_plan_change_dao as dao
from .policy import PlanNotFound, readable_plan
from .read import serialize_plan
from .versions import change_row


def detail(user, role_code, change_id):
    change = dao.find_change(change_id)
    if not change or change.status == "deleted":
        raise PlanNotFound("变更申请不存在或已删除。")
    plan = readable_plan(user, role_code, change.monthly_plan_id)
    own = int(plan.employee_id) == int(user.id) and plan.role_code == role_code
    return {
        "plan": {
            **serialize_plan(plan, user.id, role_code=role_code),
            "role_name": account_role_name(plan.role_code),
        },
        "change": change_row(change),
        "base_snapshot": json.loads(change.base_snapshot_json),
        "snapshot": json.loads(change.proposed_snapshot_json),
        "approvals": approval_history("monthly_plan_change", change.id, user.id, role_code),
        "can_edit": own and change.status in {"draft", "rejected"},
    }
