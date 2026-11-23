"""Weekly report workflow, visibility and aggregation services."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any
from uuid import uuid4

from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.uploadedfile import UploadedFile
from django.db import IntegrityError, transaction
from django.db.utils import OperationalError, ProgrammingError
from django.utils import timezone
from django.utils.text import get_valid_filename

from apps.accounts.models import Role, UserAccount
from apps.accounts.public import shared_report_owner_ids, visible_user_ids
from apps.core.models import Attachment
from apps.dictionary.public import list_active_dictionary_items
from apps.todos.public import complete as complete_todo
from apps.weekly_report.services.submission_validation import submission_errors
from apps.weekly_report.services.task_texts import remove_unused_texts, save_task_texts

from .. import dao
from ..models import (
    MonthlyPlan,
    ReportTemplate,
    ReportTemplateItem,
    WeeklyReport,
    WeeklyReportDailyTask,
    WeeklyReportItem,
    WeeklyReportItemProgressHistory,
    WeeklyReportMetric,
)
from ..templates import ROLE_TEMPLATES, get_default_task_fields, get_default_template
from .dashboard_submissions import member_report_summaries
from .dashboard_tasks import group_work_tasks, output_distribution, task_trend
from .monthly_attachment_access import authorize_monthly_file
from .monthly_plan_tasks import (
    list_monthly_plan_tasks,
)
from .monthly_plans.policy import ensure_approved
from .submission_scope import check_part, sync_legacy


class ReportError(ValueError):
    """A safe report validation or workflow error."""

    code = "REPORT_INVALID"


class ReportNotFoundError(ReportError):
    """The requested report does not exist."""

    code = "REPORT_NOT_FOUND"


class ReportConflictError(ReportError):
    """The requested report operation conflicts with an existing period."""

    code = "REPORT_CONFLICT"


class ReportPermissionError(ReportError):
    """The current role cannot access or mutate the report."""

    code = "FORBIDDEN"


REPORT_STATUS_NOT_STARTED = "not_started"
REPORT_STATUS_IN_PROGRESS = "in_progress"
REPORT_STATUS_COMPLETED = "completed"


def get_template_by_code(
    template_code: str,
    *,
    role_code: str | None = None,
    allow_inactive: bool = False,
) -> dict[str, Any]:
    """Return one exact versioned template.

    A template code is globally unique and already contains its version.  The
    optional role code only supplies display context when a custom role reuses
    an existing template; it is never used to select the template.
    """
    normalized_code = str(template_code or "").strip()
    if not normalized_code:
        raise ReportError("模板未配置，不支持填写")
    template = ReportTemplate.objects.filter(template_code=normalized_code).first()
    if template is None:
        try:
            fallback = get_default_template(normalized_code, role_code=role_code)
            # A custom role may reuse a built-in template.  Keep the template
            # structure from the built-in code, but expose the active role's
            # display name when it is available.
            if role_code:
                bound_role = Role.objects.filter(role_code=role_code).first()
                if bound_role is not None:
                    fallback["role_name"] = bound_role.role_name
            return fallback
        except ValueError as exc:
            raise ReportNotFoundError("模板未配置，不支持填写") from exc
    if template.status != "active" and not allow_inactive:
        raise ReportError("模板未配置，不支持填写")
    rows = list(
        ReportTemplateItem.objects.filter(template_id=template.id).order_by("sort_order", "id")
    )
    template_role_code = role_code or next(
        (
            candidate_role
            for candidate_role, source in ROLE_TEMPLATES.items()
            if source["template_code"] == template.template_code
        ),
        "",
    )
    tasks = [_serialize_template_item(row) for row in rows if row.item_type == "task"]
    metrics = [_serialize_template_item(row) for row in rows if row.item_type == "metric"]
    section_map: dict[str, dict[str, Any]] = {}
    for row in rows:
        section_map.setdefault(
            row.section_code,
            {"section_code": row.section_code, "section_name": row.section_name, "tasks": []},
        )
        if row.item_type == "task":
            section_map[row.section_code]["tasks"].append(_serialize_template_item(row))
    return {
        "role_code": template_role_code,
        "role_name": (
            _role_name(template_role_code) if template_role_code else template.template_name
        ),
        "template_code": template.template_code,
        "template_name": template.template_name,
        "description": template.description,
        "sections": list(section_map.values()),
        "tasks": tasks,
        "metrics": metrics,
        "fields": _get_template_fields(template.template_code),
    }


def resolve_role_template(role_code: str) -> dict[str, Any]:
    """Resolve the active role's explicitly bound versioned template code."""
    role = Role.objects.filter(role_code=role_code, status="active").first()
    if role is None:
        raise ReportPermissionError("当前角色不存在或已停用。")
    template_code = str(role.report_template_code or "").strip()
    if not template_code:
        raise ReportError("模板未配置，不支持填写")
    return get_template_by_code(template_code, role_code=role_code)


def visible_employee_ids(user: UserAccount, role_code: str) -> list[int]:
    """Apply the same ordered-manager team visibility as monthly plans."""
    return visible_user_ids(user, role_code)


def list_visible_reports(
    *,
    user: UserAccount,
    role_code: str,
    page: int = 1,
    page_size: int = 10,
    period_start: Any = None,
    period_end: Any = None,
    month_key: Any = None,
    group_id: Any = None,
    employee_id: Any = None,
    employee_scope: str | None = None,
    filter_role_code: str | None = None,
) -> dict[str, Any]:
    """按当前角色作用域分页查询周报。

    self 角色只能查询本人；team 角色可切换本人或下属团队；all 角色查询
    全部人员。周期和分组筛选由接口统一转成逻辑 ID/日期后交给 DAO。
    """
    scope = _role_scope(role_code)
    employee_ids = visible_employee_ids(user, role_code)
    if employee_scope:
        if scope not in {"team", "all"} or employee_scope not in {"self", "team"}:
            raise ReportError("当前角色不支持该人员范围筛选。")
        if employee_scope == "self":
            employee_ids = [int(user.id)]
        else:
            employee_ids = [item for item in employee_ids if item != int(user.id)]
    if scope == "self" and group_id not in (None, ""):
        raise ReportError("个人周报不支持按分组筛选。")
    parsed_group_id = _optional_int(group_id)
    parsed_employee_id = _optional_int(employee_id)
    if parsed_employee_id is not None:
        employee_ids = [parsed_employee_id] if parsed_employee_id in employee_ids else []
    parsed_period_start = _parse_optional_date(period_start)
    parsed_period_end = _parse_optional_date(period_end)
    parsed_month_key = _parse_month_key(month_key)
    role_filter = str(filter_role_code or "").strip() or None
    if role_filter and len(role_filter) > 64:
        raise ReportError("职位筛选编码不能超过64字符。")
    if page < 1:
        raise ReportError("页码必须是大于 0 的整数。")
    if page_size < 1 or page_size > 100:
        raise ReportError("每页条数必须在 1—100 范围内。")
    result = dao.list_reports_page(
        employee_ids=employee_ids,
        role_code=role_filter,
        period_start=parsed_period_start,
        period_end=parsed_period_end,
        month_key=parsed_month_key,
        group_id=parsed_group_id,
        page=page,
        page_size=page_size,
    )
    result["items"] = [_serialize_report_row(row) for row in result["items"]]
    return result


