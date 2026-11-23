"""独立月度计划列表的读取、校验和事务保存。"""

from __future__ import annotations

import re
from collections.abc import Mapping
from datetime import date
from typing import Any

from django.db import transaction

from .. import monthly_plan_task_dao as dao
from .monthly_draft_tasks import draft_tasks
from .monthly_task_metadata import restore_metadata, task_metadata, validate_group_contents
from .monthly_validation_feedback import scope_label, task_location, validation_feedback


def validate_month_key(month_key: str) -> str:
    if not re.fullmatch(r"[0-9]{4}-(0[1-9]|1[0-2])", month_key) or month_key.startswith("0000"):
        raise ValueError("所属月份必须为 YYYY-MM 格式的有效月份。")
    return month_key


def list_monthly_plan_tasks(
    *, employee_id: int, role_code: str, month_key: str
) -> list[dict[str, Any]]:
    """内部读取已获授权的员工月度明细；权限由周报服务或本人接口入口确定。"""
    rows = dao.list_tasks(
        employee_id=employee_id, role_code=role_code, month_key=validate_month_key(month_key)
    )
    items = [
        {
            "id": str(row.id),
            "scope_name": row.scope_name or "",
            # 旧客户端的输入输出兼容别名，不对应独立数据库字段。
            "customer_name": row.scope_name or "",
            "dimension": row.scope_name or "",
            "work_task": row.work_task,
            "work_content": row.work_content,
            "output_description": row.output_description,
            "planned_date": row.planned_date.isoformat() if row.planned_date else None,
            "sort_order": row.sort_order,
            "updated_at": row.updated_at.isoformat(),
        }
        for row in rows
    ]
    items = restore_metadata(
        items,
        dao.latest_task_snapshot(employee_id=employee_id, role_code=role_code, month_key=month_key),
    )
    from .monthly_task_live_progress import overlay_live_progress

    return overlay_live_progress(items)


def validate_tasks(
    value: Any, template_code: str = "", *, allow_incomplete=False
) -> list[dict[str, Any]]:
    if allow_incomplete:
        return draft_tasks(value)
    if not isinstance(value, list):
        raise ValueError("系统错误：月度计划明细数据格式异常，请刷新后重试；仍失败请联系管理员。")
    if len(value) > 200:
        raise ValueError("月度计划填写内容校验不通过：最多支持200条明细，请减少任务数量。")
    work_tasks = []
    for index, item in enumerate(value, 1):
        try:
            work_tasks.append(validate_task(item))
        except ValueError as exc:
            raise ValueError(
                f"{task_location(item, index, template_code)}：{validation_feedback(str(exc))}"
            ) from exc
    validate_group_contents(work_tasks)
    return work_tasks


def validate_task(item):
    if not isinstance(item, Mapping) or not isinstance(item.get("work_task"), str):
        raise ValueError("月度计划中的工作任务必须为文字。")
    work_task = item["work_task"].strip()
    if not work_task:
        raise ValueError("月度计划工作任务不能为空。")
    scope_name = item.get("scope_name", item.get("dimension") or item.get("customer_name", ""))
    if scope_name is None:
        scope_name = ""
    if not isinstance(scope_name, str) or len(scope_name.strip()) > 255:
        raise ValueError("月度计划客户/维度必须为文字且不能超过 255 个字符。")
    work_content = item.get("work_content", "")
    if not isinstance(work_content, str) or len(work_content) > 10000:
        raise ValueError("月度计划主要工作内容必须为文字且不能超过 10000 个字符。")
    normalized = {
        "scope_name": scope_name.strip(),
        "work_task": work_task,
        "work_content": work_content.strip(),
    }
    normalized.update(validate_outcome(item))
    normalized.update(task_metadata(item))
    task_id = item.get("id")
    if task_id and str(task_id).isdigit():
        normalized["id"] = str(task_id)
    return normalized

def validate_outcome(item):
    output = item.get("output_description", "")
    if not isinstance(output, str) or len(output) > 10000:
        raise ValueError("月度计划输出成果必须为文字且不能超过10000字符。")
    planned = item.get("planned_date") or None
    if planned is not None:
        if not isinstance(planned, str) or not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", planned):
            raise ValueError("月度计划计划完成时间必须为有效的 YYYY-MM-DD 日期。")
        try:
            date.fromisoformat(planned)
        except ValueError as exc:
            raise ValueError("月度计划计划完成时间必须为有效日期。") from exc
    return {"output_description": output.strip(), "planned_date": planned}


def validate_report_monthly_data(summary: Any, tasks: Any, template_code: str) -> None:
    """月度计划保存和提交必须具备有效月度目标和至少一条有效明细。"""
    if not isinstance(summary, str) or not summary.strip():
        raise ValueError("月度目标填写内容校验不通过：请填写月度目标。")
    if len(summary) > 10000:
        raise ValueError("月度目标填写内容校验不通过：月度目标不能超过10000字符。")
    normalized = validate_tasks(tasks, template_code)
    if not normalized:
        raise ValueError("请至少填写一条月度计划。")
    if template_code == "functional_group_v1":
        return
    for index, task in enumerate(normalized, 1):
        if not task["scope_name"]:
            raise ValueError(
                f"{task_location(task, index, template_code)}：填写内容校验不通过："
                f"{scope_label(template_code)}不能为空，请补充后提交。"
            )



@transaction.atomic
def save_monthly_plan_tasks(
    *, employee_id: int, role_code: str, month_key: str, value: Any, allow_incomplete=False
) -> None:
    """由月度计划管理写用例调用，在同一事务中保存共用月度任务及变更历史。"""
    dao.replace_tasks(
        employee_id=employee_id,
        role_code=role_code,
        month_key=validate_month_key(month_key),
        work_tasks=validate_tasks(value, allow_incomplete=allow_incomplete),
    )
