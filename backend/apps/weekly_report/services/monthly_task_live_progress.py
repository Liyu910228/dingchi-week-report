"""月度任务实时执行进度；独立于计划基线、提交状态和审批快照。"""

from __future__ import annotations

import json
from typing import Any

from django.db import transaction

from apps.accounts.public import assigned_role_codes, user_profiles

from .. import monthly_plan_task_dao as dao
from ..models import (
    MonthlyPlan,
    MonthlyPlanTask,
    MonthlyPlanTaskProgress,
    MonthlyPlanTaskProgressHistory,
)
from .monthly_task_progress import progress_metadata

PROGRESS_FIELDS = (
    "progress_text",
    "progress_percent",
    "quality_percent",
    "completion_rate",
    "delay_reason",
    "on_time_status",
    "actual_completion_date",
    "owner_id",
    "owner_name",
    "collaborator_names",
    "document_links",
)
FIELD_LABELS = {
    "progress_text": "工作进展",
    "progress_percent": "完成进度",
    "quality_percent": "完成质量",
    "completion_rate": "月度工作完成率",
    "delay_reason": "进度缓慢原因说明",
    "on_time_status": "完成状态",
    "actual_completion_date": "实际完成时间",
    "owner_id": "责任人ID",
    "owner_name": "责任人",
    "collaborator_names": "协作人",
    "document_links": "相关文档链接或佐证材料",
}


class ProgressConflictError(ValueError):
    pass


def _default_progress() -> dict[str, Any]:
    return progress_metadata({"progress_text": ""})


def _stored_snapshot_progress(task_id: int) -> dict[str, Any]:
    task = MonthlyPlanTask.objects.filter(id=task_id).first()
    if not task:
        return _default_progress()
    snapshot = dao.latest_task_snapshot(
        employee_id=task.employee_id, role_code=task.role_code, month_key=task.month_key
    )
    data = json.loads(snapshot or "{}")
    original = next(
        (row for row in data.get("tasks", []) if str(row.get("id")) == str(task_id)), {}
    )
    return (progress_metadata(original) or _default_progress()) if original else _default_progress()


def _progress_values(row: MonthlyPlanTaskProgress | None, task_id: int) -> dict[str, Any]:
    if row:
        return progress_metadata(json.loads(row.data_json or "{}"))
    return _stored_snapshot_progress(task_id)


def overlay_live_progress(tasks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """详情、周报月度区和周报准入读取同一份实时进度；历史审批快照不经过这里。"""
    ids = [int(task["id"]) for task in tasks if str(task.get("id", "")).isdigit()]
    rows = MonthlyPlanTaskProgress.objects.filter(task_id__in=ids).in_bulk(field_name="task_id")
    profiles = user_profiles([row.updated_by for row in rows.values()]) if rows else {}
    for task in tasks:
        row = rows.get(int(task["id"])) if str(task.get("id", "")).isdigit() else None
        if row:
            task.update(progress_metadata(json.loads(row.data_json or "{}")))
        task["progress_revision"] = row.revision if row else 0
        task["progress_updated_at"] = row.updated_at.isoformat() if row else None
        task["progress_updated_by"] = str(row.updated_by) if row else None
        task["progress_updated_by_name"] = (
            profiles.get(row.updated_by, {}).get("employee_name", "") if row else ""
        )
    return tasks


def progress_history(task_ids: list[int], *, limit: int = 100) -> list[dict[str, Any]]:
    if not task_ids:
        return []
    histories = list(
        MonthlyPlanTaskProgressHistory.objects.filter(task_id__in=task_ids).order_by(
            "-created_at", "-id"
        )[:limit]
    )
    tasks = MonthlyPlanTask.objects.filter(id__in=task_ids).in_bulk()
    profiles = user_profiles([row.changed_by for row in histories]) if histories else {}
    result = []
    for row in histories:
        before, after = json.loads(row.before_json or "{}"), json.loads(row.after_json or "{}")
        changes = [
            {
                "field": field,
                "label": FIELD_LABELS[field],
                "before": before.get(field),
                "after": after.get(field),
            }
            for field in PROGRESS_FIELDS
            if field != "owner_id" and before.get(field) != after.get(field)
        ]
        task = tasks.get(row.task_id)
        result.append(
            {
                "id": str(row.id),
                "task_id": str(row.task_id),
                "task_name": task.work_task if task else "已删除任务",
                "revision": row.revision,
                "changed_by": str(row.changed_by),
                "changed_by_name": profiles.get(row.changed_by, {}).get("employee_name", ""),
                "created_at": row.created_at.isoformat(),
                "before": before,
                "after": after,
                "changes": changes,
            }
        )
    return result


@transaction.atomic
def update_live_progress(user, role_code: str, task_id: int, payload: dict[str, Any]):
    unknown = set(payload) - set(PROGRESS_FIELDS) - {"revision"}
    if unknown:
        raise ValueError("已提交计划仅允许更新右侧执行进度，左侧计划基线请通过变更流程修改。")
    task = MonthlyPlanTask.objects.select_for_update().filter(id=task_id).first()
    if not task:
        raise LookupError("月度计划任务不存在或已删除。")
    plan = MonthlyPlan.objects.filter(
        employee_id=task.employee_id, role_code=task.role_code, month_key=task.month_key
    ).first()
    if not plan or plan.status == "deleted":
        raise LookupError("月度计划不存在或已删除。")
    if int(task.employee_id) != int(user.id):
        raise PermissionError("只能更新自己的月度任务进度。")
    if task.role_code != role_code and task.role_code not in assigned_role_codes(user.id):
        raise PermissionError("只能更新本人已分配职位的月度任务进度。")
    row = MonthlyPlanTaskProgress.objects.select_for_update().filter(task_id=task_id).first()
    current_revision = row.revision if row else 0
    if int(payload.get("revision", -1)) != current_revision:
        raise ProgressConflictError("进度已被更新，请重新加载后再修改。")
    before = _progress_values(row, task_id)
    submitted = {key: payload[key] for key in PROGRESS_FIELDS if key in payload}
    after = progress_metadata({**before, **submitted})
    if before == after:
        return {"task_id": str(task_id), "revision": current_revision, "values": after}
    revision = current_revision + 1
    if row:
        row.data_json = json.dumps(after, ensure_ascii=False)
        row.revision = revision
        row.updated_by = user.id
        row.save(update_fields=["data_json", "revision", "updated_by", "updated_at"])
    else:
        row = MonthlyPlanTaskProgress.objects.create(
            task_id=task_id,
            data_json=json.dumps(after, ensure_ascii=False),
            revision=revision,
            updated_by=user.id,
        )
    MonthlyPlanTaskProgressHistory.objects.create(
        task_id=task_id,
        revision=revision,
        changed_by=user.id,
        before_json=json.dumps(before, ensure_ascii=False),
        after_json=json.dumps(after, ensure_ascii=False),
    )
    profile = user_profiles([user.id]).get(int(user.id), {})
    return {
        "task_id": str(task_id),
        "revision": revision,
        "values": after,
        "updated_at": row.updated_at.isoformat(),
        "updated_by": str(user.id),
        "updated_by_name": profile.get("employee_name", ""),
    }
