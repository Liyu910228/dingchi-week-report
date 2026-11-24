"""按人员及所属月度汇总周报，只读，不创建填报记录。"""

from apps.accounts.public import account_role_name, report_owner, visible_user_ids

from .. import monthly_overview_dao as overview_dao
from .. import submission_dao as dao
from . import submission_read as read
from .monthly_plan_tasks import validate_month_key
from .monthly_plans import read as monthly_read
from .submission_list import validate_filters


def visible_rows(user, role_code, filters):
    validate_filters("weekly", filters)
    if len(str(filters.get("role_code") or "")) > 64:
        raise ValueError("职位编码不能超过64字符。")
    view = filters.get("view") or "members"
    if view not in {"mine", "members"}:
        raise ValueError("查看范围无效。")
    visible = [user.id] if view == "mine" else visible_user_ids(user, role_code)
    return dao.query("weekly", visible, filters)


def month_row(user, role_code, rows, group):
    periods, roles = {}, {}
    employee_name = ""
    for row in rows:
        data = read.serialize(read.accessible(user, role_code, row.id), user, role_code)
        employee_name = data.get("employee_name", "")
        periods.setdefault(row.period_start, []).append(data["status"] == "completed")
        for part in dao.part_rows(row):
            roles[part.role_code] = account_role_name(part.role_code)
    return {
        "employee_id": str(group["employee_id"]),
        "employee_name": employee_name,
        "month_key": group["month_key"],
        "role_name": " / ".join(roles.values()),
        "week_count": len(periods),
        "completed_count": sum(all(states) for states in periods.values()),
        "updated_at": group["latest"].isoformat(),
    }


def list_months(user, role_code, filters):
    page, size = int(filters.get("page") or 1), int(filters.get("page_size") or 10)
    if page < 1 or not 1 <= size <= 100:
        raise ValueError("分页参数无效。")
    rows = visible_rows(user, role_code, filters)
    total, groups = overview_dao.paginated_months(rows, page, size)
    items = [
        month_row(
            user,
            role_code,
            overview_dao.month_rows(rows, group["employee_id"], group["month_key"]),
            group,
        )
        for group in groups
    ]
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": size,
        "total_pages": (total + size - 1) // size,
    }


def week_rows(user, role_code, rows):
    weeks = {}
    for row in sorted(rows, key=lambda value: (value.period_start, value.id)):
        parent = read.accessible(user, role_code, row.id)
        plan = read.serialize(parent, user, role_code)
        week = weeks.setdefault(row.period_start, {"plan": plan, "parts": [], "sources": []})
        week["parts"].extend(read.parts(parent, user, role_code))
        week["sources"].append({"id": plan["id"], "role_name": plan["role_name"]})
        if plan["status"] != "completed":
            week["plan"]["status"] = plan["status"]
    return list(weeks.values())


def approved_month_parts(owner, month_key, weeks):
    monthly_parts = {}
    for week in weeks:
        for part in week["parts"]:
            code = part["role_code"]
            if code in monthly_parts:
                continue
            gate = monthly_read.gate(owner, code, month_key)
            plan = gate["plan"] if gate["approved"] else None
            monthly_parts[code] = {
                **part,
                "monthly_approved": gate["approved"],
                "template_code": plan["template_code"] if plan else part["template_code"],
                "payload": {
                    "summary": plan["summary"] if plan else "",
                    "tasks": gate["tasks"] if plan else [],
                },
            }
    return list(monthly_parts.values())


def detail(user, role_code, employee_id, month_key):
    month_key = validate_month_key(month_key)
    filters = {"view": "members", "employee_id": str(employee_id), "month_key": month_key}
    rows = list(visible_rows(user, role_code, filters))
    if not rows:
        raise LookupError("该月没有可查看的周报，或无权访问。")
    weeks = week_rows(user, role_code, rows)
    return {
        "month_key": month_key,
        "employee_id": str(employee_id),
        "weeks": weeks,
        "monthly_parts": approved_month_parts(report_owner(employee_id), month_key, weeks),
    }
