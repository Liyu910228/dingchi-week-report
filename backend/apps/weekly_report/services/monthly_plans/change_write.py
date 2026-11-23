import json

from django.db import transaction

from apps.approvals.public import approval_history, decide_approval, start_approval
from apps.core.services.id_generator import generate_primary_id

from ... import monthly_plan_change_dao as dao
from ... import monthly_plan_management_dao as plans
from ..monthly_attachments import prepare_tasks
from ..monthly_draft_tasks import restore_draft
from ..monthly_plan_tasks import (
    save_monthly_plan_tasks,
    validate_report_monthly_data,
    validate_tasks,
)
from ..monthly_task_metadata import snapshot_with_metadata, task_content_key
from ..submission_scope import sync_legacy
from . import change_read
from .policy import PlanNotFound, configured_approvers, editable_plan, readable_plan
from .versions import live_snapshot


def locked_change(user, role_code, change_id, *, editable=False):
    candidate = dao.find_change(change_id)
    if not candidate or candidate.status == "deleted":
        raise PlanNotFound("变更申请不存在或已删除。")
    plan = readable_plan(user, role_code, candidate.monthly_plan_id, lock=True)
    change = dao.find_change(change_id, lock=True)
    if editable:
        if int(plan.employee_id) != int(user.id) or plan.role_code != role_code:
            raise PermissionError("只能修改本人当前角色的变更申请。")
        if change.status not in {"draft", "rejected"}:
            raise ValueError("审批中或已通过的变更申请不能修改。")
        configured_approvers(user.id)
    return plan, change


@transaction.atomic
def create(user, role_code, plan_id):
    plan = editable_plan(user, role_code, plan_id)
    if plan.status != "approved":
        raise ValueError("只有已审批通过的月度计划可以申请变更。")
    if dao.active_change(plan.id):
        raise ValueError("已有未完成的变更申请，请先修改或处理该申请。")
    data = json.dumps(live_snapshot(plan), ensure_ascii=False)
    change = dao.create_change(
        monthly_plan_id=plan.id,
        base_revision=plan.revision,
        base_snapshot_json=data,
        proposed_snapshot_json=data,
        created_by=user.id,
    )
    return change_read.detail(user, role_code, change.id)


def normalized_proposal(change, payload):
    base = json.loads(change.base_snapshot_json)
    summary = str(payload.get("summary") or "").strip()

    tasks = validate_tasks(payload["tasks"], allow_incomplete=True)
    for task, raw in zip(tasks, payload["tasks"], strict=True):
        restore_draft(task, raw)
    base_ids = {str(task["id"]) for task in base["tasks"]}
    seen = set()
    for raw, task in zip(payload["tasks"], tasks, strict=True):
        key = str(raw.get("id") or f"draft-{generate_primary_id()}")
        if len(key) > 100 or (key.isdigit() and key not in base_ids) or key in seen:
            raise ValueError("变更任务ID重复或不属于原始计划。")
        task["id"] = key
        seen.add(key)
    reason = payload.get(
        "change_reason", json.loads(change.proposed_snapshot_json).get("change_reason", "")
    )
    if not isinstance(reason, str) or len(reason) > 10000:
        raise ValueError("变更原因必须为文本，最多10000字符。")
    return {**base, "summary": summary, "tasks": tasks, "change_reason": reason.strip()}


def same_content(first, second):
    return first["summary"] == second["summary"] and [
        (task.get("id"), task_content_key(task, allow_incomplete=True)) for task in first["tasks"]
    ] == [
        (task.get("id"), task_content_key(task, allow_incomplete=True)) for task in second["tasks"]
    ]


