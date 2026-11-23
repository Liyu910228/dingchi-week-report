import json

from django.db import transaction

from apps.accounts.public import account_role_name, account_role_scope
from apps.approvals.public import approval_history, decide_approval, start_approval

from ... import monthly_plan_change_dao as changes
from ... import monthly_plan_management_dao as dao
from .. import reports
from ..monthly_attachments import prepare_tasks
from ..monthly_plan_tasks import (
    list_monthly_plan_tasks,
    save_monthly_plan_tasks,
    validate_month_key,
    validate_report_monthly_data,
)
from ..monthly_task_metadata import snapshot_with_metadata, task_content_key
from ..submission_scope import sync_legacy
from .policy import configured_approvers, editable_plan, readable_plan
from .read import detail


def snapshot(plan):
    return {
        "role_code": plan.role_code,
        "role_name": account_role_name(plan.role_code),
        "summary": plan.summary,
        "tasks": list_monthly_plan_tasks(
            employee_id=plan.employee_id, role_code=plan.role_code, month_key=plan.month_key
        ),
        "template_code": plan.template_code,
        "month_key": plan.month_key,
    }


def record_change(plan, user_id, action, before, after):
    old = {str(task.get("id")): task for task in before.get("tasks", [])}
    new = {str(task.get("id")): task for task in after.get("tasks", [])}
    changes = {
        "summary": {"before": before.get("summary", ""), "after": after.get("summary", "")},
        "added": [new[key] for key in new.keys() - old.keys()],
        "deleted": [old[key] for key in old.keys() - new.keys()],
        "modified": [
            {"before": old[key], "after": new[key]}
            for key in old.keys() & new.keys()
            if any(
                old[key].get(field) != new[key].get(field)
                for field in [
                    "scope_group_key",
                    "task_group_key",
                    "content_group_key",
                    "scope_name",
                    "work_task",
                    "work_content",
                    "output_description",
                    "planned_date",
                    "sort_order",
                    "task_source",
                    "task_template",
                    "task_values",
                    "dimension_source",
                    "dimension_template",
                    "dimension_values",
                    "customer_source",
                    "customer_template",
                    "customer_values",
                    "attachments",
                ]
            )
        ],
    }
    dao.append_revision(
        monthly_plan_id=plan.id,
        revision=plan.revision,
        changed_by=user_id,
        action=action,
        snapshot_json=json.dumps(after, ensure_ascii=False),
        changes_json=json.dumps(changes, ensure_ascii=False),
    )


@transaction.atomic
def save(user, role_code, payload, plan_id=None, *, allow_incomplete=True):
    if account_role_scope(role_code) == "all":
        raise PermissionError("全员角色仅支持查看和审批。")
    configured_approvers(user.id)
    before = {}
    if plan_id:
        plan = editable_plan(user, role_code, plan_id)
        if plan.status == "approved":
            raise ValueError("已生效月度计划不能直接修改，请申请变更子流程。")
        if int(payload.get("revision", -1)) != plan.revision:
            raise ValueError("计划已被更新，请重新加载后再修改。")
        if payload.get("month_key", plan.month_key) != plan.month_key:
            raise ValueError("已有计划不能变更所属月份。")
        before = snapshot(plan)
    else:
        month = validate_month_key(str(payload.get("month_key") or ""))
        template = reports.resolve_role_template(role_code)["template_code"]
        plan = dao.find_plan(employee_id=user.id, role_code=role_code, month_key=month, lock=True)
        if plan and plan.status != "deleted":
            raise ValueError("该月份已有月度计划，请修改原计划。")
        plan = plan or dao.create_plan(
            employee_id=user.id, role_code=role_code, month_key=month, group_id=user.group_id
        )
        plan.template_code = template
    if not plan.template_code:
        plan.template_code = reports.resolve_role_template(role_code)["template_code"]
    summary = str(payload.get("summary") or "").strip()
    tasks = prepare_tasks(payload.get("tasks"), user.id, plan.id, before.get("tasks", []))
    if not allow_incomplete and len(summary) > 10000:
        raise ValueError("月度目标填写内容校验不通过：月度目标不能超过10000字符，请缩短后提交。")
    if not allow_incomplete:
        validate_report_monthly_data(summary, tasks, plan.template_code)
    current_content = [
        task_content_key(task, allow_incomplete=allow_incomplete)
        for task in before.get("tasks", [])
    ]
    next_content = [task_content_key(task, allow_incomplete=allow_incomplete) for task in tasks]
    if before and summary == before["summary"] and current_content == next_content:
        if plan.status == "rejected" and not allow_incomplete:
            raise ValueError("请先修改驳回的内容，再重新提交。")
        return detail(user, role_code, plan.id)
    plan.summary, plan.status = summary, "draft"
    plan.revision += 1
    dao.save_plan(plan)
    sync_legacy(plan, "monthly")
    save_monthly_plan_tasks(
        employee_id=plan.employee_id,
        role_code=plan.role_code,
        month_key=plan.month_key,
        value=tasks,
        allow_incomplete=allow_incomplete,
    )
    record_change(
        plan,
        user.id,
        "update" if before else "create",
        before,
        snapshot_with_metadata(snapshot(plan), tasks, allow_incomplete=allow_incomplete),
    )
    return detail(user, role_code, plan.id)


