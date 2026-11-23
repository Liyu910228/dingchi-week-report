from apps.accounts.public import (
    account_role_name,
    approval_managers,
    shared_report_owner_ids,
    visible_user_ids,
)

from ... import monthly_plan_management_dao as dao
from ..submission_scope import check_part
from .versions import assigned_root_ids


class PlanNotFound(ValueError):
    pass


def readable_plan(user, role_code, plan_id, *, lock=False):
    plan = dao.find_plan(plan_id, lock=lock)
    if plan is None or plan.status == "deleted":
        raise PlanNotFound("月度计划不存在或已删除。")
    visible = int(plan.employee_id) in visible_user_ids(user, role_code) or int(
        plan.employee_id
    ) in shared_report_owner_ids(user.id)
    if not visible and int(plan.id) not in assigned_root_ids(user.id, role_code):
        raise PermissionError("无权查看该月度计划。")
    return plan


def editable_plan(user, role_code, plan_id):
    plan = readable_plan(user, role_code, plan_id, lock=True)
    check_part(plan)
    if int(plan.employee_id) != int(user.id) or plan.role_code != role_code:
        raise PermissionError("只能修改当前角色下自己的月度计划。")
    if plan.status == "pending":
        raise ValueError("审批期间不允许修改或删除月度计划。")
    configured_approvers(user.id)
    return plan


def configured_approvers(user_id):
    return approval_managers(user_id)


def approval_requirement_message(role_code, month_key, plan):
    location = f"「{account_role_name(role_code)}」→「{month_key} 月度计划」"
    status = plan.status if plan else "missing"
    reasons = {
        "missing": "尚未填写，请进入月度计划页面新增该职位的计划并提交审批，审批通过后再提交周报。",
        "deleted": "已删除，请重新填写该职位的月度计划并提交审批，审批通过后再提交周报。",
        "draft": "当前为草稿，尚未审批通过，请先提交月度计划审批。",
        "pending": "当前待审批，尚未审批通过，请等待审批完成后再提交周报。",
        "rejected": "已被驳回，尚未审批通过，请修改月度计划并重新提交审批。",
    }
    return f"{location}：{reasons.get(status, '尚未审批通过，请进入月度计划页面确认审批状态。')}"


def ensure_approved(user, role_code, month_key, *, missing_message=None):
    plan = dao.find_plan(employee_id=user.id, role_code=role_code, month_key=month_key, lock=True)
    if missing_message and (plan is None or plan.status == "deleted"):
        raise ValueError(missing_message)
    if plan is None or plan.status != "approved":
        raise ValueError(approval_requirement_message(role_code, month_key, plan))
    return plan
