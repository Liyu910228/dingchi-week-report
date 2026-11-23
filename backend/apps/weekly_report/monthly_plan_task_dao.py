"""独立月度计划明细表的数据访问。"""

from __future__ import annotations

from .models import MonthlyPlan, MonthlyPlanChange, MonthlyPlanRevision, MonthlyPlanTask


def list_tasks(*, employee_id: int, role_code: str, month_key: str) -> list[MonthlyPlanTask]:
    return list(
        MonthlyPlanTask.objects.filter(
            employee_id=employee_id, role_code=role_code, month_key=month_key
        ).order_by("sort_order", "id")
    )


def replace_tasks(
    *, employee_id: int, role_code: str, month_key: str, work_tasks: list[dict[str, str]]
) -> None:
    """在调用方事务内替换指定月份任务，其他员工、角色、月份数据保持独立。"""
    existing = {
        str(task.id): task
        for task in MonthlyPlanTask.objects.select_for_update().filter(
            employee_id=employee_id, role_code=role_code, month_key=month_key
        )
    }
    ids = [task["id"] for task in work_tasks if task.get("id")]
    if len(ids) != len(set(ids)) or any(value not in existing for value in ids):
        raise ValueError("计划明细 ID 不存在、重复或不属于当前月份。")
    # 先移出原排序位置，避免交换顺序时触发唯一约束。
    for index, task in enumerate(existing.values()):
        task.sort_order = 1000 + index
        task.save(update_fields=["sort_order"])
    MonthlyPlanTask.objects.filter(
        id__in=[task.id for key, task in existing.items() if key not in ids]
    ).delete()
    for index, fields in enumerate(work_tasks):
        task = existing.get(fields.get("id"))
        if task is None:
            task = MonthlyPlanTask(
                employee_id=employee_id, role_code=role_code, month_key=month_key
            )
        task.scope_name = fields["scope_name"] or None
        task.work_task = fields["work_task"]
        task.work_content = fields.get("work_content", "")
        task.output_description = fields.get("output_description", "")
        task.planned_date = fields.get("planned_date")
        task.sort_order = index
        task.save()


def latest_task_snapshot(*, employee_id, role_code, month_key):
    """复用现有版本/变更快照保存模板元数据，不扩展任务表结构。"""
    plan = MonthlyPlan.objects.filter(
        employee_id=employee_id, role_code=role_code, month_key=month_key
    ).first()
    if not plan:
        return ""
    revision = (
        MonthlyPlanRevision.objects.filter(monthly_plan_id=plan.id)
        .order_by("-revision", "-id")
        .first()
    )
    change = (
        MonthlyPlanChange.objects.filter(monthly_plan_id=plan.id, status="approved")
        .exclude(published_snapshot_json="")
        .order_by("-effective_revision", "-id")
        .first()
    )
    if change and (not revision or change.effective_revision >= revision.revision):
        return change.published_snapshot_json
    return revision.snapshot_json if revision else ""