def create_or_update_report(
    *, user: UserAccount, role_code: str, payload: Mapping[str, Any], report_id: int | None = None,
) -> dict[str, Any]:
    if _role_scope(role_code) == "all":
        raise ReportPermissionError("全员数据角色仅支持查看周报。")
    current_start = _current_period_start()
    period_start = _parse_date(payload.get("period_start"), default=current_start)
    period_end = _parse_date(payload.get("period_end"), default=period_start + timedelta(days=6))
    as_of_date = _parse_date(payload.get("as_of_date"), default=timezone.localdate())
    if period_end < period_start:
        raise ReportError("周报结束日期不能早于开始日期。")
    if period_start.weekday() != 0:
        raise ReportError("周报周期必须从周一开始。")
    if period_end != period_start + timedelta(days=6):
        raise ReportError("周报周期结束日期必须是开始日期后的周日。")
    report = _load_editable_report(
        user=user,
        role_code=role_code,
        report_id=report_id,
        period_start=period_start,
    )
    # New reports use the active role binding.  Editing always uses the
    # report's stored template snapshot so changing a role's binding does not
    # rewrite historical/current report data to another template version.
    template = (
        get_template_by_code(report.template_code, role_code=role_code, allow_inactive=True)
        if report is not None
        else resolve_role_template(role_code)
    )
    # 新建周报只根据是否为未来周期确定初始状态。周报不会因为周期结束
    # 自动提交，周期结束后的成果补录仍需要保持可编辑，直到用户手动提交。
    period_status = _initial_report_status(period_start)
    with transaction.atomic():
        existing_attachments: list[Attachment] = []
        if report is not None:
            existing_attachments = list(
                Attachment.objects.filter(
                    attachment_type="weekly_report", relation_id=report.id
                ).order_by("created_at", "id")
            )
        if report is None:
            try:
                report = WeeklyReport.objects.create(
                    role_code=role_code,
                    template_code=template["template_code"],
                    employee_id=user.id,
                    group_id=user.group_id,
                    period_type="week",
                    month_key=period_start.strftime("%Y-%m"),
                    period_start=period_start,
                    period_end=period_end,
                    as_of_date=as_of_date,
                    status=period_status,
                )
            except IntegrityError as exc:
                raise ReportConflictError(
                    "该角色在此周报周期已有记录，请直接查看或编辑已有周报。"
                ) from exc
        else:
            if report.period_start != period_start:
                if dao.report_period_exists(user.id, role_code, period_start, report.id):
                    raise ReportConflictError("该职位在此周报周期已有记录，请选择其他周期。")
                dao.move_daily_task_dates(report.id, period_start - report.period_start)
                report.period_start = period_start
                report.month_key = period_start.strftime("%Y-%m")
                report.status = period_status
            report.period_end = period_end
            report.as_of_date = as_of_date
            # 周期未改变时保留原月度归属；调整周期时按新周期开始月校验审批。
            report.group_id = user.group_id
            # 保留已经持久化的状态。未来周报进入当前周期时只允许从
            # 未来周报进入当前周期时由展示层计算为进行中，不再根据周期结束日期自动变更状态。
        report.summary = str(payload.get("summary") or "").strip()
        report.risk_level = str(payload.get("risk_level") or "none").strip()
        report.risk_blocked = bool(payload.get("risk_blocked", False))
        report.risk_reason = str(payload.get("risk_reason") or "").strip()
        report.next_action = str(payload.get("next_action") or "").strip()
        report.support_needed = str(payload.get("support_needed") or "").strip()
        report.expected_resolve_date = _parse_optional_date(payload.get("expected_resolve_date"))
        try:
            report.save()
        except IntegrityError as exc:
            raise ReportConflictError("该职位在此周报周期已有记录，请选择其他周期。") from exc
        ensure_approved(user, role_code, report.month_key)
        if "monthly_plan" in payload or "monthly_plan_tasks" in payload:
            raise ReportError("月度目标和计划只能在月度计划管理中维护，周报中仅展示。")
        previous_item_progress = _get_item_progress_state(int(report.id))
        WeeklyReportItem.objects.filter(report_id=report.id).delete()
        WeeklyReportMetric.objects.filter(report_id=report.id).delete()
        item_id_map = _save_items(report, payload.get("items"), template["tasks"], user.id)
        remove_unused_texts(report.id)
        _record_item_progress_history(
            report=report,
            previous_state=previous_item_progress,
            recorded_by=int(user.id),
        )
        _save_metrics(report, payload.get("metrics"), template["metrics"], item_id_map)
        _sync_attachments(
            value=payload.get("attachments"),
            item_id_map=item_id_map,
            existing=existing_attachments,
            report=report,
            user=user,
        )
        _save_daily_tasks(report, payload.get("daily_tasks"))
        complete_todo(
            recipient_id=user.id,
            role_code=role_code,
            dedupe_key=f"weekly:{role_code}:{report.period_start}",
        )
    sync_legacy(report, "weekly")
    return get_report_detail(user=user, role_code=role_code, report_id=int(report.id))


def delete_report(*, user: UserAccount, role_code: str, report_id: int) -> dict[str, Any]:
    """删除本人尚未提交的周报及其逻辑关联明细。"""
    report = WeeklyReport.objects.filter(id=report_id).first()
    if _role_scope(role_code) == "all":
        raise ReportPermissionError("全员数据角色仅支持查看周报。")
    if report is None:
        raise ReportNotFoundError("周报不存在。")
    if int(report.employee_id) != int(user.id) or report.role_code != role_code:
        raise ReportPermissionError("只能删除当前角色下自己的周报。")
    if _effective_report_status(report.status, report.period_start) == REPORT_STATUS_COMPLETED:
        raise ReportError("已完成的周报不支持删除。")
    with transaction.atomic():
        WeeklyReportDailyTask.objects.filter(report_id=report.id).delete()
        WeeklyReportItemProgressHistory.objects.filter(report_id=report.id).delete()
        WeeklyReportItem.objects.filter(report_id=report.id).delete()
        remove_unused_texts(report.id)
        WeeklyReportMetric.objects.filter(report_id=report.id).delete()
        for attachment in Attachment.objects.filter(
            attachment_type="weekly_report", relation_id=report.id
        ):
            _delete_attachment_record(attachment)
        report_id_text = str(report.id)
        check_part(report)
        report.status = "deleted"
        sync_legacy(report, "weekly")
        from .physical_delete import delete_legacy_parent

        delete_legacy_parent(report.submission_id)
        report.delete()
    return {"id": report_id_text, "deleted": True}


