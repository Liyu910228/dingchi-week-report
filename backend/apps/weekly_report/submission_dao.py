"""统一主单数据访问；单表子查询均保留权限过滤后分页。"""

from pathlib import Path

from django.db.models import Q
from django.db.models.expressions import RawSQL

from .models import MonthlyPlan, WeeklyReport
from .submission_models import ReportSubmission, ReportSubmissionChange


def find(submission_id, lock=False, *, include_deleted=False):
    rows = ReportSubmission.objects.select_for_update() if lock else ReportSubmission.objects.all()
    seen = set()
    while submission_id not in seen:
        seen.add(submission_id)
        candidates = rows.filter(id=submission_id)
        row = (candidates if include_deleted else candidates.exclude(status="deleted")).first()
        if not row or not row.merged_into_id:
            return row
        submission_id = row.merged_into_id
    raise ValueError("月度计划合并关联异常。")


def create(**fields):
    return ReportSubmission.objects.create(**fields)


def save(row):
    row.save()


def part_rows(parent, lock=False, *, include_deleted=False):
    model = MonthlyPlan if parent.kind == "monthly" else WeeklyReport
    rows = model.objects.filter(submission_id=parent.id).order_by("id")
    if not include_deleted:
        rows = rows.exclude(status="deleted")
    return list(rows.select_for_update() if lock else rows)


def attach(kind, part_id, submission_id):
    model = MonthlyPlan if kind == "monthly" else WeeklyReport
    model.objects.filter(id=part_id).update(submission_id=submission_id)


def set_part_status(parent, status):
    model = MonthlyPlan if parent.kind == "monthly" else WeeklyReport
    model.objects.filter(submission_id=parent.id).exclude(status="deleted").update(status=status)


def query(kind, visible_ids, filters, ids=None, *, include_deleted=False):
    rows = ReportSubmission.objects.filter(kind=kind, merged_into_id__isnull=True)
    if not include_deleted:
        rows = rows.exclude(status="deleted")
    rows = (
        rows.filter(id__in=canonical_ids(ids, include_deleted=include_deleted))
        if ids is not None
        else rows.filter(employee_id__in=visible_ids)
    )
    for field in ["month_key", "group_id", "employee_id"]:
        if filters.get(field):
            rows = rows.filter(**{field: filters[field]})
    if filters.get("employee_name"):
        sql = (Path(__file__).parent / "sql/submission_employee_ids.sql").read_text(
            encoding="utf-8"
        )
        rows = rows.filter(employee_id__in=RawSQL(sql, [f"%{filters['employee_name']}%"]))
    if filters.get("status"):
        status = filters["status"]
        if kind == "monthly":
            sql = (Path(__file__).parent / "sql/submission_status_ids.sql").read_text(
                encoding="utf-8"
            )
            rows = rows.filter(Q(status=status) | Q(id__in=RawSQL(sql, [status, status])))
        else:
            rows = rows.filter(status=status)
    if filters.get("period_start"):
        rows = rows.filter(period_start__gte=filters["period_start"])
    if filters.get("period_end"):
        rows = rows.filter(period_end__lte=filters["period_end"])
    if filters.get("role_code"):
        table = "monthly_plan" if kind == "monthly" else "weekly_report"
        sql = (Path(__file__).parent / "sql/submission_role_ids.sql").read_text(encoding="utf-8")
        if include_deleted:
            sql = sql.replace("AND status <> 'deleted'", "")
        rows = rows.filter(id__in=RawSQL(sql.format(part_table=table), [filters["role_code"]]))
    return rows.order_by("-month_key", "-period_start", "-updated_at", "-id")


def pending_changes(parent_id):
    return ReportSubmissionChange.objects.filter(
        submission_id=parent_id, status__in=["draft", "pending", "rejected"]
    )


def changes(parent_id, *, include_deleted=False):
    rows = ReportSubmissionChange.objects.filter(submission_id=parent_id)
    return list(rows if include_deleted else rows.exclude(status="deleted"))


def find_change(change_id, lock=False, *, include_deleted=False):
    rows = (
        ReportSubmissionChange.objects.select_for_update()
        if lock
        else ReportSubmissionChange.objects.all()
    )
    rows = rows.filter(id=change_id)
    return (rows if include_deleted else rows.exclude(status="deleted")).first()


def create_change(**fields):
    return ReportSubmissionChange.objects.create(**fields)


def parent_ids_for_parts(kind, ids):
    model = MonthlyPlan if kind == "monthly" else WeeklyReport
    return list(model.objects.filter(id__in=ids).values_list("submission_id", flat=True))


def change_parent_ids(ids):
    return list(
        ReportSubmissionChange.objects.filter(id__in=ids).values_list("submission_id", flat=True)
    )


def active_exists(kind, user_id, month_key, period_start=None):
    rows = ReportSubmission.objects.filter(kind=kind, employee_id=user_id).exclude(status="deleted")
    return (
        rows.filter(month_key=month_key).exists()
        if kind == "monthly"
        else rows.filter(period_start=period_start).exists()
    )


def find_by_part(part_id):
    for model in [MonthlyPlan, WeeklyReport]:
        row = model.objects.filter(id=part_id).first()
        if row and row.submission_id:
            return find(row.submission_id)
    return None


def monthly_rows_for_period(employee_id, month_key):
    return list(
        MonthlyPlan.objects.filter(employee_id=employee_id, month_key=month_key)
        .exclude(status="deleted")
        .order_by("id")
    )


def merged_source_ids(parent_id):
    result, frontier = set(), [parent_id]
    while frontier:
        ids = (
            set(
                ReportSubmission.objects.filter(merged_into_id__in=frontier).values_list(
                    "id", flat=True
                )
            )
            - result
        )
        result.update(ids)
        frontier = list(ids)
    return sorted(result)


def merge_source(source_id, parent_id):
    ReportSubmission.objects.filter(id=source_id).update(merged_into_id=parent_id, active_key=None)


def create_monthly_part(**values):
    return MonthlyPlan.objects.create(**values)


def canonical_ids(ids, *, include_deleted=False):
    return list(
        {
            row.id
            for value in ids
            if (row := find(value, include_deleted=include_deleted)) is not None
        }
    )


def weekly_rows_for_period(employee_id, period_start, lock=False):
    rows = WeeklyReport.objects.filter(employee_id=employee_id, period_start=period_start)
    if lock:
        rows = rows.select_for_update()
    return list(rows.exclude(status="deleted").order_by("id"))


def reopen_weekly_parts(part_ids, updated_at):
    WeeklyReport.objects.filter(id__in=part_ids).update(status="in_progress", updated_at=updated_at)
