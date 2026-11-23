"""主单配置、权限与详情序列化。"""

import json

from apps.accounts.public import (
    account_role_name,
    approval_managers,
    assigned_role_codes,
    report_owner,
    reporting_positions,
    shared_report_owner_ids,
    user_profiles,
    visible_user_ids,
)
from apps.approvals.public import approval_history, participated_business_ids

from .. import monthly_plan_change_dao as old_changes
from .. import submission_dao as dao
from . import reports
from . import weekly_submission_positions as weekly_positions
from .monthly_plans import read as monthly_read
from .monthly_plans.versions import change_row
from .submission_history import versions


def context(user, role_code, kind, month_key=None):
    positions = reporting_positions(user.id)
    if not positions:
        raise ValueError("模板未配置，不支持填写")
    for position in positions:
        position["template"] = reports.get_template_by_code(
            position["template_code"], role_code=position["role_code"]
        )
    if kind == "weekly" and month_key:
        for position in positions:
            gate = monthly_read.gate(user, position["role_code"], month_key)
            position.update(
                monthly_plan=gate,
                monthly_approved=gate["approved"],
                monthly_message=gate["message"],
            )
    return {"positions": positions, "managers": approval_managers(user.id), "kind": kind}


def accessible(user, role_code, submission_id, lock=False, editable=False):
    parent = dao.find(submission_id, lock)
    if not parent:
        legacy = dao.find_by_part(submission_id)
        parent = dao.find(legacy.id, lock) if legacy else None
    if not parent:
        raise LookupError("计划或周报不存在或已删除。")
    assigned = participated_business_ids(user.id, "monthly_submission", role_code=role_code)
    changes = participated_business_ids(user.id, "monthly_submission_change", role_code=role_code)
    legacy_ids = participated_business_ids(user.id, "monthly_plan", role_code=role_code)
    old_change_ids = participated_business_ids(user.id, "monthly_plan_change", role_code=role_code)
    old_plan_ids = [row.monthly_plan_id for row in old_changes.changes_by_ids(old_change_ids)]
    permitted = (
        int(parent.id) in dao.canonical_ids(assigned)
        or int(parent.id) in dao.canonical_ids(dao.change_parent_ids(changes))
        or int(parent.id) in dao.parent_ids_for_parts("monthly", legacy_ids + old_plan_ids)
    )
    if (
        parent.employee_id not in visible_user_ids(user, role_code)
        and parent.employee_id not in shared_report_owner_ids(user.id)
        and not permitted
    ):
        raise PermissionError("无权访问该计划或周报。")
    if editable and parent.employee_id != user.id:
        raise PermissionError("只能修改自己的计划或周报。")
    if editable and any(
        row.role_code not in assigned_role_codes(user.id) for row in dao.part_rows(parent)
    ):
        raise PermissionError("主单中包含未分配或已停用的职位，不能修改或提交。")
    if parent.legacy:
        rows = dao.part_rows(parent)
        if rows:
            parent.status = rows[0].status
            parent.revision = rows[0].revision if parent.kind == "monthly" else parent.revision
    if (
        parent.kind == "weekly"
        and parent.status == "not_started"
        and parent.period_start <= reports._current_period_start()
    ):
        parent.status = "in_progress"
    return parent


def parts(parent, user, role_code, rows=None):
    result = []
    owner = report_owner(parent.employee_id)
    configs = {row["role_code"]: row for row in reporting_positions(parent.employee_id)}
    for row in dao.part_rows(parent) if rows is None else rows:
        if parent.kind == "monthly":
            data = monthly_read.detail(owner, row.role_code, row.id)
            payload = {"summary": row.summary, "tasks": data["tasks"], "revision": row.revision}
        else:
            data = reports.get_report_detail(user=owner, role_code=row.role_code, report_id=row.id)
            payload = {
                **{key: data["report"].get(key) for key in (
                    "risk_level", "risk_blocked", "risk_reason", "next_action",
                    "support_needed", "expected_resolve_date", "as_of_date",
                )},
                "items": data["items"],
                "daily_tasks": data["daily_tasks"],
                "metrics": data["metrics"],
                "attachments": data["attachments"],
                "summary": row.summary,
            }
        result.append(
            {
                "id": str(row.id),
                "role_code": row.role_code,
                "role_name": account_role_name(row.role_code),
                "template_code": row.template_code,
                "customers": configs.get(row.role_code, {}).get("customers", []),
                "payload": payload,
                **(
                    {
                        "monthly_plan": {
                            "plan": data.get("monthly_plan"),
                            "tasks": data.get("monthly_plan_tasks", []),
                            "approved": True,
                            "message": "",
                        }
                    }
                    if parent.kind == "weekly"
                    else {}
                ),
                "template": reports.get_template_by_code(
                    row.template_code, role_code=row.role_code, allow_inactive=True
                ),
                "detail": data,
            }
        )
    return result


def snapshot(parent, user, role_code):
    return {
        "month_key": parent.month_key,
        "summary": " / ".join(row.summary for row in dao.part_rows(parent) if row.summary),
        "parts": [
            {key: value for key, value in part.items() if key != "detail"}
            for part in parts(parent, user, role_code)
        ],
    }


