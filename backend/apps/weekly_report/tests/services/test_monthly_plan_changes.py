import importlib
import json
from types import SimpleNamespace

import pytest
from django.apps import apps
from django.db import connection

from apps.accounts.models import Role
from apps.approvals.models import ApprovalRequest, ApprovalStep
from apps.approvals.public import start_approval
from apps.weekly_report.models import MonthlyPlan, MonthlyPlanChange
from apps.weekly_report.services.monthly_plans import change_read, change_write, read, write

from .test_monthly_plan_workflow import create
from .test_monthly_plan_workflow import people as people

pytestmark = pytest.mark.django_db


def effective(people):
    data = create(people)
    plan_id = int(data["plan"]["id"])
    write.submit(people[0], "delivery", plan_id)
    write.decide(people[1], "manager", plan_id, {"action": "approve"})
    return write.decide(people[2], "manager", plan_id, {"action": "approve"})


def test_work_content_roundtrip_approval_and_content_only_change(people):
    data = create(people)
    plan_id = int(data["plan"]["id"])
    tasks = [{**data["tasks"][0], "work_content": "策略：？？"}]
    data = write.save(people[0], "delivery", {
        "revision": data["plan"]["revision"], "summary": "原目标", "tasks": tasks,
    }, plan_id)
    assert data["tasks"][0]["work_content"] == "策略：？？"
    write.submit(people[0], "delivery", plan_id)
    write.decide(people[1], "manager", plan_id, {"action": "approve"})
    main = write.decide(people[2], "manager", plan_id, {"action": "approve"})
    assert main["history"][0]["snapshot"]["tasks"][0]["work_content"] == "策略：？？"
    child = change_write.create(people[0], "delivery", plan_id)
    change_id = int(child["change"]["id"])
    tasks = [{**child["snapshot"]["tasks"][0], "work_content": "已补充策略"}]
    change_write.save(people[0], "delivery", change_id, {
        "revision": child["change"]["revision"], "summary": "原目标", "tasks": tasks,
    })
    change_write.submit(people[0], "delivery", change_id)
    change_write.decide(people[1], "manager", change_id, {"action": "approve"})
    change_write.decide(people[2], "manager", change_id, {"action": "approve"})
    assert read.detail(people[0], "delivery", plan_id)["tasks"][0]["work_content"] == "已补充策略"


def test_change_permissions_validation_and_deleted_audit(people):
    main = effective(people)
    plan_id = int(main["plan"]["id"])
    child = change_write.create(people[0], "delivery", plan_id)
    change_id = int(child["change"]["id"])
    Role.objects.filter(role_code="delivery").update(role_name="交付专员")
    assert change_read.detail(people[1], "manager", change_id)["plan"]["role_name"] == "交付专员"
    with pytest.raises(PermissionError):
        change_read.detail(people[3], "delivery", change_id)
    with pytest.raises(PermissionError):
        change_write.save(people[1], "manager", change_id, {})
    with pytest.raises(ValueError, match="更新"):
        change_write.save(people[0], "delivery", change_id, {"revision": 99})
    with pytest.raises(ValueError, match="修改"):
        change_write.submit(people[0], "delivery", change_id)
    change_write.save(
        people[0],
        "delivery",
        change_id,
        {
            "revision": 0,
            "summary": "新目标",
            "tasks": child["snapshot"]["tasks"],
        },
    )
    change_write.submit(people[0], "delivery", change_id)
    with pytest.raises(ValueError, match="更新"):
        change_write.decide(
            people[1],
            "manager",
            change_id,
            {
                "action": "approve",
                "approval_id": "123",
            },
        )
    with pytest.raises(ValueError, match="原因"):
        change_write.decide(people[1], "manager", change_id, {"action": "reject"})
    change_write.decide(
        people[1],
        "manager",
        change_id,
        {
            "action": "reject",
            "reason": "需完善",
        },
    )
    change_write.delete(people[0], "delivery", change_id)
    assert MonthlyPlanChange.objects.get(id=change_id).status == "deleted"
    assert read.gate(people[0], "delivery", "2026-10")["approved"]
    assert read.detail(people[0], "delivery", plan_id)["plan"]["summary"] == "原目标"
    audit = read.list_plans(people[1], "manager", {"view": "approvals"})
    assert any(row["change_id"] == str(change_id) for row in audit["approvals"])
    assert change_write.create(people[0], "delivery", plan_id)["change"]["id"] != str(change_id)


def test_legacy_pending_change_preserves_approval_nodes(people):
    main = effective(people)
    plan = MonthlyPlan.objects.get(id=main["plan"]["id"])
    baseline = main["history"][0]["snapshot"]
    plan.summary, plan.status, plan.revision = "旧变更申请", "pending", plan.revision + 1
    plan.save()
    approval = start_approval(
        business_type="monthly_plan",
        business_id=plan.id,
        applicant_id=people[0].id,
        revision=plan.revision,
        snapshot={**baseline, "summary": plan.summary},
        approvers=[{"id": str(people[1].id), "name": "first"}],
    )
    request_id = approval
    node_id = ApprovalStep.objects.get(approval_id=request_id).id
    migration = importlib.import_module(
        "apps.weekly_report.migrations.0011_restore_effective_monthly_plans"
    )
    migration.migrate_changes(apps, SimpleNamespace(connection=connection))
    plan.refresh_from_db()
    assert plan.status == "approved" and plan.summary == "原目标"
    child = MonthlyPlanChange.objects.get(monthly_plan_id=plan.id)
    assert child.status == "pending"
    assert json.loads(child.proposed_snapshot_json)["summary"] == "旧变更申请"
    request = ApprovalRequest.objects.get(id=request_id)
    assert request.business_type == "monthly_plan_change" and request.business_id == child.id
    assert ApprovalStep.objects.get(approval_id=request_id).id == node_id
    assert read.gate(people[0], "delivery", "2026-10")["approved"]
    migration.migrate_changes(apps, SimpleNamespace(connection=connection))
    assert MonthlyPlanChange.objects.filter(monthly_plan_id=plan.id).count() == 1


