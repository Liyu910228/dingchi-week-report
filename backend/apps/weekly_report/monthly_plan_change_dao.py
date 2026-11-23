from .models import MonthlyPlanChange


def find_change(change_id, *, lock=False):
    rows = (
        MonthlyPlanChange.objects.select_for_update() if lock else MonthlyPlanChange.objects.all()
    )
    return rows.filter(id=change_id).first()


def changes_for_plan(plan_id):
    return list(MonthlyPlanChange.objects.filter(monthly_plan_id=plan_id).exclude(status="deleted"))


def changes_by_ids(ids):
    return list(MonthlyPlanChange.objects.filter(id__in=ids))


def changes_for_plans(ids, *, include_deleted=False):
    rows = MonthlyPlanChange.objects.filter(monthly_plan_id__in=ids)
    return list(rows if include_deleted else rows.exclude(status="deleted"))


def active_change(plan_id):
    return MonthlyPlanChange.objects.filter(
        monthly_plan_id=plan_id, status__in=["draft", "rejected", "pending"]
    ).first()


def create_change(**values):
    return MonthlyPlanChange.objects.create(**values)


def save_change(change):
    change.save()
