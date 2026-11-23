import json

from apps.accounts.public import user_profiles
from apps.todos.public import publish

from . import dao


def entry(request, role_code, applicant_name=None):
    if applicant_name is None:
        applicant_name = (
            user_profiles([request.applicant_id])
            .get(int(request.applicant_id), {})
            .get("employee_name")
        )
    applicant_name = applicant_name or "未知提交人"
    month = json.loads(request.snapshot_json).get("month_key", "")
    label = (
        "月度计划变更"
        if request.business_type in {"monthly_plan_change", "monthly_submission_change"}
        else "月度计划"
    )
    return {
        "role_code": role_code,
        "dedupe_key": f"approval:{request.id}",
        "title": f"{month} {applicant_name}的{label}待审批",
        "target": {
            "kind": "monthly_plan_approval",
            "approval_id": str(request.id),
            "role_code": role_code,
        },
    }


def notify(request, approver_id):
    if request.business_type in {
        "monthly_plan",
        "monthly_plan_change",
        "monthly_submission",
        "monthly_submission_change",
    }:
        publish(
            recipient_id=approver_id,
            source="approval",
            **entry(request, dao.step_at(request.id, request.current_step).approver_role_code),
        )