@transaction.atomic
def submit(user, role_code, plan_id):
    plan = editable_plan(user, role_code, plan_id)
    if plan.status == "approved":
        raise ValueError("已通过计划需先修改内容再重新提交。")
    history = approval_history("monthly_plan", int(plan.id), user.id, role_code)
    if history and history[0]["status"] == "rejected" and history[0]["revision"] == plan.revision:
        raise ValueError("请先修改驳回的计划，再重新提交。")
    data = snapshot(plan)
    validate_report_monthly_data(plan.summary, data["tasks"], plan.template_code)
    approvers = configured_approvers(user.id)
    start_approval(
        business_type="monthly_plan",
        business_id=int(plan.id),
        applicant_id=int(user.id),
        revision=plan.revision,
        snapshot=data,
        approvers=approvers,
    )
    plan.status, plan.rejection_reason = "pending" if approvers else "approved", ""
    dao.save_plan(plan)
    sync_legacy(plan, "monthly")
    return detail(user, role_code, plan.id)


@transaction.atomic
def decide(user, role_code, plan_id, payload):
    plan = readable_plan(user, role_code, plan_id, lock=True)
    if plan.status != "pending":
        raise ValueError("该计划当前不在审批中。")
    history = approval_history("monthly_plan", int(plan.id), user.id, role_code)
    if not history or not history[0]["can_approve"]:
        raise PermissionError("当前审批尚未轮到你。")
    if payload.get("approval_id") and str(payload["approval_id"]) != history[0]["id"]:
        raise ValueError("审批记录已更新，请刷新列表后再操作。")
    action = payload.get("action")
    if action not in {"approve", "reject"}:
        raise ValueError("审批操作无效。")
    plan.status = decide_approval(
        request_id=int(history[0]["id"]),
        user_id=user.id,
        role_code=role_code,
        approve=action == "approve",
        reason=payload.get("reason", ""),
    )
    if plan.status == "rejected":
        plan.rejection_reason = str(payload.get("reason") or "").strip()
    dao.save_plan(plan)
    sync_legacy(plan, "monthly")
    return detail(user, role_code, plan.id)


@transaction.atomic
def delete(user, role_code, plan_id):
    plan = editable_plan(user, role_code, plan_id)
    if plan.status == "approved":
        raise ValueError("审批通过的月度计划不能删除，请申请变更。")
    if changes.active_change(plan.id):
        raise ValueError("存在未完成的变更申请，不能删除主流程。")
    if plan.status != "draft":
        raise ValueError("仅草稿状态的月度计划支持删除。")
    before = snapshot(plan)
    plan.status = "deleted"
    plan.revision += 1
    dao.save_plan(plan)
    sync_legacy(plan, "monthly")
    record_change(plan, user.id, "delete", before, {})
    return {"id": str(plan.id), "deleted": True}
