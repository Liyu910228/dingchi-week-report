"""月度任务进展字段的白名单校验；与模板元数据一同持久化到版本快照。"""

import re
from datetime import date
from math import isfinite


def progress_metadata(item):
    fields = ("progress_text", "progress_percent", "quality_percent", "completion_rate",
              "delay_reason", "on_time_status", "actual_completion_date", "owner_id",
              "owner_name", "collaborator_names", "document_links")
    if not any(field in item for field in fields):
        return {}
    result = {}
    for field in (
        "progress_text", "delay_reason", "owner_name", "collaborator_names", "document_links",
    ):
        value = item.get(field, "")
        if not isinstance(value, str) or len(value) > 10000:
            raise ValueError("月度计划进展、人员和文档字段必须为文字且不能超过10000字符。")
        result[field] = value.strip()
    for field in ("progress_percent", "quality_percent"):
        value = item.get(field, 0)
        if value is None:
            value = 0
        if (
            isinstance(value, bool) or not isinstance(value, (int, float))
            or not isfinite(value) or not 0 <= value <= 100
        ):
            raise ValueError("月度计划完成进度和质量必须为0到100的数值。")
        result[field] = value
    result["completion_rate"] = int(
        (result["progress_percent"] + result["quality_percent"]) / 2 + 0.5
    )
    status = item.get("on_time_status", "in_progress")
    if status not in (
        "pending", "in_progress", "on_time", "late", "overdue", "completed", "not_applicable",
    ):
        raise ValueError("月度计划完成状态无效。")
    result["on_time_status"] = status
    result.update(completion_metadata(item))
    return result


def completion_metadata(item):
    result = {}
    actual = item.get("actual_completion_date") or ""
    if actual:
        if not isinstance(actual, str) or not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", actual):
            raise ValueError("月度计划实际完成时间必须为有效的YYYY-MM-DD日期。")
        try:
            date.fromisoformat(actual)
        except ValueError as exc:
            raise ValueError("月度计划实际完成时间必须为有效日期。") from exc
    result["actual_completion_date"] = actual
    owner = item.get("owner_id")
    if owner is not None and (
        not isinstance(owner, str) or not re.fullmatch(r"[0-9]{1,20}", owner)
    ):
        raise ValueError("月度计划责任人ID必须为数字字符串或null。")
    result["owner_id"] = owner
    return result
