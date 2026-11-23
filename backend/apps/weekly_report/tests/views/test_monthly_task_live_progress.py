import json
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from django.urls import reverse

from apps.weekly_report.models import (
    MonthlyPlan,
    MonthlyPlanRevision,
    MonthlyPlanTask,
    MonthlyPlanTaskProgress,
    MonthlyPlanTaskProgressHistory,
)
from apps.weekly_report.services.monthly_plan_tasks import list_monthly_plan_tasks
from apps.weekly_report.services.monthly_task_live_progress import (
    ProgressConflictError,
    update_live_progress,
)

pytestmark = pytest.mark.django_db


def make_task(status="approved"):
    plan = MonthlyPlan.objects.create(
        employee_id=101,
        role_code="delivery",
        month_key="2026-11",
        summary="固定月度目标",
        template_code="delivery_specialist_v1",
        status=status,
        revision=7,
    )
    task = MonthlyPlanTask.objects.create(
        employee_id=101,
        role_code="delivery",
        month_key="2026-11",
        scope_name="客户A",
        work_task="固定工作任务",
        work_content="固定工作指引",
        output_description="固定输出成果",
        planned_date="2026-11-30",
    )
    snapshot = {
        "summary": plan.summary,
        "tasks": [{
            "id": str(task.id),
            "scope_name": task.scope_name,
            "work_task": task.work_task,
            "work_content": task.work_content,
            "output_description": task.output_description,
            "planned_date": task.planned_date,
            "progress_text": "提交时的进展",
            "progress_percent": 10,
            "quality_percent": 20,
            "on_time_status": "in_progress",
        }],
        "month_key": plan.month_key,
        "template_code": plan.template_code,
    }
    MonthlyPlanRevision.objects.create(
        monthly_plan_id=plan.id,
        revision=plan.revision,
        changed_by=101,
        action="submit",
        snapshot_json=json.dumps(snapshot, ensure_ascii=False),
        changes_json="{}",
    )
    return plan, task, snapshot


def test_submitted_plan_progress_updates_without_changing_baseline_or_approval_snapshot():
    plan, task, snapshot = make_task()
    result = update_live_progress(
        SimpleNamespace(id=101),
        "delivery",
        task.id,
        {
            "progress_text": "11月23日已完成联调",
            "progress_percent": 80,
            "quality_percent": 90,
            "revision": 0,
        },
    )
    assert result["revision"] == 1
    assert result["values"]["completion_rate"] == 85
    plan.refresh_from_db()
    task.refresh_from_db()
    assert plan.status == "approved" and plan.revision == 7
    assert task.work_task == "固定工作任务"
    assert task.output_description == "固定输出成果"
    assert json.loads(MonthlyPlanRevision.objects.get().snapshot_json) == snapshot
    current = list_monthly_plan_tasks(employee_id=101, role_code="delivery", month_key="2026-11")[0]
    assert current["progress_text"] == "11月23日已完成联调"
    assert current["progress_percent"] == 80
    assert current["progress_revision"] == 1
    history = MonthlyPlanTaskProgressHistory.objects.get()
    assert json.loads(history.before_json)["progress_text"] == "提交时的进展"
    assert json.loads(history.after_json)["progress_text"] == "11月23日已完成联调"


@pytest.mark.parametrize("status", ["draft", "pending", "rejected", "approved"])
def test_progress_update_does_not_depend_on_plan_status(status):
    plan, task, _ = make_task(status)
    update_live_progress(
        SimpleNamespace(id=101), "delivery", task.id,
        {"progress_text": f"{status}进度", "revision": 0},
    )
    plan.refresh_from_db()
    assert plan.status == status
    assert MonthlyPlanTaskProgress.objects.get(task_id=task.id).revision == 1


def test_progress_permission_whitelist_and_optimistic_lock():
    _, task, _ = make_task("pending")
    with pytest.raises(PermissionError):
        update_live_progress(SimpleNamespace(id=102), "delivery", task.id, {"revision": 0})
    with pytest.raises(PermissionError):
        update_live_progress(SimpleNamespace(id=101), "manager", task.id, {"revision": 0})
    with pytest.raises(ValueError, match="左侧计划基线"):
        update_live_progress(
            SimpleNamespace(id=101), "delivery", task.id,
            {"work_task": "试图改基线", "revision": 0},
        )
    update_live_progress(
        SimpleNamespace(id=101), "delivery", task.id,
        {"progress_percent": 50, "revision": 0},
    )
    with pytest.raises(ProgressConflictError):
        update_live_progress(
            SimpleNamespace(id=101), "delivery", task.id,
            {"progress_percent": 60, "revision": 0},
        )
    assert MonthlyPlanTaskProgressHistory.objects.count() == 1


def test_multi_position_owner_can_update_assigned_role_outside_default_role():
    _, task, _ = make_task()
    with patch(
        "apps.weekly_report.services.monthly_task_live_progress.assigned_role_codes",
        return_value=["delivery", "recruitment"],
    ):
        result = update_live_progress(
            SimpleNamespace(id=101), "manager", task.id,
            {"progress_text": "多职位更新", "revision": 0},
        )
    assert result["values"]["progress_text"] == "多职位更新"


def test_first_progress_history_does_not_record_default_values_as_changes():
    _, task, _ = make_task()
    revision = MonthlyPlanRevision.objects.get()
    snapshot = json.loads(revision.snapshot_json)
    for field in ("progress_text", "progress_percent", "quality_percent", "on_time_status"):
        snapshot["tasks"][0].pop(field, None)
    revision.snapshot_json = json.dumps(snapshot, ensure_ascii=False)
    revision.save()
    update_live_progress(
        SimpleNamespace(id=101), "delivery", task.id,
        {"progress_text": "只填写进展", "revision": 0},
    )
    history = MonthlyPlanTaskProgressHistory.objects.get()
    before, after = json.loads(history.before_json), json.loads(history.after_json)
    changed = [field for field in after if before.get(field) != after.get(field)]
    assert changed == ["progress_text"]


def test_progress_patch_api_and_validation(client):
    _, task, _ = make_task()
    url = reverse("weekly_report:monthly-plan-task-progress", args=[str(task.id)])
    with patch(
        "apps.weekly_report.monthly_plan_task_views.require_report_user",
        return_value=(SimpleNamespace(id=101), "delivery"),
    ):
        response = client.patch(
            url,
            data=json.dumps({"progress_text": "接口更新", "progress_percent": 70, "revision": 0}),
            content_type="application/json",
        )
    assert response.status_code == 200
    assert response.json()["data"]["values"]["progress_text"] == "接口更新"
    assert response.headers.get("X-Trace-ID")
    with patch(
        "apps.weekly_report.monthly_plan_task_views.require_report_user",
        return_value=(SimpleNamespace(id=101), "delivery"),
    ):
        conflict = client.patch(
            url,
            data=json.dumps({"progress_text": "过期更新", "revision": 0}),
            content_type="application/json",
        )
    assert conflict.status_code == 409
    assert conflict.json()["error"]["code"] == "PROGRESS_CONFLICT"
