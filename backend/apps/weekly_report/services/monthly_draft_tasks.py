"""草稿仅整理持久化形状，保留待完善原文；业务校验统一在提交时执行。"""

from contextlib import suppress
from datetime import date

from .monthly_task_progress import progress_metadata


def draft_metadata(item):
    fields = ["customer_id", "attachments", "scope_group_key",
              "task_group_key", "content_group_key",
              "progress_text", "progress_percent", "quality_percent", "completion_rate",
              "delay_reason", "on_time_status", "actual_completion_date", "owner_id",
              "owner_name", "collaborator_names", "document_links"]
    fields += [f"{prefix}_{suffix}" for prefix in ("task", "dimension", "customer")
               for suffix in ("source", "template", "values")]
    result = {field: item[field] for field in fields if field in item}
    for prefix in ("task", "dimension", "customer"):
        result.setdefault(f"{prefix}_source", "custom")
        result.setdefault(f"{prefix}_template", "")
        result.setdefault(f"{prefix}_values", [])
    # 进度可计算时保持派生值一致；无效输入留待提交审批时反馈。
    with suppress(ValueError):
        result.update(progress_metadata(item))
    return result


def draft_tasks(value):
    if not isinstance(value, list) or any(not isinstance(item, dict) for item in value):
        raise ValueError("系统错误：月度计划草稿数据格式异常，请刷新后重试。")
    result = []
    for item in value:
        planned = item.get("planned_date") or None
        try:
            planned = date.fromisoformat(planned).isoformat() if planned else None
        except (ValueError, TypeError):
            planned = None
        task = {
            "scope_name": str(item.get("scope_name") or "")[:255],
            "work_task": str(item.get("work_task") or ""),
            "work_content": str(item.get("work_content") or ""),
            "output_description": str(item.get("output_description") or ""),
            "planned_date": planned,
        }
        if item.get("id") and str(item["id"]).isdigit():
            task["id"] = str(item["id"])
        result.append(task)
    return result


def restore_draft(task, raw):
    task.update(draft_metadata(raw))
    for field in ("scope_name", "work_task", "work_content", "output_description", "planned_date"):
        if field in raw:
            task[field] = raw[field]
