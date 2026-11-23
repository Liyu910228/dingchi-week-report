"""历史单职位月度计划变更的只读职位展开。"""

from apps.accounts.public import report_owner, reporting_positions

from .. import monthly_plan_management_dao as plans
from .. import submission_dao as dao
from . import reports
from . import submission_read as read
from .monthly_plans import read as monthly_read


def expanded_snapshot(parent, user):
    positions = reporting_positions(user.id)
    rows = {row.role_code: row for row in dao.monthly_rows_for_period(user.id, parent.month_key)}
    owner = report_owner(user.id)
    parts = []
    for position in positions:
        code = position["role_code"]
        row = rows.get(code)
        template_code = row.template_code if row else position["template_code"]
        data = monthly_read.detail(owner, code, row.id) if row else None
        parts.append(
            {
                **position,
                "template_code": template_code,
                "template": reports.get_template_by_code(
                    template_code, role_code=code, allow_inactive=True
                ),
                "payload": {
                    "summary": row.summary if row else "",
                    "tasks": data["tasks"] if data else [],
                },
                "source_plan_id": str(row.id) if row else None,
                "id": str(row.id) if row else None,
                "source_revision": row.revision if row else None,
                "source_submission_id": str(row.submission_id)
                if row and row.submission_id
                else None,
            }
        )
    return {
        "expand_legacy_positions": True,
        "month_key": parent.month_key,
        "summary": " / ".join(part["payload"]["summary"] for part in parts),
        "parts": parts,
    }


def source_rows(parent, baseline):
    """保存、提交及发布时复核全部来源，拒绝覆盖并发变更或未完成的独立申请。"""
    current = {
        row.role_code: row
        for row in dao.monthly_rows_for_period(parent.employee_id, parent.month_key)
    }
    result = {}
    for part in baseline["parts"]:
        code = part["role_code"]
        row = current.get(code)
        expected = part.get("source_plan_id")
        if not expected:
            if row:
                raise ValueError("其他职位的月度计划已发生变化，请重新申请变更。")
            result[code] = None
            continue
        row = plans.find_plan(int(expected), lock=True)
        if (
            not row
            or row.status != "approved"
            or row.revision != part["source_revision"]
            or current.get(code) is None
            or current[code].id != row.id
            or str(row.submission_id) != str(part.get("source_submission_id"))
        ):
            raise ValueError("来源月度计划未通过审批或版本已更新，请重新申请变更。")
        source = dao.find(row.submission_id, True) if row.submission_id else None
        if source and source.id != parent.id:
            if {item.role_code for item in dao.part_rows(source)} - {
                item["role_code"] for item in baseline["parts"]
            }:
                raise ValueError("来源计划包含未配置的职位，请先调整职位配置后再合并。")
            children = read.change_rows(source, dao.part_rows(source))
            if source.status != "approved" or any(
                child["status"] in {"draft", "pending", "rejected"} for child in children
            ):
                raise ValueError("其他职位已有未完成的申请，请先处理后再统一变更。")
        result[code] = row
    return result


def needs_expansion(parent, user):
    current = {part["role_code"] for part in reporting_positions(user.id)}
    existing = {row.role_code for row in dao.part_rows(parent)}
    return parent.legacy or bool(current - existing)
