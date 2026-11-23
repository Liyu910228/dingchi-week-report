"""按最新生效内容复制整张主单，所有职位、任务及文本创建独立ID。"""

from datetime import timedelta

from django.core.files.storage import default_storage
from django.db import transaction

from .. import submission_dao as dao
from . import report_copy
from . import submission_read as read
from .monthly_plan_tasks import validate_month_key
from .monthly_plans import copy as monthly_copy
from .submission_scope import aggregate_write


@aggregate_write
def copy(user, role_code, submission_id):
    copied_files = []
    try:
        with transaction.atomic():
            return copy_parts(user, role_code, submission_id, copied_files)
    except Exception:
        for key in copied_files:
            default_storage.delete(key)
        raise


def copy_parts(user, role_code, submission_id, copied_files):
    source = read.accessible(user, role_code, submission_id, lock=True, editable=True)
    if source.kind == "monthly":
        if source.status != "approved":
            raise ValueError("只有审批通过的月度计划支持复制。")
        year, month = map(int, source.month_key.split("-"))
        month = month + 1
        if month == 13:
            year, month = year + 1, 1
        key, start, end = validate_month_key(f"{year:04d}-{month:02d}"), None, None
    else:
        if source.status != "completed":
            raise ValueError("只有已完成的周报支持复制。")
        start, end = source.period_start + timedelta(days=7), source.period_end + timedelta(days=7)
        key = start.strftime("%Y-%m")
    if dao.active_exists(source.kind, user.id, key, start):
        raise ValueError(
            "下个月度计划已存在。" if source.kind == "monthly" else "下个周期的周报已存在。"
        )
    target = dao.create(
        kind=source.kind,
        employee_id=user.id,
        group_id=user.group_id,
        month_key=key,
        period_start=start,
        period_end=end,
        active_key=f"{source.kind}:{user.id}:{start or key}",
        status="draft" if source.kind == "monthly" else "not_started",
    )
    for row in dao.part_rows(source):
        if source.kind == "monthly":
            result = monthly_copy.copy_next_month(
                user, row.role_code, row.id, copied_files=copied_files
            )
            child_id = result["plan"]["id"]
        else:
            result = report_copy.copy_report(
                user=user, role_code=row.role_code, report_id=row.id, copied_files=copied_files
            )
            child_id = result["id"]
            target.status = result["status"]
        dao.attach(source.kind, int(child_id), target.id)
    dao.save(target)
    return {
        **read.detail(user, role_code, target.id),
        "id": str(target.id),
        "period_start": start.isoformat() if start else None,
        "period_end": end.isoformat() if end else None,
        "status": target.status,
    }
