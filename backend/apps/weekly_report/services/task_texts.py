"""统一保存周任务长文本引用，所有模板共用同一条存取路径。"""

import json
import re

from apps.weekly_report.models import WeeklyReportItem, WeeklyTaskText


def _text_state(raw, kind):
    prefix = kind if kind in {"dimension", "customer"} else "task"
    field = {
        "task": "task_name_snapshot",
        "work": "work_content",
        "dimension": "dimension",
        "customer": "customer_name_snapshot",
    }[kind]
    content = str(
        raw.get(field, raw.get("section_code", "") if kind == "dimension" else "") or ""
    ).strip()
    source = str(raw.get(f"{prefix}_source") or "custom") if kind != "work" else "custom"
    if source not in {"custom", "template"}:
        raise ValueError("任务数据来源无效。")
    template = str(raw.get(f"{prefix}_template") or "") if source == "template" else ""
    values = raw.get(f"{prefix}_values", []) if source == "template" else []
    if not isinstance(values, list) or any(not isinstance(v, str) or len(v) > 256 for v in values):
        raise ValueError("模板占位值格式无效，每项最多256字符。")
    if source == "template":
        parts = re.split(r"[?？]", template)
        if len(values) != len(parts) - 1:
            raise ValueError("模板占位值数量不匹配。")
        content = "".join(
            part + (values[i] if i < len(values) else "") for i, part in enumerate(parts)
        ).strip()
    return content, source, template, json.dumps(values, ensure_ascii=False)


def _resolve_text(report, raw, index, kind, existing, groups):
    id_key, group_key = {
        "task": ("task_text_id", "task_group_key"),
        "work": ("work_content_text_id", "work_content_group_key"),
        "dimension": ("dimension_text_id", "dimension_group_key"),
        "customer": ("customer_text_id", "customer_group_key"),
    }[kind]
    state = _text_state(raw, kind)
    text_id = str(raw.get(id_key) or "")
    if text_id and text_id not in existing:
        raise ValueError("文本引用不存在或不属于当前周报。")
    previous = existing.get(text_id)
    if (
        previous
        and previous.source == "template"
        and report.template_code
        in {
            "delivery_specialist_v1",
            "delivery_assistant_v1",
            "recruitment_v1",
            "ito_sales_v1",
            "innovation_sales_v1",
            "functional_group_v1",
            "human_resources_v1",
        }
        and (state[1] != "template" or state[2] != previous.template_text)
    ):
        raise ValueError("模板任务仅允许修改占位值，不能修改描述文字。")
    key = (kind, text_id or str(raw.get(group_key) or f"row-{index}"))
    if key in groups:
        row, saved_state = groups[key]
        if saved_state != state:
            raise ValueError("同一组共享文本存在冲突，请刷新后重试。")
    else:
        row = previous or WeeklyTaskText(report_id=report.id, content_type=kind)
        if row.content_type != kind:
            raise ValueError("文本引用类型不匹配。")
        row.content, row.source, row.template_text, row.values_json = state
        row.save()
        groups[key] = (row, state)
    return id_key, row.id


def save_task_texts(report, submitted):
    existing = {
        str(row.id): row
        for row in WeeklyTaskText.objects.select_for_update().filter(report_id=report.id)
    }
    groups = {}
    kinds = ("task", "work")
    if report.template_code in {"recruitment_v1", "human_resources_v1"}:
        kinds = ("dimension", *kinds)
    elif report.template_code in {"ito_sales_v1", "innovation_sales_v1"}:
        kinds = ("customer", *kinds)
    return [
        dict(_resolve_text(report, raw, index, kind, existing, groups) for kind in kinds)
        for index, raw in enumerate(submitted)
    ]


def remove_unused_texts(report_id):
    refs = set()
    for task_id, work_id, dimension_id, customer_id in WeeklyReportItem.objects.filter(
        report_id=report_id
    ).values_list("task_text_id", "work_content_text_id", "dimension_text_id", "customer_text_id"):
        refs.update(
            value for value in (task_id, work_id, dimension_id, customer_id) if value is not None
        )
    WeeklyTaskText.objects.filter(report_id=report_id).exclude(id__in=refs).delete()
