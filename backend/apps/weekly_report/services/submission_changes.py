"""统一月度主单变更：待审批提案不会覆盖已生效的职位明细。"""

import json

from django.db import transaction

from apps.accounts.public import account_role_name, approval_managers
from apps.approvals.public import approval_history, start_approval

from .. import submission_dao as dao
from . import submission_legacy_changes as legacy
from . import submission_read as read
from .legacy_monthly_positions import expanded_snapshot, needs_expansion, source_rows
from .monthly_attachments import prepare_tasks
from .monthly_plan_tasks import save_monthly_plan_tasks
from .monthly_plans import write as monthly_write
from .monthly_submission_validation import validate_monthly_parts
from .monthly_task_metadata import snapshot_with_metadata
from .submission_scope import aggregate_write
from .submission_write import content_key, validate_parts


def detail(user, role_code, change_id):
    if legacy.candidate(change_id):
        return legacy.dispatch(user, role_code, change_id, "detail")
    change = dao.find_change(change_id)
    if not change:
        raise LookupError("变更申请不存在。")
    parent = read.accessible(user, role_code, change.submission_id)
    proposal = json.loads(change.proposed_snapshot_json)
    plan = read.serialize(parent, user, role_code)
    plan["role_name"] = " / ".join(
        part.get("role_name") or part["role_code"] for part in proposal["parts"]
    )
    return {
        "plan": plan,
        "change": read.serialize_change(change),
        "base_snapshot": json.loads(change.base_snapshot_json),
        "snapshot": json.loads(change.proposed_snapshot_json),
        "approvals": approval_history("monthly_submission_change", change.id, user.id, role_code),
        "can_edit": parent.employee_id == user.id and change.status in {"draft", "rejected"},
        "managers": approval_managers(parent.employee_id) if parent.employee_id == user.id else [],
    }


def preview(user, role_code, submission_id):
    """只读准备变更，不落库；提交时再次校验版本和未完成申请。"""
    parent = read.accessible(user, role_code, submission_id, editable=True)
    if (
        parent.kind != "monthly"
        or parent.status != "approved"
        or not read.serialize(parent, user, role_code)["can_create_change"]
    ):
        raise ValueError("当前月度计划不能申请变更。")
    snapshot = (
        expanded_snapshot(parent, user)
        if needs_expansion(parent, user)
        else read.snapshot(parent, user, role_code)
    )
    plan = read.serialize(parent, user, role_code)
    plan["role_name"] = " / ".join(part["role_name"] for part in snapshot["parts"])
    return {
        "plan": plan,
        "change": {
            "id": "",
            "plan_id": str(parent.id),
            "status": "draft",
            "revision": 0,
            "base_revision": parent.revision,
            "summary": snapshot["summary"],
            "rejection_reason": "",
            "created_at": "",
            "updated_at": "",
        },
        "base_snapshot": snapshot,
        "snapshot": json.loads(json.dumps(snapshot)),
        "approvals": [],
        "can_edit": True,
        "managers": approval_managers(user.id),
    }


def change_reason(payload, default=""):
    value = payload.get("change_reason", default)
    if not isinstance(value, str) or len(value) > 10000:
        raise ValueError("变更原因必须为文本，最多10000字符。")
    return value.strip()


@transaction.atomic
@aggregate_write
def create(user, role_code, submission_id, payload=None):
    parent = read.accessible(user, role_code, submission_id, lock=True, editable=True)
    if (
        parent.kind != "monthly"
        or parent.status != "approved"
        or not read.serialize(parent, user, role_code)["can_create_change"]
    ):
        raise ValueError("当前月度计划不能申请变更。")
    if payload is not None and int(payload.get("base_revision", -1)) != parent.revision:
        raise ValueError("原始生效版本已变更，请重新加载后申请变更。")
    baseline = (
        expanded_snapshot(parent, user)
        if needs_expansion(parent, user)
        else read.snapshot(parent, user, role_code)
    )
    if baseline.get("expand_legacy_positions"):
        source_rows(parent, baseline)
        if payload is not None:
            incoming = {
                part.get("role_code"): part
                for part in payload.get("parts", [])
                if isinstance(part, dict)
            }
            for source in baseline["parts"]:
                sent = incoming.get(source["role_code"], {})
                if any(
                    sent.get(field) != source.get(field)
                    for field in ["source_plan_id", "source_revision", "source_submission_id"]
                ):
                    raise ValueError("来源月度计划已更新，请重新加载变更页面。")
    data = json.dumps(baseline, ensure_ascii=False)
    change = dao.create_change(
        submission_id=parent.id,
        base_revision=parent.revision,
        base_snapshot_json=data,
        proposed_snapshot_json=data,
    )
    if payload is not None:
        result = save(user, role_code, change.id, {**payload, "revision": 0})
        return submit(user, role_code, change.id) if payload.get("submit") is True else result
    return detail(user, role_code, change.id)


