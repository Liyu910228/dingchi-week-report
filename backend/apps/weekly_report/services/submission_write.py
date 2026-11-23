"""主单保存与统一提交，整单事务保证各职位不会部分成功。"""

from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from apps.accounts.public import account_role_name, approval_managers, reporting_positions
from apps.approvals.public import approval_history, start_approval

from .. import submission_dao as dao
from . import reports
from . import submission_read as read
from . import weekly_submission_positions as weekly_positions
from .monthly_plan_tasks import validate_month_key
from .monthly_plans import write as monthly_write
from .monthly_submission_validation import validate_monthly_parts
from .monthly_task_metadata import task_content_key
from .submission_scope import aggregate_write


def validate_parts(user, incoming, existing=None):
    positions = {row["role_code"]: row for row in reporting_positions(user.id)}
    if not isinstance(incoming, list) or not incoming:
        raise ValueError("至少填写一个职位的内容。")
    codes = [part.get("role_code") for part in incoming if isinstance(part, dict)]
    if (
        len(codes) != len(incoming)
        or len(codes) != len(set(codes))
        or set(codes) - positions.keys()
    ):
        raise PermissionError("职位重复、未分配或不支持填写。")
    old_codes = {row.role_code for row in dao.part_rows(existing)} if existing else set()
    if existing and old_codes != set(codes):
        raise ValueError("已有主单的职位集合不能变更，请保留原职位内容。")
    if not existing and set(codes) != positions.keys():
        raise ValueError("请完整填写所有需要填报的职位。")


def period(kind, payload):
    if kind == "monthly":
        month = validate_month_key(str(payload.get("month_key") or ""))
        return month, None, None
    start = reports._parse_date(
        payload.get("period_start"), default=reports._current_period_start()
    )
    if start.weekday() != 0:
        raise ValueError("周报周期必须从周一开始。")
    return start.strftime("%Y-%m"), start, start + timedelta(days=6)


def save_parts(parent, user, incoming):
    old = {row.role_code: row for row in dao.part_rows(parent)}
    for part in incoming:
        code = part["role_code"]
        current = old.get(code)
        body = dict(part.get("payload") or {})
        if parent.kind == "monthly":
            body["month_key"] = parent.month_key
            if current:
                body["revision"] = current.revision
            try:
                data = monthly_write.save(
                    user, code, body, current.id if current else None, allow_incomplete=True
                )
            except (ValueError, PermissionError) as exc:
                raise type(exc)(f"{account_role_name(code)}：{exc}") from exc
            part_id = int(data["plan"]["id"])
        else:
            body.setdefault("attachments", [])
            body.update(
                period_start=parent.period_start.isoformat(),
                period_end=parent.period_end.isoformat(),
            )
            data = reports.create_or_update_report(
                user=user, role_code=code, payload=body, report_id=current.id if current else None,
            )
            part_id = int(data["report"]["id"])
        dao.attach(parent.kind, part_id, parent.id)


@transaction.atomic
@aggregate_write
def save(user, role_code, kind, payload, submission_id=None):
    parent = (
        read.accessible(user, role_code, submission_id, lock=True, editable=True)
        if submission_id
        else None
    )
    if parent and (
        parent.kind != kind
        or parent.status not in {"draft", "rejected", "in_progress", "not_started"}
    ):
        raise ValueError("当前主单不可编辑，已通过计划请申请变更。")
    if parent and int(payload.get("revision", -1)) != parent.revision:
        raise ValueError("数据已更新，请重新加载。")
    incoming = payload.get("parts")
    expand_weekly = bool(parent and kind == "weekly" and weekly_positions.needs_expansion(parent))
    validate_parts(user, incoming, None if expand_weekly else parent)
    month, start, end = period(kind, payload)
    if parent and parent.kind == "monthly" and parent.month_key != month:
        raise ValueError("已有月度计划不能修改所属月份。")
    if parent is None:
        parent = new_parent(user, kind, month, start, end)
    if parent.period_start != start and dao.active_exists(kind, user.id, month, start):
        raise ValueError("该周期已有计划或周报，请编辑已有记录。")
    if expand_weekly:
        weekly_positions.prepare_save(parent, incoming)
    parent.month_key, parent.period_start, parent.period_end = month, start, end
    if not parent.legacy:
        parent.active_key = f"{kind}:{user.id}:{start or month}"
    save_parts(parent, user, incoming)
    if kind == "monthly":
        parent.status = "draft"
    else:
        parent.status = "not_started" if start > reports._current_period_start() else "in_progress"
    parent.revision += 1
    dao.save(parent)
    return read.detail(user, role_code, parent.id)