def serialize(parent, user, role_code, *, include_deleted=False):
    rows = dao.part_rows(parent, include_deleted=include_deleted)
    codes = [row.role_code for row in rows]
    children = change_rows(parent, rows)
    profile = user_profiles([parent.employee_id]).get(parent.employee_id, {})
    return {
        "id": str(parent.id),
        "submission_id": str(parent.id),
        "kind": parent.kind,
        "employee_id": str(parent.employee_id),
        "group_id": str(parent.group_id) if parent.group_id else None,
        "month_key": parent.month_key,
        "period_start": parent.period_start.isoformat() if parent.period_start else None,
        "period_end": parent.period_end.isoformat() if parent.period_end else None,
        "status": parent.status,
        "revision": parent.revision,
        "legacy": parent.legacy,
        "can_approve": False,
        "rejection_reason": "",
        "role_codes": codes,
        "role_code": codes[0] if codes else "",
        "role_name": " / ".join(account_role_name(code) for code in codes),
        "summary": "\n".join(row.summary for row in rows if row.summary),
        **(
            {
                "role_summaries": [
                    {
                        "role_code": row.role_code,
                        "role_name": account_role_name(row.role_code),
                        "summary": row.summary,
                    }
                    for row in rows
                ]
            }
            if parent.kind == "monthly"
            else {}
        ),
        "updated_at": parent.updated_at.isoformat(),
        "created_at": parent.created_at.isoformat(),
        "template_code": rows[0].template_code if rows else "",
        "can_create_change": parent.employee_id == user.id
        and parent.kind == "monthly"
        and parent.status == "approved"
        and not any(child["status"] in {"draft", "pending", "rejected"} for child in children),
        "children": children,
        **profile,
    }


def serialize_change(change):
    snapshot = json.loads(change.proposed_snapshot_json)
    return {
        "id": str(change.id),
        "plan_id": str(change.submission_id),
        "status": change.status,
        "revision": change.revision,
        "base_revision": change.base_revision,
        "summary": snapshot.get("summary", ""),
        "change_reason": snapshot.get("change_reason", ""),
        "role_summaries": [
            {
                "role_code": part["role_code"],
                "role_name": part.get("role_name") or account_role_name(part["role_code"]),
                "summary": part.get("payload", {}).get("summary", ""),
            }
            for part in snapshot.get("parts", [])
        ],
        "rejection_reason": change.rejection_reason,
        "updated_at": change.updated_at.isoformat(),
        "created_at": change.created_at.isoformat(),
    }


def detail(user, role_code, submission_id):
    parent = accessible(user, role_code, submission_id)
    records = approval_history("monthly_submission", parent.id, user.id, role_code)
    if parent.legacy and parent.kind == "monthly":
        rows = dao.part_rows(parent)
        records = approval_history("monthly_plan", rows[0].id, user.id, role_code) if rows else []
    detail_rows = detail_parts(parent, user, role_code)
    from .monthly_task_live_progress import progress_history

    task_ids = [
        int(task["id"])
        for part in detail_rows
        for task in (
            part.get("payload", {}).get("tasks", [])
            if parent.kind == "monthly"
            else (part.get("monthly_plan") or {}).get("tasks", [])
        )
        if str(task.get("id", "")).isdigit()
    ]
    return {
        "plan": serialize(parent, user, role_code),
        "parts": detail_rows,
        "progress_history": progress_history(task_ids),
        "approvals": records,
        "history": versions(parent, user.id, role_code),
        "managers": approval_managers(parent.employee_id)
        if parent.kind == "monthly" and parent.employee_id == user.id
        else [],
        "can_edit": parent.employee_id == user.id
        and parent.status in {"draft", "rejected", "in_progress", "not_started"},
    }


def matching_id(user, role_code, kind, submission_id):
    parent = accessible(user, role_code, submission_id)
    if parent.kind != kind:
        raise LookupError("计划或周报不存在。")
    return parent.id


def change_rows(parent, rows):
    children = [
        serialize_change(row)
        for source in [parent.id, *dao.merged_source_ids(parent.id)]
        for row in dao.changes(source)
    ]
    if parent.legacy and parent.kind == "monthly" and rows:
        parent.status, parent.revision = rows[0].status, rows[0].revision
    if parent.kind == "monthly":
        children += [
            {**change_row(change, include_snapshots=False), "plan_id": str(parent.id)}
            for change in old_changes.changes_for_plans([row.id for row in rows])
            if change.status != "deleted"
        ]
    if (
        parent.kind == "weekly"
        and parent.status == "not_started"
        and parent.period_start <= reports._current_period_start()
    ):
        parent.status = "in_progress"
    return children


def detail_parts(parent, user, role_code):
    if parent.kind != "weekly" or parent.status not in weekly_positions.EDITABLE:
        return parts(parent, user, role_code)
    configs = reporting_positions(parent.employee_id)
    rows = weekly_positions.sources(parent)
    result = {p["role_code"]: p for p in parts(parent, user, role_code, list(rows.values()))}
    # 已移除的历史职位仍保留，不能因展开而丢弃。
    for config in configs:
        code = config["role_code"]
        if code not in result:
            result[code] = {
                **config,
                "template": reports.get_template_by_code(config["template_code"], role_code=code),
                "payload": {"summary": "", "items": [], "daily_tasks": [],
                            "metrics": [], "attachments": []},
            }
    ordered = [p["role_code"] for p in configs]
    ordered += [code for code in result if code not in ordered]
    return [{**result[code], **weekly_positions.stamp(rows.get(code))} for code in ordered]