@transaction.atomic
@aggregate_write
def save(user, role_code, change_id, payload):
    if legacy.candidate(change_id):
        return legacy.dispatch(user, role_code, change_id, "save", payload)
    change = dao.find_change(change_id, True)
    if not change:
        raise LookupError("变更申请不存在。")
    parent = read.accessible(user, role_code, change.submission_id, lock=True, editable=True)
    if (
        change.status not in {"draft", "rejected"}
        or parent.status != "approved"
        or change.base_revision != parent.revision
    ):
        raise ValueError("当前变更不可编辑或生效版本已更新。")
    if int(payload.get("revision", -1)) != change.revision:
        raise ValueError("变更内容已更新，请刷新。")
    parts = payload.get("parts")
    baseline = json.loads(change.base_snapshot_json)
    expanding = baseline.get("expand_legacy_positions", False)
    validate_parts(user, parts, None if expanding else parent)
    base_parts = {part["role_code"]: part for part in baseline["parts"]}
    existing = (
        source_rows(parent, baseline)
        if expanding
        else {row.role_code: row for row in dao.part_rows(parent)}
    )
    if set(base_parts) != {part["role_code"] for part in parts}:
        raise ValueError("变更必须保留原主单的职位集合。")
    for part in parts:
        row = existing[part["role_code"]]
        part["template_code"] = base_parts[part["role_code"]]["template_code"]
        data = part.get("payload") or {}
        previous = monthly_write.snapshot(row)["tasks"] if row else []
        try:
            data["tasks"] = prepare_tasks(
                data.get("tasks"), user.id, row.id if row else None, previous
            )
        except (ValueError, PermissionError) as exc:
            raise type(exc)(f"{account_role_name(part['role_code'])}：{exc}") from exc
    change.proposed_snapshot_json = json.dumps(
        {
            "month_key": parent.month_key,
            "change_reason": change_reason(
                payload, json.loads(change.proposed_snapshot_json).get("change_reason", "")
            ),
            "summary": " / ".join(part["payload"].get("summary", "") for part in parts),
            "parts": parts,
        },
        ensure_ascii=False,
    )
    change.revision += 1
    change.status = "draft"
    dao.save(change)
    return detail(user, role_code, change.id)


def publish(parent, change, user):
    if parent.status != "approved" or parent.revision != change.base_revision:
        raise ValueError("生效版本已变更，不能覆盖。")
    baseline = json.loads(change.base_snapshot_json)
    parts = {part["role_code"]: part for part in json.loads(change.proposed_snapshot_json)["parts"]}
    if baseline.get("expand_legacy_positions"):
        sources = source_rows(parent, baseline)
        rows = []
        for code, part in parts.items():
            row = sources[code]
            if row is None:
                row = dao.create_monthly_part(
                    employee_id=parent.employee_id,
                    role_code=code,
                    month_key=parent.month_key,
                    group_id=parent.group_id,
                    template_code=part["template_code"],
                    status="approved",
                    submission_id=parent.id,
                )
            elif row.submission_id and row.submission_id != parent.id:
                dao.merge_source(row.submission_id, parent.id)
                dao.attach("monthly", row.id, parent.id)
            row.submission_id = parent.id
            part["payload"]["tasks"] = prepare_tasks(
                part["payload"]["tasks"],
                parent.employee_id,
                row.id,
                monthly_write.snapshot(row)["tasks"],
            )
            rows.append(row)
        parent.legacy = False
        parent.active_key = f"monthly:{parent.employee_id}:{parent.month_key}"
    else:
        rows = dao.part_rows(parent)
    for row in rows:
        proposal = parts[row.role_code]["payload"]
        before = monthly_write.snapshot(row)
        save_monthly_plan_tasks(
            employee_id=row.employee_id,
            role_code=row.role_code,
            month_key=row.month_key,
            value=proposal["tasks"],
        )
        row.summary = proposal["summary"]
        row.revision += 1
        dao.save(row)
        monthly_write.record_change(
            row,
            user.id,
            "update",
            before,
            snapshot_with_metadata(monthly_write.snapshot(row), proposal["tasks"]),
        )
    parent.revision += 1
    dao.save(parent)


@transaction.atomic
@aggregate_write
def submit(user, role_code, change_id):
    if legacy.candidate(change_id):
        return legacy.dispatch(user, role_code, change_id, "submit")
    change = dao.find_change(change_id, True)
    if not change:
        raise LookupError("变更申请不存在。")
    parent = read.accessible(user, role_code, change.submission_id, lock=True, editable=True)
    if change.status != "draft" or change.base_revision != parent.revision:
        raise ValueError("当前变更不支持提交。")
    validate_monthly_parts(json.loads(change.proposed_snapshot_json)["parts"])
    if content_key(json.loads(change.base_snapshot_json)["parts"]) == content_key(
        json.loads(change.proposed_snapshot_json)["parts"]
    ):
        raise ValueError("请修改内容后再提交变更。")
    baseline = json.loads(change.base_snapshot_json)
    if baseline.get("expand_legacy_positions"):
        source_rows(parent, baseline)
    approvers = approval_managers(user.id)
    start_approval(
        business_type="monthly_submission_change",
        business_id=change.id,
        applicant_id=user.id,
        revision=change.revision,
        snapshot=json.loads(change.proposed_snapshot_json),
        approvers=approvers,
    )
    change.status = "pending" if approvers else "approved"
    if not approvers:
        publish(parent, change, user)
    dao.save(change)
    return detail(user, role_code, change.id)


@transaction.atomic
@aggregate_write
def delete(user, role_code, change_id):
    if legacy.candidate(change_id):
        return legacy.dispatch(user, role_code, change_id, "delete")
    change = dao.find_change(change_id, True)
    if not change:
        raise LookupError("变更申请不存在。")
    read.accessible(user, role_code, change.submission_id, lock=True, editable=True)
    if change.status not in {"draft", "rejected"}:
        raise ValueError("当前变更不能删除。")
    change.status = "deleted"
    dao.save(change)
    return {"id": str(change.id), "deleted": True}
