import pytest

from apps.weekly_report.models import MonthlyPlan
from apps.weekly_report.services.monthly_plans import change_write, read, write
from apps.weekly_report.services.monthly_plans.copy import copy_next_month

from .test_monthly_plan_changes import effective
from .test_monthly_plan_workflow import create
from .test_monthly_plan_workflow import people as people

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize("template", [
    "delivery_specialist_v1", "delivery_assistant_v1", "recruitment_v1",
    "ito_sales_v1", "innovation_sales_v1", "functional_group_v1", "human_resources_v1",
])
def test_copy_all_templates_independent_draft(people, template):
    main = effective(people)
    source_id = int(main["plan"]["id"])
    MonthlyPlan.objects.filter(id=source_id).update(template_code=template, month_key="2026-12")
    # 本测试保持任务与月份匹配，同时验证跨年。
    from apps.weekly_report.models import MonthlyPlanTask
    MonthlyPlanTask.objects.filter(month_key="2026-10").update(month_key="2026-12")
    copied = copy_next_month(people[0], "delivery", source_id)
    assert copied["plan"]["month_key"] == "2027-01"
    assert copied["plan"]["status"] == "draft"
    assert copied["plan"]["template_code"] == template
    assert copied["plan"]["id"] != str(source_id)
    assert copied["tasks"][0]["id"] != main["tasks"][0]["id"]
    assert copied["tasks"][0]["work_task"] == "原任务"
    assert copied["approvals"] == []
    with pytest.raises(ValueError, match="下个月度计划已存在"):
        copy_next_month(people[0], "delivery", source_id)
    assert read.detail(people[0], "delivery", source_id)["plan"]["status"] == "approved"


@pytest.mark.parametrize("pending", [False, True])
def test_copy_excludes_unapproved_changes(people, pending):
    main = effective(people)
    source_id = int(main["plan"]["id"])
    child = change_write.create(people[0], "delivery", source_id)
    change_id = int(child["change"]["id"])
    change_write.save(people[0], "delivery", change_id, {
        "revision": 0, "summary": "未审批目标",
        "tasks": [{**child["snapshot"]["tasks"][0], "work_task": "未审批任务"}],
    })
    if pending:
        change_write.submit(people[0], "delivery", change_id)
    copied = copy_next_month(people[0], "delivery", source_id)
    assert copied["plan"]["summary"] == "原目标"
    assert copied["tasks"][0]["work_task"] == "原任务"
    assert copied["plan"]["children"] == []


def test_copy_uses_latest_approved_change_and_preserves_metadata(people):
    main = effective(people)
    source_id = int(main["plan"]["id"])
    child = change_write.create(people[0], "delivery", source_id)
    change_id = int(child["change"]["id"])
    task = {**child["snapshot"]["tasks"][0], "work_task": "目标5人",
            "work_content": "最新内容", "task_source": "template",
            "task_template": "目标？人", "task_values": ["5"],
            "scope_group_key": "scope", "task_group_key": "task"}
    change_write.save(people[0], "delivery", change_id, {
        "revision": 0, "summary": "生效新目标", "tasks": [task],
    })
    change_write.submit(people[0], "delivery", change_id)
    for approver in people[1:3]:
        change_write.decide(approver, "manager", change_id, {"action": "approve"})
    copied = copy_next_month(people[0], "delivery", source_id)
    assert copied["plan"]["summary"] == "生效新目标"
    for key in ["work_task", "work_content", "task_source", "task_template", "task_values",
                "scope_group_key", "task_group_key"]:
        assert copied["tasks"][0][key] == task[key]
    write.save(people[0], "delivery", {
        "revision": copied["plan"]["revision"], "summary": "独立修改",
        "tasks": [{**copied["tasks"][0], "work_content": "下月内容"}],
    }, int(copied["plan"]["id"]))
    assert read.detail(people[0], "delivery", source_id)["tasks"][0]["work_content"] == "最新内容"


def test_copy_rejects_draft_and_other_owner(people):
    draft = create(people)
    source_id = int(draft["plan"]["id"])
    with pytest.raises(ValueError, match="仅审批通过"):
        copy_next_month(people[0], "delivery", source_id)
    main = effective_after_draft(people, source_id)
    with pytest.raises(PermissionError):
        copy_next_month(people[1], "manager", int(main["plan"]["id"]))


def effective_after_draft(people, plan_id):
    write.submit(people[0], "delivery", plan_id)
    write.decide(people[1], "manager", plan_id, {"action": "approve"})
    return write.decide(people[2], "manager", plan_id, {"action": "approve"})