def get_report_detail(*, user: UserAccount, role_code: str, report_id: int) -> dict[str, Any]:
    from .daily_tasks import list_daily_tasks_for_report

    header = _get_accessible_report(user=user, role_code=role_code, report_id=report_id)
    template = get_template_by_code(
        str(header.get("template_code") or ""),
        role_code=str(header.get("role_code") or ""),
        allow_inactive=True,
    )
    return {
        "report": _serialize_report_row(header),
        "template": template,
        "monthly_plan": get_monthly_plan(
            user=user,
            access_role_code=role_code,
            plan_role_code=str(header["role_code"]),
            month_key=str(header["month_key"]),
            employee_id=int(header["employee_id"]),
        ),
        "items": [_serialize_row(row) for row in dao.get_report_items(report_id)],
        "metrics": [_serialize_row(row) for row in dao.get_report_metrics(report_id)],
        "attachments": [_serialize_row(row) for row in dao.get_report_attachments(report_id)],
        "daily_tasks": list_daily_tasks_for_report(report_id),
        "monthly_plan_tasks": list_monthly_plan_tasks(
            employee_id=int(header["employee_id"]),
            role_code=str(header["role_code"]),
            month_key=str(header["month_key"]),
        ),
    }


def submit_report(*, user: UserAccount, role_code: str, report_id: int) -> dict[str, Any]:
    """提交本人当前角色的周报，提交后周报及其明细只读。"""
    if _role_scope(role_code) == "all":
        raise ReportPermissionError("全员数据角色仅支持查看周报。")
    with transaction.atomic():
        report = WeeklyReport.objects.select_for_update().filter(id=report_id).first()
        if report is None:
            raise ReportNotFoundError("周报不存在。")
        check_part(report)
        if int(report.employee_id) != int(user.id) or report.role_code != role_code:
            raise ReportPermissionError("只能提交当前角色下自己的周报。")
        check_part(report)
        effective_status = _effective_report_status(report.status, report.period_start)
        if effective_status != REPORT_STATUS_IN_PROGRESS:
            raise ReportError("仅进行中的周报可以提交。")
        errors = submission_errors(
            report,
            dao.get_report_items(report.id),
            _get_template_fields(report.template_code),
            get_template_by_code(report.template_code, role_code=role_code, allow_inactive=True),
        )
        if errors:
            raise ReportError("提交失败：\n" + "\n".join(errors))
        report.status = REPORT_STATUS_COMPLETED
        report.save(update_fields=["status", "updated_at"])
        sync_legacy(report, "weekly")
    return {"id": str(report.id), "status": REPORT_STATUS_COMPLETED, "submitted": True}


def upload_pending_report_attachment(
    *,
    user: UserAccount,
    uploaded_file: UploadedFile | None,
    description: Any = "",
) -> dict[str, Any]:
    """上传尚未绑定周报任务的附件，并返回可在保存任务时使用的附件 ID。"""
    if uploaded_file is None:
        raise ReportError("请选择附件。")

    max_size = int(settings.ATTACHMENT_MAX_SIZE_BYTES)
    if uploaded_file.size is not None and uploaded_file.size > max_size:
        raise ReportError(f"附件大小不能超过 {max_size // (1024 * 1024)} MB。")
    original_name = Path(uploaded_file.name or "附件").name
    safe_name = get_valid_filename(original_name) or "attachment"
    extension = Path(safe_name).suffix.lower()
    allowed = {
        str(item).strip().lower()
        for item in settings.ATTACHMENT_ALLOWED_EXTENSIONS
        if str(item).strip()
    }
    if allowed and extension not in allowed:
        raise ReportError("附件类型不在允许范围内。")

    upload_dir = f"{str(settings.ATTACHMENT_UPLOAD_DIR).strip('/')}/pending/{user.id}"
    storage_name = default_storage.save(
        f"{upload_dir}/{uuid4().hex}_{safe_name}",
        uploaded_file,
    )
    file_url = f"{str(settings.MEDIA_URL).rstrip('/')}/{storage_name}"
    try:
        attachment = Attachment.objects.create(
            attachment_type="weekly_report_pending",
            relation_id=user.id,
            relation_sub_id=None,
            storage_key=storage_name,
            file_url=file_url,
            file_name=original_name,
            mime_type=str(uploaded_file.content_type or "application/octet-stream")[:128],
            file_size=int(uploaded_file.size or 0),
            description=str(description or "").strip()[:500],
        )
    except Exception:
        default_storage.delete(storage_name)
        raise
    return _serialize_row(
        {
            "id": attachment.id,
            "attachment_type": attachment.attachment_type,
            "relation_id": attachment.relation_id,
            "relation_sub_id": attachment.relation_sub_id,
            "storage_key": attachment.storage_key,
            "file_url": attachment.file_url,
            "file_name": attachment.file_name,
            "mime_type": attachment.mime_type,
            "file_size": attachment.file_size,
            "description": attachment.description,
            "created_at": attachment.created_at,
            "updated_at": attachment.updated_at,
        }
    )


def get_report_attachment_for_download(
    *,
    user: UserAccount,
    role_code: str,
    attachment_id: int,
) -> Attachment:
    """校验附件及所属周报的可见权限，并返回可下载的附件记录。"""
    attachment = Attachment.objects.filter(id=attachment_id).first()
    if attachment is None or attachment.attachment_type not in {
        "weekly_report",
        "weekly_report_pending",
        "monthly_plan",
    }:
        raise ReportNotFoundError("附件不存在。")

    if attachment.attachment_type == "weekly_report_pending":
        if int(attachment.relation_id) != int(user.id):
            raise ReportPermissionError("无权下载该附件。")
        storage_key = str(attachment.storage_key or "").strip()
        if not storage_key or not default_storage.exists(storage_key):
            raise ReportNotFoundError("附件文件不存在。")
        return attachment

    if attachment.attachment_type == "monthly_plan":
        authorize_monthly_file(user, role_code, attachment.relation_id)
    else:
        _get_accessible_report(
            user=user, role_code=role_code, report_id=int(attachment.relation_id)
        )
    storage_key = str(attachment.storage_key or "").strip()
    if not storage_key or not default_storage.exists(storage_key):
        raise ReportNotFoundError("附件文件不存在。")
    return attachment


def delete_report_attachment(
    *,
    user: UserAccount,
    role_code: str,
    attachment_id: int,
) -> dict[str, Any]:
    """物理删除本人未提交周报的附件记录和存储文件。"""
    with transaction.atomic():
        attachment = Attachment.objects.select_for_update().filter(id=attachment_id).first()
        if attachment is None or attachment.attachment_type not in {
            "weekly_report",
            "weekly_report_pending",
        }:
            raise ReportNotFoundError("附件不存在。")
        if attachment.attachment_type == "weekly_report_pending":
            if int(attachment.relation_id) != int(user.id):
                raise ReportPermissionError("只能删除自己上传的附件。")
            _delete_attachment_record(attachment)
            return {"id": str(attachment_id), "deleted": True}
        report = WeeklyReport.objects.filter(id=attachment.relation_id).first()
        if report is None:
            raise ReportNotFoundError("附件所属周报不存在。")
        if int(report.employee_id) != int(user.id) or report.role_code != role_code:
            raise ReportPermissionError("只能删除当前角色下自己的周报附件。")
        if _effective_report_status(report.status, report.period_start) == REPORT_STATUS_COMPLETED:
            raise ReportPermissionError("已提交的周报不支持删除附件。")
        _delete_attachment_record(attachment)
    return {"id": str(attachment_id), "deleted": True}


