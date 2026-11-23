"""填写职位验证与已有记录所属职位解析，不改变登录会话。"""

from apps.accounts.public import assigned_role_codes

from .. import dao, monthly_plan_change_dao, monthly_plan_management_dao


def resolve_reporting_role(user, default_role, selected_role="", identifiers=None):
    codes = assigned_role_codes(user.id)
    if selected_role and selected_role not in codes:
        raise PermissionError("当前用户未分配该职位。")
    identifiers = identifiers or {}
    plan = None
    if identifiers.get("change_id"):
        change = monthly_plan_change_dao.find_change(identifiers["change_id"])
        if change:
            plan = monthly_plan_management_dao.find_plan(change.monthly_plan_id)
    elif identifiers.get("plan_id"):
        plan = monthly_plan_management_dao.find_plan(identifiers["plan_id"])
    if plan and int(plan.employee_id) == int(user.id) and plan.role_code in codes:
        return plan.role_code
    report_id = identifiers.get("report_id")
    if not report_id and identifiers.get("attachment_id"):
        report_id = dao.attachment_report_id(int(identifiers["attachment_id"]))
    if report_id:
        report = dao.get_report_header(int(report_id))
        if report and int(report["employee_id"]) == int(user.id) and report["role_code"] in codes:
            return report["role_code"]
    if any(
        key in identifiers
        for key in ("plan_id", "change_id", "report_id", "attachment_id", "approval_id")
    ):
        return default_role
    return selected_role or default_role
