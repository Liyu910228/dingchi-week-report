"""月度周报列表先按人员、月度聚合分页，避免加载全部历史主单。"""

from django.db.models import Max


def paginated_months(rows, page, size):
    groups = (
        rows.order_by()
        .values("employee_id", "month_key")
        .annotate(latest=Max("updated_at"))
        .order_by("-month_key", "-latest", "employee_id")
    )
    return groups.count(), list(groups[(page - 1) * size : page * size])


def month_rows(rows, employee_id, month_key):
    return list(rows.filter(employee_id=employee_id, month_key=month_key))
