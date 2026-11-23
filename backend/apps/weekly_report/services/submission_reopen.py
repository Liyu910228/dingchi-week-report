"""系统管理员恢复误提交周报；只更新状态与主单版本，不改填写内容。"""

import logging

from django.db import transaction
from django.utils import timezone

from apps.accounts.public import assigned_role_codes

from .. import submission_dao as dao
from . import submission_read as read

_logger = logging.getLogger(__name__)


@transaction.atomic
def reopen(user, role_code, submission_id):
    if "system_admin" not in assigned_role_codes(user.id):
        raise PermissionError("仅系统管理员可以恢复周报编辑。")
    parent = read.accessible(user, "system_admin", submission_id, lock=True)
    if parent.kind != "weekly":
        raise ValueError("此操作仅支持周报。")
    if parent.status != "completed":
        raise ValueError("只有已完成的周报可以恢复编辑，请刷新列表。")
    rows = dao.part_rows(parent, lock=True)
    if not rows or any(row.status != "completed" for row in rows):
        raise ValueError("周报职位明细状态已变化，请刷新列表后重试。")
    dao.reopen_weekly_parts([row.id for row in rows], timezone.now())
    parent.status = "in_progress"
    parent.submitted_at = None
    parent.revision += 1
    dao.save(parent)
    _logger.info(
        "weekly_report_reopened actor_id=%s submission_id=%s employee_id=%s part_count=%s",
        user.id, parent.id, parent.employee_id, len(rows),
    )
    return {"id": str(parent.id), "status": parent.status,
            "revision": parent.revision, "restored": True}
