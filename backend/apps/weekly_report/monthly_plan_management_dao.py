from pathlib import Path

from django.db.models.expressions import RawSQL

from .models import MonthlyPlan, MonthlyPlanRevision, WeeklyReport


def find_plan(plan_id=None, *, employee_id=None, role_code=None, month_key=None, lock=False):
    rows = MonthlyPlan.objects.select_for_update() if lock else MonthlyPlan.objects.all()
    if plan_id is not None:
        return rows.filter(id=plan_id).first()
    return rows.filter(employee_id=employee_id, role_code=role_code, month_key=month_key).first()


def plans():
    return MonthlyPlan.objects.exclude(status="deleted").order_by(
        "-month_key", "-updated_at", "-id"
    )


def paginated_plans(
    *, visible_ids, own_role, pending_ids, filters, page, size, exclude_employee=None
):
    rows = plans()
    if pending_ids is not None:
        rows = rows.filter(id__in=pending_ids)
    else:
        rows = rows.filter(employee_id__in=visible_ids)
        if exclude_employee is not None:
            rows = rows.exclude(employee_id=exclude_employee)
        if own_role:
            rows = rows.filter(role_code=own_role)
    for field in ["month_key", "employee_id", "group_id", "role_code"]:
        if filters.get(field):
            rows = rows.filter(**{field: filters[field]})
    if filters.get("status"):
        sql = (Path(__file__).with_name("dao") / "sql" / "monthly_status_roots.sql").read_text(
            encoding="utf-8"
        )
        rows = rows.filter(id__in=RawSQL(sql, [filters["status"], filters["status"]]))
    return rows.count(), list(rows[(page - 1) * size : page * size])


def approval_plans(ids, filters):
    rows = MonthlyPlan.objects.filter(id__in=ids)
    for field in ["month_key", "employee_id", "group_id", "role_code"]:
        if filters.get(field):
            rows = rows.filter(**{field: filters[field]})
    return list(rows)


def create_plan(**fields):
    return MonthlyPlan.objects.create(**fields)


def save_plan(plan):
    plan.save()


def append_revision(**fields):
    return MonthlyPlanRevision.objects.create(**fields)


def has_report(employee_id, role_code, month_key):
    return WeeklyReport.objects.filter(
        employee_id=employee_id, role_code=role_code, month_key=month_key
    ).exists()
