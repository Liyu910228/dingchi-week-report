"""月度附件读取权限，沿用主单与历史审批参与人范围。"""

from apps.accounts.public import shared_report_owner_ids, visible_user_ids
from apps.approvals.public import participated_business_ids

from .. import monthly_plan_change_dao as changes
from .. import monthly_plan_management_dao as plans
from .. import submission_dao as submissions


def authorize_monthly_file(user, role_code, plan_id):
    plan = plans.find_plan(plan_id)
    if not plan:
        raise PermissionError("无权下载该附件。")
    if plan.employee_id in visible_user_ids(
        user, role_code
    ) or plan.employee_id in shared_report_owner_ids(user.id):
        return
    roots = participated_business_ids(user.id, "monthly_plan", role_code=role_code)
    proposal_ids = participated_business_ids(user.id, "monthly_plan_change", role_code=role_code)
    roots.extend(row.monthly_plan_id for row in changes.changes_by_ids(proposal_ids))
    if plan.id in roots:
        return
    root_ids = participated_business_ids(user.id, "monthly_submission", role_code=role_code)
    change_ids = participated_business_ids(
        user.id, "monthly_submission_change", role_code=role_code
    )
    root_ids.extend(submissions.change_parent_ids(change_ids))
    if plan.submission_id and plan.submission_id in submissions.canonical_ids(root_ids):
        return
    raise PermissionError("无权下载该附件。")
