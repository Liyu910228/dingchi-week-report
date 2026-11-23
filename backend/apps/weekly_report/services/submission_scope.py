"""整单写入边界，阻止旧的单职位写接口拆开修改新主单。"""

from contextvars import ContextVar
from functools import wraps

from .. import submission_dao as dao

_managed = ContextVar("submission_write", default=False)


def aggregate_write(function):
    @wraps(function)
    def wrapped(*args, **kwargs):
        token = _managed.set(True)
        try:
            return function(*args, **kwargs)
        finally:
            _managed.reset(token)

    return wrapped


def check_part(row):
    if not row or not row.submission_id or _managed.get():
        return
    parent = dao.find(row.submission_id)
    if parent and not parent.legacy:
        raise ValueError("请通过整份计划或周报统一保存、提交和复制。")


def sync_legacy(row, kind):
    if _managed.get():
        return
    check_part(row)
    parent = dao.find(row.submission_id) if row.submission_id else None
    if not parent:
        parent = dao.create(
            kind=kind,
            employee_id=row.employee_id,
            group_id=row.group_id,
            month_key=row.month_key,
            period_start=getattr(row, "period_start", None),
            period_end=getattr(row, "period_end", None),
            legacy=True,
        )
        dao.attach(kind, row.id, parent.id)
        row.submission_id = parent.id
    parent.status = row.status
    parent.revision = getattr(row, "revision", 0)
    parent.month_key = row.month_key
    parent.period_start = getattr(row, "period_start", None)
    parent.period_end = getattr(row, "period_end", None)
    dao.save(parent)
