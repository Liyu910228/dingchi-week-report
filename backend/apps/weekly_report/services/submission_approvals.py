"""主单审批与历史单职位审批的兼容入口。"""

import json

from django.db import transaction

from apps.accounts.public import account_role_name
from apps.approvals.public import approval_history, assigned_record, decide_approval

from .. import monthly_plan_change_dao as old_changes
from .. import monthly_plan_management_dao as old_plans
from .. import submission_dao as dao
from . import submission_changes as changes
from . import submission_read as read
from .monthly_plans import approval_read as old_read
from .monthly_plans import change_write as old_write_change
from .monthly_plans import write as old_write
from .submission_scope import aggregate_write


def parent_for(record, *, include_deleted=False):
    business_id = int(record["business_id"])
    if record["business_type"] == "monthly_submission":
        return dao.find(business_id, include_deleted=include_deleted), None
    if record["business_type"] == "monthly_submission_change":
        change = dao.find_change(business_id, include_deleted=include_deleted)
        return (
            (dao.find(change.submission_id, include_deleted=include_deleted), change)
            if change
            else (None, None)
        )
    if record["business_type"] == "monthly_plan_change":
        change = old_changes.find_change(business_id)
        part = old_plans.find_plan(change.monthly_plan_id) if change else None
    else:
        part = old_plans.find_plan(business_id)
    return (
        (dao.find(part.submission_id, include_deleted=include_deleted), None)
        if part and part.submission_id
        else (None, None)
    )


def detail(user, role_code, approval_id):
    record = assigned_record(user.id, approval_id, role_code)
    if record["business_type"] in {"monthly_plan", "monthly_plan_change"}:
        original = old_read.detail_assigned(user, role_code, approval_id)
        parent, _ = parent_for(record, include_deleted=True)
        return {
            **original,
            "plan_id": str(parent.id) if parent else original["plan_id"],
            "legacy_plan_id": original["plan_id"],
            "legacy_change_id": original.get("change_id"),
        }
    parent, change = parent_for(record, include_deleted=True)
    if not parent:
        raise LookupError("月度计划不存在。")
    row = read.serialize(parent, user, role_code, include_deleted=True)
    snapshot_parts = record.get("snapshot", {}).get("parts", [])
    codes = [part.get("role_code") for part in snapshot_parts if part.get("role_code")]
    names = [
        part.get("role_name") or account_role_name(part["role_code"])
        for part in snapshot_parts
        if part.get("role_code")
    ]
    return {
        **record,
        "plan_id": str(parent.id),
        "month_key": parent.month_key,
        "role_code": codes[0] if codes else row["role_code"],
        "role_name": " / ".join(names) if names else row["role_name"],
        "employee_name": row.get("employee_name", ""),
        "group_name": row.get("group_name", ""),
        "process_type": "change" if change else "initial",
        "change_id": str(change.id) if change else None,
        "base_snapshot": json.loads(change.base_snapshot_json) if change else None,
    }


@transaction.atomic
@aggregate_write
def decide(user, role_code, approval_id, payload):
    record = assigned_record(user.id, approval_id, role_code)
    parent, change = parent_for(record)
    if not parent:
        raise LookupError("月度计划不存在。")
    parent = dao.find(parent.id, True)
    if record["business_type"] == "monthly_plan":
        old_write.decide(user, role_code, int(record["business_id"]), payload)
        parent.status = dao.part_rows(parent)[0].status
    elif record["business_type"] == "monthly_plan_change":
        old_write_change.decide(user, role_code, int(record["business_id"]), payload)
    else:
        if payload.get("action") not in {"approve", "reject"}:
            raise ValueError("审批操作无效。")
        history = approval_history(
            record["business_type"], int(record["business_id"]), user.id, role_code
        )
        if not history or history[0]["id"] != str(approval_id):
            raise ValueError("审批版本已更新，请刷新。")
        status = decide_approval(
            request_id=approval_id,
            user_id=user.id,
            role_code=role_code,
            approve=payload["action"] == "approve",
            reason=payload.get("reason", ""),
        )
        if change:
            change.status = status
            change.rejection_reason = (
                str(payload.get("reason") or "") if status == "rejected" else ""
            )
            if status == "approved":
                changes.publish(parent, change, user)
            dao.save(change)
        else:
            parent.status = status
            dao.set_part_status(parent, status)
    dao.save(parent)
    return read.detail(user, role_code, parent.id)
