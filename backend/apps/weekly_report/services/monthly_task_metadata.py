"""月度计划模板信息保存在既有版本快照中，正文仍使用原文本列。"""

import json
import re

from .monthly_attachment_metadata import attachment_metadata
from .monthly_draft_tasks import restore_draft
from .monthly_task_progress import progress_metadata
from .monthly_validation_feedback import task_location, validation_feedback


def _field_metadata(item, prefix):
    label = {"task": "工作任务", "dimension": "维度/模块", "customer": "客户/维度"}[prefix]
    source = item.get(f"{prefix}_source", "custom")
    if source not in {"custom", "template"}:
        raise ValueError(f"系统错误：{label}来源标记异常，请刷新后重试；仍失败请联系管理员。")
    if source == "custom":
        return {f"{prefix}_source": "custom", f"{prefix}_template": "", f"{prefix}_values": []}
    template, values = item.get(f"{prefix}_template"), item.get(f"{prefix}_values")
    if not isinstance(template, str) or not template.strip():
        raise ValueError(
            f"系统错误：{label}被标记为模板内容，但模板原文缺失。"
            "请重新选择模板或改为自定义填写；仍失败请联系管理员。"
        )
    if not isinstance(values, list):
        raise ValueError(
            f"系统错误：{label}模板填充值数据缺失或格式异常，请重新选择模板；"
            "仍失败请联系管理员。"
        )
    if len(values) != len(re.findall(r"[?？]", template)):
        raise ValueError(
            f"系统错误：{label}模板的填充值数量与问号占位符数量不一致，"
            "请重新选择模板；仍失败请联系管理员。"
        )
    if any(not isinstance(value, str) or len(value) > 256 for value in values):
        raise ValueError(
            f"{label}模板填写内容校验不通过："
            "每个问号对应的填写内容必须为文字，最多256字符。"
        )
    return {f"{prefix}_source": source, f"{prefix}_template": template, f"{prefix}_values": values}


def _group_metadata(item):
    groups = {}
    for field in ("scope_group_key", "task_group_key", "content_group_key"):
        value = item.get(field)
        if value is None:
            continue
        if not isinstance(value, str) or not value.strip() or len(value) > 128:
            raise ValueError("月度计划分组标识必须为非空文字且不能超过128字符。")
        groups[field] = value
    return groups


def task_metadata(item):
    customer_id = item.get("customer_id")
    if customer_id is not None and not str(customer_id).isdigit():
        raise ValueError("客户ID无效。")
    return {
        "customer_id": str(customer_id) if customer_id else None,
        "attachments": attachment_metadata(item),
        **progress_metadata(item),
        **_group_metadata(item),
        **_field_metadata(item, "task"),
        **_field_metadata(item, "dimension"),
        **_field_metadata(item, "customer"),
    }


def restore_metadata(tasks, snapshot):
    data = json.loads(snapshot or "{}")
    saved = {str(task.get("id")): task for task in data.get("tasks", [])}
    for index, task in enumerate(tasks, 1):
        original = saved.get(str(task["id"]), {})
        stored = original.get("_draft_stored")
        if data.get("draft_content") and original and (
            not stored or all(task.get(field) == value for field, value in stored.items())
        ):
            restore_draft(task, original)
            continue
        if original.get("work_task") == task["work_task"] and (
            original.get("scope_name") or ""
        ) == (task.get("scope_name") or ""):
            try:
                task.update(task_metadata(original))
            except ValueError as exc:
                raise ValueError(
                    f"{task_location(task, index)}：{validation_feedback(str(exc))}"
                ) from exc
    return tasks


def snapshot_with_metadata(snapshot, submitted, *, allow_incomplete=False):
    if allow_incomplete:
        snapshot["draft_content"] = True
    for task, raw in zip(snapshot["tasks"], submitted, strict=True):
        if allow_incomplete:
            task["_draft_stored"] = {
                field: task.get(field) for field in (
                    "scope_name", "work_task", "work_content", "output_description", "planned_date"
                )
            }
            restore_draft(task, raw)
        else:
            task.update(task_metadata(raw))
    return snapshot


def task_content_key(task, *, allow_incomplete=False):
    if allow_incomplete:
        return json.dumps(task, sort_keys=True, ensure_ascii=False, default=str)
    metadata = task_metadata(task)
    return (
        metadata.get("customer_id"),
        json.dumps(metadata["attachments"], sort_keys=True, ensure_ascii=False),
        metadata.get("scope_group_key", ""),
        metadata.get("task_group_key", ""),
        metadata.get("content_group_key", ""),
        task.get("scope_name") or "",
        task.get("work_task"),
        task.get("work_content", ""),
        task.get("output_description", ""),
        task.get("planned_date") or None,
        tuple(sorted(progress_metadata(task).items())),
        metadata["task_source"],
        metadata["task_template"],
        tuple(metadata["task_values"]),
        metadata["dimension_source"],
        metadata["dimension_template"],
        tuple(metadata["dimension_values"]),
        metadata["customer_source"],
        metadata["customer_template"],
        tuple(metadata["customer_values"]),
    )


def validate_group_contents(tasks):
    """分组仅在本次计划载荷内生效，共用字段及其模板信息必须一致。"""
    scopes, groups, contents = {}, {}, {}
    for index, task in enumerate(tasks, 1):
        scope_key = task.get("scope_group_key")
        task_key = task.get("task_group_key")
        scope = tuple(
            json.dumps(task.get(name), ensure_ascii=False, sort_keys=True)
            for name in (
                "scope_name", "customer_source", "customer_template", "customer_values",
                "dimension_source", "dimension_template", "dimension_values",
            )
        )
        content = tuple(
            json.dumps(task.get(name), ensure_ascii=False, sort_keys=True)
            for name in ("work_task", "task_source", "task_template", "task_values")
        )
        if scope_key and scopes.setdefault(scope_key, scope) != scope:
            raise ValueError(
                f"{task_location(task, index)}：系统错误："
                "同一月度计划分组的客户/维度内容不一致，请刷新后重试。"
            )
        if task_key and groups.setdefault((scope_key, task_key), content) != content:
            raise ValueError(
                f"{task_location(task, index)}：系统错误："
                "同一月度计划分组的工作任务内容不一致，请刷新后重试。"
            )

        content_key = task.get("content_group_key")
        if content_key and contents.setdefault(
            (scope_key, task_key, content_key), task.get("work_content", "")
        ) != task.get("work_content", ""):
            raise ValueError(
                f"{task_location(task, index)}：系统错误："
                "同一月度计划分组的工作内容不一致，请刷新后重试。"
            )