@transaction.atomic
@aggregate_write
def submit(user, role_code, submission_id):
    parent = read.accessible(user, role_code, submission_id, lock=True, editable=True)
    rows = dao.part_rows(parent)
    if not rows:
        raise ValueError("没有可提交的职位内容。")
    if parent.kind == "monthly":
        submit_monthly(parent, user, role_code, rows)
    else:
        if parent.status != "in_progress":
            raise ValueError("仅进行中的周报可以提交。")
        if {p["role_code"] for p in reporting_positions(user.id)} - {r.role_code for r in rows}:
            raise ValueError("请先编辑并保存全部职位的周报，再提交。")
        for row in rows:
            reports.submit_report(user=user, role_code=row.role_code, report_id=row.id)
        parent.status = "completed"
    parent.submitted_at = timezone.now()
    dao.save(parent)
    return read.detail(user, role_code, parent.id)


@transaction.atomic
@aggregate_write
def delete(user, role_code, submission_id):
    parent = read.accessible(user, role_code, submission_id, lock=True, editable=True)
    if (
        parent.status not in (
            {"draft"} if parent.kind == "monthly" else {"draft", "not_started", "in_progress"}
        )
        or dao.pending_changes(parent.id).exists()
    ):
        raise ValueError("当前状态不允许删除。")
    for row in dao.part_rows(parent):
        if parent.kind == "monthly":
            monthly_write.delete(user, row.role_code, row.id)
        else:
            reports.delete_report(user=user, role_code=row.role_code, report_id=row.id)
    if parent.kind == "monthly":
        parent.status, parent.active_key = "deleted", None
        dao.save(parent)
        return {"id": str(parent.id), "deleted": True}
    parent_id = str(parent.id)
    from ..submission_models import ReportSubmissionChange

    ReportSubmissionChange.objects.filter(submission_id=parent.id).delete()
    parent.delete()
    return {"id": parent_id, "deleted": True}


def new_parent(user, kind, month, start, end):
    if dao.active_exists(kind, user.id, month, start):
        raise ValueError("该周期已有计划或周报，请编辑已有记录。")
    status = (
        "draft"
        if kind == "monthly"
        else ("not_started" if start > reports._current_period_start() else "in_progress")
    )
    return dao.create(
        kind=kind,
        employee_id=user.id,
        group_id=user.group_id,
        month_key=month,
        period_start=start,
        period_end=end,
        status=status,
        active_key=f"{kind}:{user.id}:{start or month}",
    )


def submit_monthly(parent, user, role_code, rows):
    if parent.status not in {"draft", "rejected"}:
        raise ValueError("当前计划不支持提交。")
    validate_monthly_parts(
        [
            {
                "role_code": row.role_code,
                "template_code": row.template_code,
                "payload": monthly_write.snapshot(row),
            }
            for row in rows
        ]
    )
    if parent.legacy:
        result = monthly_write.submit(user, rows[0].role_code, rows[0].id)
        parent.status = result["plan"]["status"]
    else:
        history = approval_history("monthly_submission", parent.id, user.id, role_code)
        if (
            history
            and history[0]["status"] == "rejected"
            and history[0]["revision"] == parent.revision
        ):
            raise ValueError("请先修改驳回的内容，再重新提交。")
        approvers = approval_managers(user.id)
        start_approval(
            business_type="monthly_submission",
            business_id=parent.id,
            applicant_id=user.id,
            revision=parent.revision,
            snapshot=read.snapshot(parent, user, role_code),
            approvers=approvers,
        )
        parent.status = "pending" if approvers else "approved"
        dao.set_part_status(parent, parent.status)


def content_key(parts):
    return sorted(
        (
            part["role_code"],
            str(part["payload"].get("summary") or "").strip(),
            tuple(task_content_key(task) for task in part["payload"].get("tasks", [])),
        )
        for part in parts
    )