def get_monthly_plan(
    *,
    user: UserAccount,
    access_role_code: str,
    month_key: Any,
    employee_id: int | None = None,
    plan_role_code: str | None = None,
) -> dict[str, Any] | None:
    """返回指定月份计划；本人可读写，管理角色可随周报详情只读查看。"""
    parsed_month_key = _parse_month_key(month_key, required=True)
    target_employee_id = employee_id or int(user.id)
    if target_employee_id not in visible_employee_ids(user, access_role_code):
        raise ReportPermissionError("无权查看该员工的月度计划。")
    role_code = plan_role_code or access_role_code
    plan = dao.get_monthly_plan(target_employee_id, role_code, parsed_month_key)
    if plan is None:
        return None
    result = _serialize_row(plan)
    record = MonthlyPlan.objects.filter(id=plan["id"]).first()
    result["status"] = record.status if record else "draft"
    return result


def save_monthly_plan(
    *, user: UserAccount, role_code: str, month_key: Any, summary: Any
) -> dict[str, Any]:
    """旧写入接口停用；编辑和审批统一迁移到月度计划管理。"""
    raise ReportPermissionError("请在月度计划管理页面填写、修改和提交审批。")


def dashboard_summary(
    *,
    user: UserAccount,
    role_code: str,
    period_start: Any = None,
) -> dict[str, Any]:
    selected_start = _parse_optional_date(period_start)
    if selected_start is not None and selected_start.weekday() != 0:
        raise ReportError("周报周期只能选择周一。")

    employee_ids = visible_employee_ids(user, role_code)
    current_start = selected_start or _current_period_start()
    current_end = current_start + timedelta(days=6)
    rows = dao.list_reports(
        employee_ids=employee_ids,
        period_start=current_start,
        period_end=current_end,
    )
    current_rows = [
        _with_report_status(row)
        for row in rows
        if (_as_date(row.get("period_start")) or current_start) == current_start
    ]
    team_items: list[dict[str, Any]] = []
    for row in current_rows:
        report_id = int(row["id"])
        report_items = dao.get_report_items(report_id)
        for item in report_items:
            team_items.append(
                {
                    **item,
                    "employee_id": row.get("employee_id"),
                    "employee_name": row.get("employee_name") or "",
                    "role_code": row.get("role_code") or "",
                    "role_name": row.get("role_name") or row.get("role_code") or "",
                    "group_id": row.get("group_id"),
                    "group_name": row.get("group_name") or "",
                    "report_status": row.get("status") or "",
                    "report_period_start": row.get("period_start"),
                    "report_period_end": row.get("period_end"),
                }
            )
    week_rows = [
        row
        for row in current_rows
        if (_as_date(row.get("period_start")) or current_start) == current_start
    ]
    week_items = [
        item
        for item in team_items
        if (_as_date(item.get("report_period_start")) or current_start) == current_start
    ]
    visible_members = dao.list_dashboard_members(employee_ids)
    reporting_ids = {str(member["employee_id"]) for member in visible_members}
    week_rows = [row for row in week_rows if str(row["employee_id"]) in reporting_ids]
    week_items = [item for item in week_items if str(item["employee_id"]) in reporting_ids]
    member_stats, group_stats = _build_dashboard_task_stats(
        week_rows,
        week_items,
        visible_members,
    )
    work_tasks = group_work_tasks(week_items)
    progress_values = [
        Decimal(str(item["completion_rate"]))
        for item in work_tasks
        if item["completion_rate"] is not None
    ]
    completion = (
        round(sum(progress_values) / len(progress_values), 1) if progress_values else Decimal("0")
    )
    status_counts = {"in_progress": 0, "overdue": 0, "on_time": 0, "late": 0, "completed": 0}
    for item in work_tasks:
        status_key = str(item.get("on_time_status") or "in_progress")
        # 仅读取唯一状态字段；待完成任务在首页状态分布中归入进行中。
        if status_key == "pending":
            status_key = "in_progress"
        status_counts[status_key] = status_counts.get(status_key, 0) + 1
    risk_count = sum(1 for item in work_tasks if item.get("on_time_status") in {"overdue", "late"})
    own_rows = [row for row in current_rows if int(row["employee_id"]) == int(user.id)]
    own_week_items = []
    for row in own_rows:
        row_items = dao.get_report_items(int(row["id"]))
        own_week_items.extend(row_items)
    progress_history = dao.get_report_item_progress_history([int(row["id"]) for row in week_rows])
    trend = _build_trend(week_items, progress_history, current_start)
    return {
        "scope": _role_scope(role_code),
        "period": {
            "start": current_start.isoformat(),
            "end": (current_start + timedelta(days=6)).isoformat(),
        },
        "kpis": {
            "planned_tasks": len(work_tasks),
            "completion_rate": float(completion),
            "completed_tasks": sum(
                1
                for item in work_tasks
                if item.get("on_time_status") in {"completed", "on_time"}
                or Decimal(str(item.get("progress_percent") or 0)) >= 100
            ),
            "risk_items": risk_count,
        },
        "trend": trend,
        "status_distribution": [
            {"name": "进行中", "value": status_counts.get("in_progress", 0), "color": "#2f80ed"},
            {
                "name": "已完成",
                "value": status_counts.get("on_time", 0) + status_counts.get("completed", 0),
                "color": "#12b886",
            },
            {
                "name": "延期/风险",
                "value": status_counts.get("overdue", 0) + status_counts.get("late", 0),
                "color": "#f05d5e",
            },
        ],
        "my_tasks": [_serialize_row(item) for item in own_week_items[:8]],
        "my_work_tasks": [_serialize_row(item) for item in group_work_tasks(own_week_items)],
        "team_work_tasks": [_serialize_row(item) for item in work_tasks],
        "team_output_items": [
            _serialize_row(item)
            for item in week_items
            if str(item.get("output_description") or "").strip()
        ][:200],
        "output_distribution": output_distribution(week_items),
        "output_count": sum(
            bool(str(item.get("output_description") or "").strip()) for item in week_items
        ),
        # 下周计划由独立接口返回，避免当前周期查询越过空周读取更远周期。
        "my_plans": [],
        "reports": [_serialize_row(row) for row in current_rows[:12]],
        "member_reports": [
            _serialize_row(row)
            for row in member_report_summaries(
                week_rows, {str(member["employee_id"]) for member in member_stats}
            )
        ],
        # 领导首页需要按部门和责任人展示当前可见任务；任务仍来自周报明细，避免前端生成演示数据。
        "team_tasks": [_serialize_row(item) for item in team_items[:200]],
        # 管理视角使用后端真实聚合结果，避免前端只根据截断后的任务明细计算出错误的总数。
        "member_stats": member_stats,
        "group_stats": group_stats,
    }