def test_approved_main_cannot_be_deleted(people):
    main = effective(people)
    plan_id = int(main["plan"]["id"])
    with pytest.raises(ValueError, match="审批通过的月度计划不能删除"):
        write.delete(people[0], "delivery", plan_id)
    data = read.detail(people[0], "delivery", plan_id)
    assert data["plan"]["status"] == "approved"
    assert data["tasks"] == main["tasks"]
    assert read.gate(people[0], "delivery", "2026-10")["approved"]


def test_status_filter_matches_children_before_root_pagination(people):
    owner, first, second, outsider = people
    main = effective(people)
    plan_id = int(main["plan"]["id"])
    child = change_write.create(owner, "delivery", plan_id)
    change_id = int(child["change"]["id"])
    write.save(
        owner,
        "delivery",
        {
            "month_key": "2026-11",
            "summary": "其他月份草稿",
            "tasks": [{"scope_name": "客户", "work_task": "任务"}],
        },
    )
    draft = read.list_plans(owner, "delivery", {"view": "mine", "status": "draft", "page_size": 1})
    assert draft["total"] == 2 and draft["total_pages"] == 2
    page2 = read.list_plans(
        owner, "delivery", {"view": "mine", "status": "draft", "page_size": 1, "page": 2}
    )
    assert page2["items"][0]["id"] != draft["items"][0]["id"]
    change_write.save(
        owner,
        "delivery",
        change_id,
        {"revision": 0, "summary": "待审批变更目标", "tasks": child["snapshot"]["tasks"]},
    )
    change_write.submit(owner, "delivery", change_id)
    pending = read.list_plans(owner, "delivery", {"view": "mine", "status": "pending"})
    assert pending["total"] == 1
    assert pending["items"][0]["id"] == str(plan_id)
    assert pending["items"][0]["status"] == "approved"
    assert pending["items"][0]["children"][0]["status"] == "pending"
    assert (
        read.list_plans(
            owner, "delivery", {"view": "mine", "status": "pending", "month_key": "2026-11"}
        )["total"]
        == 0
    )
    assert (
        read.list_plans(outsider, "delivery", {"view": "mine", "status": "pending"})["total"] == 0
    )
    assert read.list_plans(first, "manager", {"view": "members", "status": "pending"})["total"] == 1
    change_write.decide(first, "manager", change_id, {"action": "reject", "reason": "补充细节"})
    assert read.list_plans(owner, "delivery", {"view": "mine", "status": "rejected"})["total"] == 1
    assert read.list_plans(owner, "delivery", {"view": "mine", "status": "pending"})["total"] == 0
    change_write.delete(owner, "delivery", change_id)
    assert MonthlyPlanChange.objects.get(id=change_id).status == "deleted"
    assert read.list_plans(owner, "delivery", {"view": "mine", "status": "rejected"})["total"] == 0
    assert read.list_plans(owner, "delivery", {"view": "mine", "status": "approved"})["total"] == 1


def test_monthly_groups_survive_save_approval_and_change(people):
    data = create(people)
    plan_id = int(data["plan"]["id"])
    first = {**data["tasks"][0], "scope_group_key": "scope-a", "task_group_key": "task-a",
             "work_content": "工作内容一"}
    second = {**first, "work_content": "工作内容二"}
    second.pop("id")
    data = write.save(people[0], "delivery", {
        "revision": data["plan"]["revision"], "summary": "原目标", "tasks": [first, second],
    }, plan_id)
    assert len({task["id"] for task in data["tasks"]}) == 2
    assert {task["task_group_key"] for task in data["tasks"]} == {"task-a"}
    write.submit(people[0], "delivery", plan_id)
    write.decide(people[1], "manager", plan_id, {"action": "approve"})
    write.decide(people[2], "manager", plan_id, {"action": "approve"})
    child = change_write.create(people[0], "delivery", plan_id)
    change_id = int(child["change"]["id"])
    tasks = child["snapshot"]["tasks"]
    assert all(task["scope_group_key"] == "scope-a" for task in tasks)
    tasks[1]["work_content"] = "独立编辑子内容"
    change_write.save(people[0], "delivery", change_id, {
        "revision": child["change"]["revision"], "summary": "原目标", "tasks": tasks,
    })
    change_write.submit(people[0], "delivery", change_id)
    change_write.decide(people[1], "manager", change_id, {"action": "approve"})
    change_write.decide(people[2], "manager", change_id, {"action": "approve"})
    saved = read.detail(people[0], "delivery", plan_id)["tasks"]
    assert [task["work_content"] for task in saved] == ["工作内容一", "独立编辑子内容"]
    assert all(task["task_group_key"] == "task-a" for task in saved)
    assert all(task["scope_group_key"] == "scope-a" for task in saved)