@transaction.atomic
def save(user, role_code, change_id, payload):
    plan, change = locked_change(user, role_code, change_id, editable=True)
    if int(payload.get("revision", -1)) != change.revision:
        raise ValueError("变更申请已更新，请重新加载。")
    if payload.get("month_key", plan.month_key) != plan.month_key:
        raise ValueError("变更申请不能修改所属月份。")
    payload = {
        **payload,
        "tasks": prepare_tasks(
            payload.get("tasks"),
            user.id,
            plan.id,
            json.loads(change.proposed_snapshot_json)["tasks"],
        ),
    }
    proposed = normalized_proposal(change, payload)
    previous = json.loads(change.proposed_snapshot_json)
    if not same_content(previous, proposed) or previous.get("change_reason", "") != proposed.get(
        "change_reason", ""
    ):
        change.proposed_snapshot_json = json.dumps(proposed, ensure_ascii=False)
        change.status = "draft"
        change.revision += 1
        dao.save_change(change)
    return change_read.detail(user, role_code, change.id)


@transaction.atomic
def submit(user, role_code, change_id):
    plan, change = locked_change(user, role_code, change_id, editable=True)
    if plan.status != "approved" or change.base_revision != plan.revision:
        raise ValueError("原始生效版本已变更，请重新申请变更。")
    base, proposal = (
        json.loads(change.base_snapshot_json),
        json.loads(change.proposed_snapshot_json),
    )
    validate_report_monthly_data(proposal["summary"], proposal["tasks"], base["template_code"])
    if same_content(base, proposal):
        raise ValueError("请修改月度目标或计划后再提交变更。")
    history = approval_history("monthly_plan_change", change.id, user.id, role_code)
    if history and history[0]["status"] == "rejected" and history[0]["revision"] == change.revision:
        raise ValueError("请修改驳回的变更申请后再提交。")
    approvers = configured_approvers(user.id)
    start_approval(
        business_type="monthly_plan_change",
        business_id=change.id,
        applicant_id=user.id,
        revision=change.revision,
        snapshot=proposal,
        approvers=approvers,
    )
    change.status, change.rejection_reason = "pending" if approvers else "approved", ""
    if not approvers:
        publish(plan, change)
    dao.save_change(change)
    return change_read.detail(user, role_code, change.id)


def publish(plan, change):
    if plan.status != "approved" or plan.revision != change.base_revision:
        raise ValueError("生效版本已变更，不能覆盖新的月度计划。")
    proposal = json.loads(change.proposed_snapshot_json)
    current_ids = {str(task["id"]) for task in live_snapshot(plan)["tasks"]}
    tasks = [
        {**task, "id": task["id"] if task["id"] in current_ids else ""}
        for task in proposal["tasks"]
    ]
    save_monthly_plan_tasks(
        employee_id=plan.employee_id,
        role_code=plan.role_code,
        month_key=plan.month_key,
        value=tasks,
    )
    plan.summary = proposal["summary"]
    plan.revision += 1
    plans.save_plan(plan)
    sync_legacy(plan, "monthly")
    change.effective_revision = plan.revision
    change.published_snapshot_json = json.dumps(
        snapshot_with_metadata(live_snapshot(plan), tasks), ensure_ascii=False
    )


@transaction.atomic
def decide(user, role_code, change_id, payload):
    plan, change = locked_change(user, role_code, change_id)
    history = approval_history("monthly_plan_change", change.id, user.id, role_code)
    if change.status != "pending" or not history or not history[0]["can_approve"]:
        raise PermissionError("当前变更审批尚未轮到你或已处理。")
    if payload.get("approval_id") and str(payload["approval_id"]) != history[0]["id"]:
        raise ValueError("审批记录已更新，请刷新列表。")
    if payload.get("action") not in {"approve", "reject"}:
        raise ValueError("审批操作无效。")
    change.status = decide_approval(
        request_id=int(history[0]["id"]),
        user_id=user.id,
        role_code=role_code,
        approve=payload["action"] == "approve",
        reason=payload.get("reason", ""),
    )
    if change.status == "approved":
        publish(plan, change)
    if change.status == "rejected":
        change.rejection_reason = str(payload.get("reason") or "").strip()
    dao.save_change(change)
    return change_read.detail(user, role_code, change.id)


@transaction.atomic
def delete(user, role_code, change_id):
    _, change = locked_change(user, role_code, change_id, editable=True)
    change.status = "deleted"
    dao.save_change(change)
    return {"id": str(change.id), "deleted": True}
