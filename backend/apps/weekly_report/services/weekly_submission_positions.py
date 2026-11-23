"""未提交周报的临时职位展开；仅显式保存时合并原主单。"""

from apps.accounts.public import reporting_positions

from .. import submission_dao as dao

EDITABLE = {"draft", "in_progress", "not_started"}


def sources(parent, lock=False):
    return {row.role_code: row for row in dao.weekly_rows_for_period(
        parent.employee_id, parent.period_start, lock
    )}


def stamp(row):
    return {
        "source_report_id": str(row.id) if row else None,
        "source_updated_at": row.updated_at.isoformat() if row else None,
        "source_submission_id": str(row.submission_id) if row and row.submission_id else None,
    }


def needs_expansion(parent):
    current = {p["role_code"] for p in reporting_positions(parent.employee_id)}
    stored = {row.role_code for row in dao.part_rows(parent)}
    return parent.legacy or bool(current - stored)


def prepare_save(parent, incoming):
    """锁定来源，拒绝过期页面及已完成来源，调用方事务中执行。"""
    rows = sources(parent, lock=True)
    for part in incoming:
        row = rows.get(part["role_code"])
        if any(part.get(key) != value for key, value in stamp(row).items()):
            raise ValueError("同周期周报数据已更新，请重新加载后保存。")
        if row and row.status not in EDITABLE:
            raise ValueError("同周期存在已完成的职位周报，不支持合并修改。")
    for row in rows.values():
        if row.role_code not in {part["role_code"] for part in incoming}:
            raise ValueError("同周期存在未分配的职位周报，不能合并。")
        if row.submission_id and row.submission_id != parent.id:
            source = dao.find(row.submission_id, lock=True)
            if not source or source.status not in EDITABLE:
                raise ValueError("同周期周报状态已更新，请重新加载。")
            dao.merge_source(source.id, parent.id)
        dao.attach("weekly", row.id, parent.id)
    parent.legacy = False
    parent.active_key = f"weekly:{parent.employee_id}:{parent.period_start}"
