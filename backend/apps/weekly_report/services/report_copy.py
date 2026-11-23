"""复制已完成周报到紧邻下一周期，正文和附件均创建独立副本。"""

from datetime import timedelta
from pathlib import PurePosixPath

from django.conf import settings
from django.core.files.storage import default_storage
from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.accounts.public import account_role_scope

from .. import report_copy_dao as dao
from .monthly_plans.policy import ensure_approved
from .reports import ReportConflictError, ReportError, ReportNotFoundError, ReportPermissionError
from .submission_scope import check_part, sync_legacy


def copy_report(*, user, role_code, report_id, copied_files=None):
    stored_files = []
    try:
        with transaction.atomic():
            source = dao.find_report(report_id)
            if source is None:
                raise ReportNotFoundError("周报不存在。")
            if (
                account_role_scope(role_code) == "all"
                or int(source.employee_id) != int(user.id)
                or source.role_code != role_code
            ):
                raise ReportPermissionError("只能复制当前职位下自己的周报。")
            check_part(source)
            if source.status != "completed":
                raise ReportError("只有已完成的周报支持复制。")
            offset = timedelta(days=7)
            start = source.period_start + offset
            if dao.target_exists(source, start):
                raise ReportConflictError("下个周期的周报已存在。")
            month = start.strftime("%Y-%m")
            ensure_approved(user, role_code, month, missing_message="下个月度计划不存在。")
            current_start = timezone.localdate() - timedelta(days=timezone.localdate().weekday())
            target = dao.duplicate(
                source,
                period_start=start,
                period_end=source.period_end + offset,
                month_key=month,
                as_of_date=start,
                status="not_started" if start > current_start else "in_progress",
            )
            sync_legacy(target, "weekly")
            item_map = dao.copy_details(source, target)
            _copy_attachments(source, target, item_map, stored_files)
            result = {
                "id": str(target.id),
                "status": target.status,
                "period_start": start.isoformat(),
                "period_end": target.period_end.isoformat(),
            }
        if copied_files is not None:
            copied_files.extend(stored_files)
        return result
    except Exception as exc:
        for storage_key in stored_files:
            default_storage.delete(storage_key)
        if isinstance(exc, IntegrityError):
            raise ReportConflictError("下个周期的周报已存在。") from exc
        raise


def _copy_attachments(source, target, item_map, stored_files):
    for attachment in dao.attachments(source.id):
        storage_key = attachment.storage_key
        if storage_key:
            name = PurePosixPath(storage_key).name
            with default_storage.open(storage_key, "rb") as content:
                storage_key = default_storage.save(
                    f"weekly_reports/{target.id}/{name}",
                    content,
                )
            stored_files.append(storage_key)
        dao.duplicate(
            attachment,
            relation_id=target.id,
            relation_sub_id=item_map.get(attachment.relation_sub_id),
            storage_key=storage_key,
            file_url=(
                f"{str(settings.MEDIA_URL).rstrip('/')}/{storage_key}"
                if storage_key
                else attachment.file_url
            ),
        )
