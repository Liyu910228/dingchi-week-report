"""周报每日工作任务（日报）的查询与维护服务。"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from django.db import IntegrityError

from apps.accounts.models import UserAccount

from ..models import WeeklyReport, WeeklyReportDailyTask
from .reports import (
    REPORT_STATUS_IN_PROGRESS,
    ReportConflictError,
    ReportError,
    ReportNotFoundError,
    ReportPermissionError,
    _effective_report_status,
    _get_accessible_report,
    _parse_optional_date,
    _serialize_row,
)


def list_daily_tasks(
    *, user: UserAccount, role_code: str, report_id: int
) -> dict[str, list[dict[str, Any]]]:
    """查询当前用户对指定周报可见的全部日报，不分页。"""

    _get_accessible_report(user=user, role_code=role_code, report_id=report_id)
    return {"items": list_daily_tasks_for_report(report_id)}


def list_daily_tasks_for_report(report_id: int) -> list[dict[str, Any]]:
    """内部读取周报日报，供周报详情一次性返回。"""

    rows = WeeklyReportDailyTask.objects.filter(report_id=report_id).order_by("work_date", "id")
    return [_serialize_daily_task(row) for row in rows]


def create_daily_task(
    *, user: UserAccount, role_code: str, report_id: int, payload: Mapping[str, Any]
) -> dict[str, Any]:
    """创建本人当前周报中的一天日报。"""

    report = _get_editable_report(user=user, role_code=role_code, report_id=report_id)
    work_date, work_content = _validate_payload(report, payload)
    try:
        task = WeeklyReportDailyTask.objects.create(
            report_id=report.id,
            work_date=work_date,
            work_content=work_content,
        )
    except IntegrityError as exc:
        raise ReportConflictError("该日期已有日报。") from exc
    return _serialize_daily_task(task)


def update_daily_task(
    *,
    user: UserAccount,
    role_code: str,
    report_id: int,
    daily_task_id: int,
    payload: Mapping[str, Any],
) -> dict[str, Any]:
    """修改本人当前周报中的一天日报。"""

    report = _get_editable_report(user=user, role_code=role_code, report_id=report_id)
    task = WeeklyReportDailyTask.objects.filter(id=daily_task_id, report_id=report.id).first()
    if task is None:
        raise ReportNotFoundError("日报不存在。")
    work_date, work_content = _validate_payload(report, payload, exclude_id=daily_task_id)
    task.work_date = work_date
    task.work_content = work_content
    try:
        task.save(update_fields=["work_date", "work_content", "updated_at"])
    except IntegrityError as exc:
        raise ReportConflictError("该日期已有日报。") from exc
    return _serialize_daily_task(task)


def delete_daily_task(
    *, user: UserAccount, role_code: str, report_id: int, daily_task_id: int
) -> dict[str, Any]:
    """删除本人当前周报中的一天日报。"""

    report = _get_editable_report(user=user, role_code=role_code, report_id=report_id)
    task = WeeklyReportDailyTask.objects.filter(id=daily_task_id, report_id=report.id).first()
    if task is None:
        raise ReportNotFoundError("日报不存在。")
    task_id = str(task.id)
    task.delete()
    return {"id": task_id, "deleted": True}


def _get_editable_report(
    *, user: UserAccount, role_code: str, report_id: int
) -> WeeklyReport:
    report = WeeklyReport.objects.filter(id=report_id).first()
    if report is None:
        raise ReportNotFoundError("周报不存在。")
    if int(report.employee_id) != int(user.id) or report.role_code != role_code:
        raise ReportPermissionError("只能维护当前角色下自己的日报。")
    if _effective_report_status(report.status, report.period_start) != REPORT_STATUS_IN_PROGRESS:
        raise ReportError("仅进行中的周报可以填写或修改日报。")
    return report


def _validate_payload(
    report: WeeklyReport,
    payload: Mapping[str, Any],
    *,
    exclude_id: int | None = None,
) -> tuple[Any, str]:
    work_date = _parse_optional_date(payload.get("work_date"))
    if work_date is None:
        raise ReportError("日报日期不能为空。")
    if work_date < report.period_start or work_date > report.period_end:
        raise ReportError("日报日期必须在本周范围内。")
    work_content = str(payload.get("work_content") or "").strip()
    if not work_content:
        raise ReportError("主要工作内容不能为空。")
    duplicate_query = WeeklyReportDailyTask.objects.filter(
        report_id=report.id,
        work_date=work_date,
    )
    if exclude_id is not None:
        duplicate_query = duplicate_query.exclude(id=exclude_id)
    if duplicate_query.exists():
        raise ReportConflictError("该日期已有日报。")
    return work_date, work_content


def _serialize_daily_task(task: WeeklyReportDailyTask) -> dict[str, Any]:
    return _serialize_row(
        {
            "id": task.id,
            "report_id": task.report_id,
            "work_date": task.work_date,
            "work_content": task.work_content,
            "created_at": task.created_at,
            "updated_at": task.updated_at,
        }
    )