def dashboard_next_week(
    *,
    user: UserAccount,
    role_code: str,
    period_start: Any = None,
) -> dict[str, Any]:
    """返回所选周期紧邻的下一周数据，不向后跳过没有数据的周期。"""
    selected_start = _parse_optional_date(period_start)
    if selected_start is not None and selected_start.weekday() != 0:
        raise ReportError("周报周期只能选择周一。")

    current_start = selected_start or _current_period_start()
    next_start = current_start + timedelta(days=7)
    next_end = next_start + timedelta(days=6)
    employee_ids = visible_employee_ids(user, role_code)
    rows = [
        _with_report_status(row)
        for row in dao.list_reports(
            employee_ids=employee_ids,
            period_start=next_start,
            period_end=next_end,
        )
        if (_as_date(row.get("period_start")) or next_start) == next_start
    ]
    team_items: list[dict[str, Any]] = []
    own_items: list[dict[str, Any]] = []
    for row in rows:
        for item in dao.get_report_items(int(row["id"])):
            enriched = {
                **item,
                "employee_id": row.get("employee_id"),
                "employee_name": row.get("employee_name") or "",
                "role_code": row.get("role_code") or "",
                "role_name": row.get("role_name") or row.get("role_code") or "",
                "group_id": row.get("group_id"),
                "group_name": row.get("group_name") or "",
                "report_status": row.get("status") or "",
                "report_period_start": row.get("period_start"),
                "report_period_end": row.get("period_end"),
            }
            team_items.append(enriched)
            if int(row["employee_id"]) == int(user.id):
                own_items.append(item)

    return {
        "period": {"start": next_start.isoformat(), "end": next_end.isoformat()},
        "my_plans": [_serialize_row(item) for item in own_items[:8]],
        "my_work_plans": [_serialize_row(item) for item in group_work_tasks(own_items)],
        "team_work_tasks": [_serialize_row(item) for item in group_work_tasks(team_items)],
        "team_tasks": [_serialize_row(item) for item in team_items[:200]],
    }


def _build_dashboard_task_stats(
    report_rows: Sequence[Mapping[str, Any]],
    task_rows: Sequence[Mapping[str, Any]],
    visible_members: Sequence[Mapping[str, Any]] = (),
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Build current-week member and group task statistics for dashboards.

    Counts use logical work-task groups; output counts still use every detail row.  The
    ``tasks`` list on each member is only a readable preview for the homepage;
    the count/rate fields never depend on that preview limit.
    """

    members: dict[str, dict[str, Any]] = {}
    groups: dict[str, dict[str, Any]] = {}

    def ensure_member(row: Mapping[str, Any]) -> dict[str, Any]:
        employee_id = str(row.get("employee_id") or "")
        key = employee_id or f"name:{row.get('employee_name') or 'unknown'}"
        member = members.get(key)
        if member is None:
            member = {
                "employee_id": employee_id,
                "employee_name": str(row.get("employee_name") or "未命名成员"),
                "role_code": str(row.get("role_code") or ""),
                "role_name": str(row.get("role_name") or row.get("role_code") or "团队成员"),
                "group_id": str(row["group_id"]) if row.get("group_id") else None,
                "group_name": str(row.get("group_name") or "未分组"),
                "report_count": 0,
                "task_count": 0,
                "completed_task_count": 0,
                "in_progress_task_count": 0,
                "risk_task_count": 0,
                "output_task_count": 0,
                "completion_total": Decimal("0"),
                "progress_total": Decimal("0"),
                "rated_task_count": 0,
                "tasks": [],
            }
            members[key] = member
        return member

    def ensure_group(group_id: Any, group_name: str) -> dict[str, Any]:
        normalized_name = group_name or "未分组"
        normalized_id = str(group_id) if group_id not in (None, "", 0, "0") else None
        key = normalized_id or f"name:{normalized_name}"
        group = groups.get(key)
        if group is None:
            group = {
                "group_id": normalized_id,
                "group_name": normalized_name,
                "member_ids": set(),
                "task_count": 0,
                "completed_task_count": 0,
                "in_progress_task_count": 0,
                "risk_task_count": 0,
                "output_task_count": 0,
                "completion_total": Decimal("0"),
                "progress_total": Decimal("0"),
                "rated_task_count": 0,
            }
            groups[key] = group
        return group

    for row in visible_members:
        member = ensure_member(row)
        group = ensure_group(row.get("group_id"), str(row.get("group_name") or "未分组"))
        group["member_ids"].add(member["employee_id"] or member["employee_name"])

    for row in report_rows:
        member = ensure_member(row)
        member["report_count"] += 1
        group = ensure_group(row.get("group_id"), str(row.get("group_name") or "未分组"))
        group["member_ids"].add(member["employee_id"] or member["employee_name"])

    for task in group_work_tasks(task_rows):
        member = ensure_member(task)
        group = ensure_group(
            task.get("group_id"),
            str(task.get("group_name") or member["group_name"] or "未分组"),
        )
        member_id = member["employee_id"] or member["employee_name"]
        group["member_ids"].add(member_id)

        progress = task.get("progress_percent")
        completion = task.get("completion_rate")
        try:
            completion_value = Decimal(str(completion if completion is not None else progress or 0))
        except (InvalidOperation, ValueError):
            completion_value = Decimal("0")
        completion_value = max(Decimal("0"), min(Decimal("100"), completion_value))
        progress_value = progress
        try:
            progress_number = Decimal(
                str(progress_value if progress_value is not None else completion or 0)
            )
        except (InvalidOperation, ValueError):
            progress_number = Decimal("0")
        is_risk = str(task.get("on_time_status") or "").lower() in {"overdue", "late"} or bool(
            str(task.get("delay_reason") or "").strip()
        )
        is_completed = str(task.get("on_time_status") or "").lower() in {
            "completed",
            "on_time",
        } or progress_number >= Decimal("100")
        if is_completed:
            status = "已完成"
        elif is_risk:
            status = "延期/风险"
        else:
            status = "进行中"

        member["task_count"] += 1
        group["task_count"] += 1
        member["completion_total"] += completion_value
        member["progress_total"] += progress_number
        group["completion_total"] += completion_value
        group["progress_total"] += progress_number
        member["rated_task_count"] += 1
        group["rated_task_count"] += 1
        if is_completed:
            member["completed_task_count"] += 1
            group["completed_task_count"] += 1
        elif is_risk:
            member["risk_task_count"] += 1
            group["risk_task_count"] += 1
        else:
            member["in_progress_task_count"] += 1
            group["in_progress_task_count"] += 1
        member["output_task_count"] += task["output_detail_count"]
        group["output_task_count"] += task["output_detail_count"]

        if len(member["tasks"]) < 8:
            planned = task.get("planned_completion_date")
            member["tasks"].append(
                {
                    "id": str(task.get("id") or ""),
                    "task_name": str(task.get("task_name_snapshot") or "未命名任务"),
                    "detail_count": task["detail_count"],
                    "completed_detail_count": task["completed_detail_count"],
                    "detail_completion_rate": float(task["detail_completion_rate"]),
                    "customer_name": str(task.get("customer_name_snapshot") or ""),
                    "progress_percent": float(progress_number),
                    "completion_rate": float(completion_value),
                    "status": status,
                    "planned_completion_date": (
                        planned.isoformat()
                        if isinstance(planned, (date, datetime))
                        else str(planned or "")
                    ),
                }
            )

    member_result: list[dict[str, Any]] = []
    for member in members.values():
        rated = int(member.pop("rated_task_count"))
        total = member.pop("completion_total")
        member["completion_rate"] = round(float(total / rated), 1) if rated else 0
        member["progress_percent"] = (
            round(float(member.pop("progress_total") / rated), 1)
            if rated
            else float(member.pop("progress_total"))
        )
        member_result.append(member)
    member_result.sort(
        key=lambda value: (
            -int(value["task_count"]),
            -float(value["completion_rate"]),
            value["employee_name"],
        )
    )

    group_result: list[dict[str, Any]] = []
    for group in groups.values():
        rated = int(group.pop("rated_task_count"))
        total = group.pop("completion_total")
        member_ids = group.pop("member_ids")
        group["member_count"] = len(member_ids)
        group["completion_rate"] = round(float(total / rated), 1) if rated else 0
        group["progress_percent"] = (
            round(float(group.pop("progress_total") / rated), 1)
            if rated
            else float(group.pop("progress_total"))
        )
        group_result.append(group)
    group_result.sort(
        key=lambda value: (
            -int(value["task_count"]),
            -float(value["completion_rate"]),
            value["group_name"],
        )
    )
    return member_result, group_result


def _save_items(
    report: WeeklyReport, value: Any, template_items: Sequence[Mapping[str, Any]], owner_id: int
) -> dict[str, int]:
    submitted = value if isinstance(value, list) else []
    template_map = {str(item["task_code"]): item for item in template_items}
    if any(not isinstance(raw, Mapping) for raw in submitted):
        raise ReportError("工作任务格式无效。")
    try:
        text_refs = save_task_texts(report, submitted)
    except ValueError as exc:
        raise ReportError(str(exc)) from exc
    item_id_map: dict[str, int] = {}
    for index, raw in enumerate(submitted):
        if not isinstance(raw, Mapping):
            continue
        task_code = str(raw.get("task_code") or f"task_{index + 1}").strip()
        config = template_map.get(task_code, {})
        customer_name = str(raw.get("customer_name_snapshot") or "").strip()
        dimension = str(
            raw.get("dimension") or raw.get("section_name") or raw.get("section_code") or ""
        ).strip()
        output_description = str(raw.get("output_description") or "").strip()
        progress = _percent(raw.get("progress_percent"))
        quality = _percent(raw.get("quality_percent"))
        completion = _completion_rate(progress, quality)
        planned = _parse_optional_date(raw.get("planned_completion_date"))
        actual = _parse_optional_date(raw.get("actual_completion_date"))
        expected = _parse_optional_date(raw.get("expected_completion_date"))
        calculated_on_time = _on_time_status(progress, planned, actual, report.as_of_date)
        requested_on_time = str(raw.get("on_time_status") or "").strip()
        on_time = (
            requested_on_time
            if requested_on_time
            in {
                "pending",
                "in_progress",
                "on_time",
                "late",
                "overdue",
                "not_applicable",
                "completed",
            }
            else calculated_on_time
        )
        delay_reason = str(raw.get("delay_reason") or "").strip()
        next_action = str(raw.get("next_action") or "").strip()
        item = WeeklyReportItem.objects.create(
            report_id=report.id,
            scope_type=str(raw.get("scope_type") or config.get("scope_type") or "overall"),
            customer_id=_optional_int(raw.get("customer_id")),
            customer_name_snapshot=""
            if text_refs[index].get("customer_text_id")
            else customer_name,
            section_code=(
                ""
                if text_refs[index].get("dimension_text_id")
                else str(dimension or raw.get("section_code") or config.get("section_code") or "")
            ),
            task_code=task_code,
            task_name_snapshot="",
            **text_refs[index],
            guidance_snapshot=str(
                raw.get("guidance_snapshot") or config.get("guidance") or ""
            ).strip(),
            work_content="",
            output_description=output_description,
            planned_completion_date=planned,
            progress_text=str(raw.get("progress_text") or "").strip(),
            progress_percent=progress,
            quality_percent=quality,
            completion_rate=completion,
            on_time_status=on_time,
            actual_completion_date=actual,
            delay_reason=delay_reason,
            next_action=next_action,
            expected_completion_date=expected,
            owner_id=_optional_int(raw.get("owner_id")) or owner_id,
            owner_name_snapshot=str(raw.get("owner_name_snapshot") or "").strip(),
            collaborator_names=str(raw.get("collaborator_names") or "").strip(),
            document_links=str(raw.get("document_links") or "").strip(),
            sort_order=int(raw.get("sort_order") or index),
        )
        item_id_map[task_code] = int(item.id)
    return item_id_map


def _get_item_progress_state(report_id: int) -> dict[str, tuple[Any, ...]]:
    """读取覆盖保存前的进度状态，用稳定的任务编码识别同一逻辑任务。"""

    return {
        str(row["task_code"]): (
            row["progress_percent"],
            row["quality_percent"],
            row["completion_rate"],
            str(row["on_time_status"] or "in_progress"),
        )
        for row in WeeklyReportItem.objects.filter(report_id=report_id).values(
            "task_code",
            "progress_percent",
            "quality_percent",
            "completion_rate",
            "on_time_status",
        )
    }


def _record_item_progress_history(
    *,
    report: WeeklyReport,
    previous_state: Mapping[str, tuple[Any, ...]],
    recorded_by: int,
) -> None:
    """仅在进度相关字段发生变化时保存历史快照，保留同日多次修改记录。"""

    today = timezone.localdate()
    record_date = min(max(today, report.period_start), report.period_end)
    rows: list[WeeklyReportItemProgressHistory] = []
    for item in WeeklyReportItem.objects.filter(report_id=report.id):
        current_state = (
            item.progress_percent,
            item.quality_percent,
            item.completion_rate,
            str(item.on_time_status or "in_progress"),
        )
        if previous_state.get(item.task_code) == current_state:
            continue
        rows.append(
            WeeklyReportItemProgressHistory(
                report_id=report.id,
                report_item_id=item.id,
                task_code_snapshot=item.task_code,
                progress_percent=item.progress_percent,
                quality_percent=item.quality_percent,
                completion_rate=item.completion_rate,
                on_time_status=item.on_time_status,
                record_date=record_date,
                recorded_by=recorded_by,
            )
        )
    if rows:
        WeeklyReportItemProgressHistory.objects.bulk_create(rows)


def _save_metrics(
    report: WeeklyReport,
    value: Any,
    template_metrics: Sequence[Mapping[str, Any]],
    item_id_map: Mapping[str, int],
) -> None:
    submitted = value if isinstance(value, list) else []
    template_map = {str(item["task_code"]): item for item in template_metrics}
    for raw in submitted:
        if not isinstance(raw, Mapping):
            continue
        code = str(raw.get("metric_code") or "").strip()
        if not code:
            continue
        config = template_map.get(code, {})
        value_type = str(raw.get("value_type") or config.get("value_type") or "number")
        target = _decimal_or_none(raw.get("target_value"), value_type)
        actual = _decimal_or_none(raw.get("actual_value"), value_type)
        if (
            value_type in {"number", "percent", "amount"}
            and actual is None
            and raw.get("actual_value") not in (None, "")
        ):
            metric_label = raw.get("metric_name_snapshot") or config.get("label") or code
            raise ReportError(f"指标“{metric_label}”数值格式无效。")
        if value_type == "percent" and actual is not None and not 0 <= actual <= 100:
            raise ReportError("百分比指标必须在 0—100 范围内。")
        if value_type in {"number", "amount"} and actual is not None and actual < 0:
            raise ReportError("数量和金额指标不能为负数。")
        WeeklyReportMetric.objects.create(
            report_id=report.id,
            item_id=item_id_map.get(str(raw.get("task_code") or ""))
            or _optional_int(raw.get("item_id")),
            metric_code=code,
            metric_name_snapshot=str(
                raw.get("metric_name_snapshot") or config.get("label") or code
            ).strip(),
            value_type=value_type,
            target_value_decimal=target,
            actual_value_decimal=actual,
            value_text=str(raw.get("value_text") or "").strip(),
            unit=str(raw.get("unit") or config.get("unit") or "").strip(),
            precision=int(raw.get("precision") or 0),
            baseline_value_decimal=_decimal_or_none(raw.get("baseline_value"), value_type),
            note=str(raw.get("note") or "").strip(),
        )


def _sync_attachments(
    *,
    value: Any,
    item_id_map: Mapping[str, int],
    existing: Sequence[Attachment],
    report: WeeklyReport,
    user: UserAccount,
) -> None:
    """同步周报附件的任务关联和删除操作。

    文件上传由独立的 multipart 接口完成；周报保存只接收已有附件 ID，确保
    删除任务或移除附件时可以同步清理附件表中的逻辑关联。
    """
    if not isinstance(value, list):
        raise ReportError("附件列表格式无效。")
    submitted = value
    requested: dict[int, tuple[str, str]] = {}
    for raw in submitted:
        if not isinstance(raw, Mapping):
            continue
        attachment_id = _optional_int(raw.get("id") or raw.get("attachment_id"))
        if attachment_id is None:
            continue
        requested[attachment_id] = (
            str(raw.get("task_code") or "").strip(),
            str(raw.get("description") or "").strip()[:500],
        )

    existing_by_id = {int(attachment.id): attachment for attachment in existing}
    pending_ids = set(requested) - set(existing_by_id)
    if pending_ids:
        pending_attachments = Attachment.objects.select_for_update().filter(
            id__in=pending_ids,
            attachment_type="weekly_report_pending",
            relation_id=user.id,
        )
        existing_by_id.update(
            {int(attachment.id): attachment for attachment in pending_attachments}
        )
    unknown_ids = set(requested) - set(existing_by_id)
    if unknown_ids:
        raise ReportError("附件不存在或不属于当前周报。")

    for attachment in existing_by_id.values():
        attachment_id = int(attachment.id)
        if attachment_id not in requested:
            if attachment.attachment_type == "weekly_report":
                _delete_attachment_record(attachment)
            continue
        task_code, description = requested[attachment_id]
        if task_code:
            if task_code not in item_id_map:
                raise ReportError("附件关联的任务不存在。")
            attachment.relation_sub_id = item_id_map[task_code]
        else:
            attachment.relation_sub_id = None
        attachment.attachment_type = "weekly_report"
        attachment.relation_id = report.id
        attachment.description = description
        attachment.save(
            update_fields=[
                "attachment_type",
                "relation_id",
                "relation_sub_id",
                "description",
                "updated_at",
            ]
        )


def _save_daily_tasks(report: WeeklyReport, value: Any) -> None:
    """在周报保存事务内同步日报，保证新建周报可以一并提交日报。"""

    if value is None:
        return
    if not isinstance(value, list):
        raise ReportError("日报列表格式无效。")
    existing = {
        int(row.id): row for row in WeeklyReportDailyTask.objects.filter(report_id=report.id)
    }
    requested_ids: set[int] = set()
    requested_dates: set[date] = set()
    normalized: list[tuple[int | None, date, str]] = []
    for index, raw in enumerate(value):
        if not isinstance(raw, Mapping):
            raise ReportError(f"第 {index + 1} 条日报格式无效。")
        work_date = _parse_optional_date(raw.get("work_date"))
        if work_date is None:
            raise ReportError(f"第 {index + 1} 条日报日期不能为空。")
        if work_date < report.period_start or work_date > report.period_end:
            raise ReportError("日报日期必须在本周范围内。")
        if work_date in requested_dates:
            raise ReportConflictError("同一个日期只能填写一条日报。")
        work_content = str(raw.get("work_content") or "").strip()
        daily_task_id = _optional_int(raw.get("id"))
        if daily_task_id is not None:
            if daily_task_id not in existing or daily_task_id in requested_ids:
                raise ReportError("日报不存在或不属于当前周报。")
            requested_ids.add(daily_task_id)
        requested_dates.add(work_date)
        normalized.append((daily_task_id, work_date, work_content))

    if _effective_report_status(report.status, report.period_start) != REPORT_STATUS_IN_PROGRESS:
        # 未来周报可能带有复制生成的日报；原样回传只表示保留，不属于填写。
        unchanged = len(normalized) == len(existing) and all(
            daily_task_id in existing
            and existing[daily_task_id].work_date == work_date
            and existing[daily_task_id].work_content == work_content
            for daily_task_id, work_date, work_content in normalized
        )
        if unchanged:
            return
        raise ReportError("仅进行中的周报可以填写日报。")

    for daily_task_id, task in existing.items():
        if daily_task_id not in requested_ids:
            task.delete()

    for daily_task_id, work_date, work_content in normalized:
        if daily_task_id is None:
            try:
                WeeklyReportDailyTask.objects.create(
                    report_id=report.id,
                    work_date=work_date,
                    work_content=work_content,
                )
            except IntegrityError as exc:
                raise ReportConflictError("同一个日期只能填写一条日报。") from exc
            continue
        task = existing[daily_task_id]
        task.work_date = work_date
        task.work_content = work_content
        task.save(update_fields=["work_date", "work_content", "updated_at"])


def _delete_attachment_record(attachment: Attachment) -> None:
    """删除附件记录并在事务提交后清理实际存储文件。"""
    storage_key = str(attachment.storage_key or "").strip()
    attachment.delete()
    if storage_key:
        transaction.on_commit(lambda: default_storage.delete(storage_key))


def _load_editable_report(
    *,
    user: UserAccount,
    role_code: str,
    report_id: int | None,
    period_start: date,
) -> WeeklyReport | None:
    if report_id is not None:
        report = WeeklyReport.objects.filter(id=report_id).first()
        if report is None:
            raise ReportNotFoundError("周报不存在。")
        check_part(report)
        if int(report.employee_id) != int(user.id) or report.role_code != role_code:
            raise ReportPermissionError("只能编辑当前角色下自己的周报。")
        if _effective_report_status(report.status, report.period_start) == REPORT_STATUS_COMPLETED:
            raise ReportError("已完成的周报不支持编辑。")
        return report
    if WeeklyReport.objects.filter(
        employee_id=user.id,
        role_code=role_code,
        period_start=period_start,
    ).exists():
        raise ReportConflictError("该角色在此周报周期已有记录，请直接查看或编辑已有周报。")
    return None


def _get_accessible_report(*, user: UserAccount, role_code: str, report_id: int) -> dict[str, Any]:
    header = dao.get_report_header(report_id)
    if header is None:
        raise ReportNotFoundError("周报不存在。")
    if (int(header["employee_id"]) not in visible_employee_ids(user, role_code)
        and int(header["employee_id"]) not in shared_report_owner_ids(user.id)):
        raise ReportPermissionError("无权查看该周报。")
    return _with_report_status(header)


def _serialize_template_item(row: ReportTemplateItem) -> dict[str, Any]:
    config: Any = {}
    try:
        config = json.loads(row.config_json or "{}")
    except json.JSONDecodeError:
        config = {}
    return {
        "item_type": row.item_type,
        "section_code": row.section_code,
        "section_name": row.section_name,
        "task_code": row.task_code,
        "label": row.label,
        "guidance": row.guidance,
        "scope_type": row.scope_type,
        "value_type": row.value_type,
        "unit": row.unit,
        "required": row.required,
        "validation_rule": row.validation_rule,
        "sort_order": row.sort_order,
        "config": config,
    }


def _serialize_row(row: Mapping[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in row.items():
        public_key = key
        if isinstance(value, Decimal):
            result[public_key] = float(value)
        elif isinstance(value, (date, datetime)):
            result[public_key] = value.isoformat()
        elif isinstance(value, bool) or value is None or isinstance(value, (str, int, float)):
            result[public_key] = (
                str(value) if (key == "id" or key.endswith("_id")) and value is not None else value
            )
        elif isinstance(value, (list, dict)):
            result[public_key] = value
        else:
            result[public_key] = str(value)
    return result


def _serialize_report_row(row: Mapping[str, Any]) -> dict[str, Any]:
    """序列化周报并保留持久化状态，不按周期结束日期自动提交。"""
    return _serialize_row(_with_report_status(row))


def _with_report_status(row: Mapping[str, Any]) -> dict[str, Any]:
    result = dict(row)
    result["status"] = _effective_report_status(
        result.get("status"), _as_date(result.get("period_start"))
    )
    return result


def _current_period_start(value: date | None = None) -> date:
    current = value or timezone.localdate()
    return current - timedelta(days=current.weekday())


def _initial_report_status(period_start: date) -> str:
    current_start = _current_period_start()
    if period_start > current_start:
        return REPORT_STATUS_NOT_STARTED
    return REPORT_STATUS_IN_PROGRESS


def _effective_report_status(status: Any, period_start: date | None) -> str:
    """返回展示/校验状态；未来周报待开始，当前及历史未提交周报进行中。"""
    normalized = str(status or "").strip()
    if normalized == REPORT_STATUS_COMPLETED:
        return REPORT_STATUS_COMPLETED
    if normalized == REPORT_STATUS_IN_PROGRESS:
        return REPORT_STATUS_IN_PROGRESS
    if normalized == REPORT_STATUS_NOT_STARTED:
        if period_start is not None and period_start > _current_period_start():
            return REPORT_STATUS_NOT_STARTED
        return REPORT_STATUS_IN_PROGRESS
    return _initial_report_status(period_start or _current_period_start())


def _as_date(value: Any) -> date | None:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if value in (None, ""):
        return None
    try:
        return date.fromisoformat(str(value)[:10])
    except ValueError:
        return None


def _role_name(role_code: str) -> str:
    role = Role.objects.filter(role_code=role_code).first()
    if role:
        return role.role_name
    source = ROLE_TEMPLATES.get(role_code)
    return str(source.get("role_name") if source else role_code)


def _get_template_fields(template_code: str) -> list[dict[str, Any]]:
    """Load task-list columns from the versioned template dictionary.

    ``system_dictionary`` is deliberately used instead of adding a schema
    table: each template/version gets an independent dictionary type, so its
    available columns, order and default visibility can evolve independently.
    """
    fallback = get_default_task_fields(template_code)
    dict_type = f"weekly_report_fields_{template_code}"
    try:
        values = list_active_dictionary_items(dict_type)
    except (OperationalError, ProgrammingError, ValueError):
        return fallback
    if not values:
        return fallback
    fields: list[dict[str, Any]] = []
    for row in values:
        code = str(row.get("dict_code") or "").strip()
        label = str(row.get("dict_name") or "").strip()
        if not code or not label:
            continue
        value = str(row.get("dict_value") or "").strip().lower()
        fields.append(
            {
                "field_code": code,
                "label": label,
                "sort_order": int(row.get("sort_order") or len(fields) + 1),
                "default_visible": value not in {"0", "false", "no", "off"},
            }
        )
    return fields or fallback


def _role_scope(role_code: str) -> str:
    role = Role.objects.filter(role_code=role_code).first()
    return role.scope if role else "self"


def _parse_date(value: Any, *, default: date) -> date:
    parsed = _parse_optional_date(value)
    return parsed or default


def _parse_optional_date(value: Any) -> date | None:
    if value in (None, ""):
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value)[:10])
    except ValueError as exc:
        raise ReportError("日期必须使用 YYYY-MM-DD 格式。") from exc


def _parse_month_key(value: Any, *, required: bool = False) -> str | None:
    if value in (None, ""):
        if required:
            raise ReportError("月度不能为空。")
        return None
    text = str(value).strip()
    try:
        datetime.strptime(text, "%Y-%m")
    except ValueError as exc:
        raise ReportError("月度必须使用 YYYY-MM 格式。") from exc
    return text


def _optional_int(value: Any) -> int | None:
    if value in (None, "", "0", 0):
        return None
    try:
        return int(str(value))
    except (TypeError, ValueError) as exc:
        raise ReportError("逻辑 ID 必须是数字字符串。") from exc


def _percent(value: Any) -> Decimal | None:
    if value in (None, ""):
        return None
    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ReportError("进度和质量必须是数字。") from exc
    if not 0 <= number <= 100:
        raise ReportError("进度和质量必须在 0—100 范围内。")
    # 页面控件按 5% 步进；服务端同样强制校验，避免绕过前端提交任意小数。
    if number != number.to_integral_value() or number % Decimal("5") != 0:
        raise ReportError("进度和质量必须以 5% 为步长填写。")
    return number.quantize(Decimal("1"))


def _completion_rate(progress: Decimal | None, quality: Decimal | None) -> Decimal | None:
    if progress is None:
        return None
    if quality is None:
        return progress
    return ((progress + quality) / Decimal("2")).quantize(Decimal("0.01"))


def _on_time_status(
    progress: Decimal | None, planned: date | None, actual: date | None, as_of: date
) -> str:
    if planned is None:
        return "not_applicable"
    if progress is not None and progress >= 100:
        if actual is None or actual <= planned:
            return "on_time"
        return "late"
    return "overdue" if as_of > planned else "in_progress"


def _decimal_or_none(value: Any, value_type: str) -> Decimal | None:
    if value in (None, "") or value_type == "text":
        return None
    try:
        return Decimal(str(value)).quantize(Decimal("0.01"))
    except (InvalidOperation, ValueError) as exc:
        raise ReportError("指标数值格式无效。") from exc


def _build_trend(items, history_rows, start):
    """先汇总每条明细的当日快照，再按工作任务等权统计趋势。"""
    return task_trend(items, history_rows, start)
