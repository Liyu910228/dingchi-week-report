from types import SimpleNamespace

import pytest
from django.db import transaction

from apps.accounts.models import Role, UserAccount, UserRole
from apps.accounts.services.managers import set_managers
from apps.accounts.services.monthly_approvers import set_monthly_approvers
from apps.approvals.models import ApprovalRequest
from apps.weekly_report.models import MonthlyPlan, MonthlyPlanRevision
from apps.weekly_report.services import reports
from apps.weekly_report.services.monthly_plans import change_write, read, write
from apps.weekly_report.services.monthly_plans.policy import ensure_approved

pytestmark = pytest.mark.django_db


@pytest.fixture
def people(monkeypatch):
    users = [
        UserAccount.objects.create(
            username=name,
            employee_no=f"DC{index:06d}",
            display_name=name,
            password_ciphertext="test-secret-8",
        )
        for index, name in enumerate(["owner", "first", "second", "outsider"], 1)
    ]
    for role_code, scope in [("delivery", "self"), ("manager", "team"), ("leader", "all")]:
        Role.objects.create(
            role_code=role_code,
            role_name=role_code,
            scope=scope,
            report_template_code="delivery_specialist_v1",
        )
    for user, code in zip(users, ["delivery", "manager", "manager", "leader"], strict=True):
        UserRole.objects.create(user_id=user.id, role_id=Role.objects.get(role_code=code).id)
    monkeypatch.setattr(
        reports, "resolve_role_template", lambda role: {"template_code": "delivery_specialist_v1"}
    )
    set_managers(users[0].id, [str(users[1].id), str(users[2].id)])
    set_monthly_approvers(users[0].id, [str(users[1].id), str(users[2].id)])
    return users


def create(people):
    return write.save(
        people[0],
        "delivery",
        {
            "month_key": "2026-10",
            "summary": "原目标",
            "tasks": [{"scope_name": "客户", "work_task": "原任务"}],
        },
    )


def test_sequential_approval_rejection_resubmit_and_change_history(people):
    owner, first, second, outsider = people
    data = create(people)
    plan_id = int(data["plan"]["id"])
    assert read.gate(owner, "delivery", "2026-10")["approved"] is False
    data = write.submit(owner, "delivery", plan_id)
    assert data["approvals"][0]["steps"][0]["approver_id"] == str(first.id)
    with pytest.raises(PermissionError):
        write.decide(second, "delivery", plan_id, {"action": "approve"})
    with pytest.raises(PermissionError):
        write.decide(outsider, "delivery", plan_id, {"action": "approve"})
    with pytest.raises(ValueError, match="审批期间"):
        write.save(owner, "delivery", {"revision": 1}, plan_id)
    data = write.decide(first, "manager", plan_id, {"action": "approve"})
    assert data["plan"]["status"] == "pending"
    assert data["approvals"][0]["completed_at"] is None
    assert data["approvals"][0]["steps"][0]["acted_at"]
    with pytest.raises(ValueError, match="原因"):
        write.decide(second, "manager", plan_id, {"action": "reject", "reason": " "})
    data = write.decide(second, "manager", plan_id, {"action": "reject", "reason": "目标需调整"})
    assert data["plan"]["rejection_reason"] == "目标需调整"
    assert data["approvals"][0]["completed_at"]
    with pytest.raises(ValueError, match="修改"):
        write.submit(owner, "delivery", plan_id)
    original_task_id = data["tasks"][0]["id"]
    task = {**data["tasks"][0], "work_task": "修改后的任务"}
    data = write.save(
        owner, "delivery", {"revision": 1, "summary": "修改目标", "tasks": [task]}, plan_id
    )
    assert data["tasks"][0]["id"] == original_task_id
    assert data["history"] == []
    data = write.submit(owner, "delivery", plan_id)
    assert len(data["approvals"]) == 2
    assert data["approvals"][1]["snapshot"]["summary"] == "原目标"
    write.decide(first, "manager", plan_id, {"action": "approve"})
    data = write.decide(second, "manager", plan_id, {"action": "approve"})
    assert data["plan"]["status"] == "approved"
    assert data["approvals"][0]["completed_at"]
    with transaction.atomic():
        assert ensure_approved(owner, "delivery", "2026-10").id == plan_id
    assert len(data["history"]) == 1
    with pytest.raises(ValueError, match="变更子流程"):
        write.save(owner, "delivery", {"revision": 2}, plan_id)
    child = change_write.create(owner, "delivery", plan_id)
    change_id = int(child["change"]["id"])
    with pytest.raises(ValueError, match="未完成"):
        change_write.create(owner, "delivery", plan_id)
    child = change_write.save(
        owner,
        "delivery",
        change_id,
        {
            "revision": 0,
            "summary": "再次变更",
            "tasks": [
                {**child["snapshot"]["tasks"][0], "work_task": "最新内容"},
                {"scope_name": "客户", "work_task": "新增内容"},
            ],
        },
    )
    assert child["base_snapshot"]["summary"] == "修改目标"
    change_write.submit(owner, "delivery", change_id)
    assert read.gate(owner, "delivery", "2026-10")["approved"] is True
    assert read.detail(owner, "delivery", plan_id)["plan"]["summary"] == "修改目标"
    with pytest.raises(PermissionError):
        change_write.decide(second, "manager", change_id, {"action": "approve"})
    change_write.decide(first, "manager", change_id, {"action": "reject", "reason": "补充指标"})
    assert read.gate(owner, "delivery", "2026-10")["approved"] is True
    assert len(read.detail(owner, "delivery", plan_id)["history"]) == 1
    with pytest.raises(ValueError, match="修改"):
        change_write.submit(owner, "delivery", change_id)
    child = change_write.save(
        owner,
        "delivery",
        change_id,
        {
            "revision": child["change"]["revision"],
            "summary": "最终目标",
            "tasks": child["snapshot"]["tasks"],
        },
    )
    child = change_write.submit(owner, "delivery", change_id)
    assert len(child["approvals"]) == 2
    records = read.list_plans(first, "manager", {"view": "approvals"})["approvals"]
    assert any(record["change_id"] == str(change_id) for record in records)
    change_write.decide(first, "manager", change_id, {"action": "approve"})
    change_write.decide(second, "manager", change_id, {"action": "approve"})
    data = read.detail(owner, "delivery", plan_id)
    assert data["plan"]["status"] == "approved"
    assert data["plan"]["summary"] == "最终目标"
    assert len(data["tasks"]) == 2
    assert data["tasks"][0]["id"] == original_task_id
    assert data["tasks"][1]["id"].isdigit()
    assert [entry["version"] for entry in data["history"]] == [2, 1]
    assert data["history"][1]["snapshot"]["summary"] == "修改目标"
    assert data["history"][0]["snapshot"]["tasks"] == data["tasks"]
    assert data["plan"]["children"][0]["id"] == str(change_id)
    assert ApprovalRequest.objects.count() == 4


def test_unconfigured_managers_do_not_block_monthly_plan(people):
    owner, first, second, outsider = people
    set_managers(owner.id, [])
    assert create(people)["plan"]["status"] == "draft"
    with pytest.raises(ValueError, match="重复"):
        set_managers(owner.id, [first.id, first.id])
    with pytest.raises(ValueError, match="本人"):
        set_managers(owner.id, [owner.id])
    set_managers(owner.id, [first.id, second.id])
    with pytest.raises(ValueError, match="循环"):
        set_managers(second.id, [owner.id])


def test_visibility_pending_list_and_optimistic_lock(people):
    owner, first, second, outsider = people
    data = create(people)
    plan_id = int(data["plan"]["id"])
    assert read.list_plans(outsider, "delivery", {})["total"] == 0
    assert read.list_plans(first, "manager", {})["total"] == 1
    assert read.list_plans(second, "manager", {})["total"] == 1
    assert read.list_plans(outsider, "leader", {})["total"] == 1
    with pytest.raises(ValueError, match="更新"):
        write.save(owner, "delivery", {"revision": 0}, plan_id)
    write.submit(owner, "delivery", plan_id)
    assert read.list_plans(first, "manager", {"pending_only": "true"})["total"] == 1
    assert read.list_plans(second, "manager", {"pending_only": "true"})["total"] == 0
    write.decide(first, "manager", plan_id, {"action": "approve"})
    assert read.list_plans(second, "manager", {"pending_only": "true"})["total"] == 1


def test_delete_retains_audit_and_inactive_manager_is_blocked(people):
    data = create(people)
    plan_id = int(data["plan"]["id"])
    write.delete(people[0], "delivery", plan_id)
    assert MonthlyPlan.objects.get(id=plan_id).status == "deleted"
    assert MonthlyPlanRevision.objects.filter(monthly_plan_id=plan_id, action="delete").exists()
    assert read.gate(people[0], "delivery", "2026-10")["approved"] is False
    people[1].status = "inactive"
    people[1].save()
    with pytest.raises(ValueError, match="停用"):
        create(people)


def test_gate_uses_exact_role_month_and_not_first_approved_month(people):
    owner = people[0]
    plan = MonthlyPlan.objects.create(
        employee_id=owner.id,
        role_code="delivery",
        month_key="2026-10",
        summary="目标",
        status="approved",
    )
    with transaction.atomic():
        assert ensure_approved(owner, "delivery", "2026-10").id == plan.id
        with pytest.raises(ValueError, match="2026-11"):
            ensure_approved(owner, "delivery", "2026-11")
        with pytest.raises(ValueError):
            ensure_approved(SimpleNamespace(id=owner.id), "another_role", "2026-10")


def test_self_scope_views_all_own_roles_but_cannot_edit_under_wrong_role(people):
    data = create(people)
    Role.objects.create(role_code="another_self", role_name="another", scope="self")
    assert read.list_plans(people[0], "another_self", {})["total"] == 1
    assert read.detail(people[0], "another_self", int(data["plan"]["id"]))["can_edit"] is False
    with pytest.raises(PermissionError):
        write.submit(people[0], "another_self", int(data["plan"]["id"]))


def test_personal_members_and_assigned_approval_tabs(people):
    owner, first, second, outsider = people
    data = create(people)
    plan_id = int(data["plan"]["id"])
    set_managers(first.id, [str(outsider.id)])
    write.save(
        first,
        "manager",
        {
            "month_key": "2026-10",
            "summary": "管理者目标",
            "tasks": [{"scope_name": "客户", "work_task": "管理者计划"}],
        },
    )
    assert read.list_plans(first, "manager", {"view": "mine"})["total"] == 1
    members = read.list_plans(first, "manager", {"view": "members"})
    assert [row["employee_id"] for row in members["items"]] == [str(owner.id)]
    assert read.list_plans(outsider, "leader", {"view": "members"})["total"] == 2
    with pytest.raises(PermissionError):
        read.list_plans(owner, "delivery", {"view": "members"})
    with pytest.raises(PermissionError):
        read.list_plans(outsider, "leader", {"view": "mine"})
    assert read.context(first, "manager")["has_approval_tasks"] is False
    first_submission = write.submit(owner, "delivery", plan_id)["approvals"][0]
    assert read.context(owner, "delivery")["has_approval_tasks"] is False
    assert read.context(first, "manager")["has_approval_tasks"] is True
    assigned = read.list_plans(first, "manager", {"view": "approvals"})
    assert assigned["total"] == 1 and assigned["approvals"][0]["can_approve"]
    waiting = read.list_plans(second, "manager", {"view": "approvals"})
    assert waiting["total"] == 0 and waiting["approvals"] == []
    write.decide(
        first, "manager", plan_id, {"action": "approve", "approval_id": first_submission["id"]}
    )
    processed = read.list_plans(first, "manager", {"view": "approvals"})
    assert processed["approvals"][0]["my_status"] == "approved"
    assert processed["approvals"][0]["my_acted_at"]
    assert not processed["approvals"][0]["can_approve"]
    assert (
        read.list_plans(first, "manager", {"view": "approvals", "pending_only": "true"})["total"]
        == 0
    )
    write.decide(second, "manager", plan_id, {"action": "reject", "reason": "需要调整"})
    write.save(
        owner,
        "delivery",
        {
            "revision": 1,
            "summary": "调整后的目标",
            "tasks": [{"scope_name": "客户", "work_task": "修改后的任务"}],
        },
        plan_id,
    )
    write.submit(owner, "delivery", plan_id)
    history = read.list_plans(first, "manager", {"view": "approvals", "page_size": 1, "page": 2})
    assert history["total"] == 2 and history["total_pages"] == 2
    assert history["approvals"][0]["snapshot"]["summary"] == "原目标"
    filtered = read.list_plans(first, "manager", {"view": "approvals", "month_key": "2026-11"})
    assert filtered["total"] == 0 and filtered["has_approval_tasks"] is True
    with pytest.raises(ValueError, match="更新"):
        write.decide(
            first, "manager", plan_id, {"action": "approve", "approval_id": first_submission["id"]}
        )


@pytest.mark.parametrize("template", ["delivery_specialist_v1", "delivery_assistant_v1"])
def test_template_metadata_survives_save_approval_and_change_without_task_columns(
    people, monkeypatch, template
):
    monkeypatch.setattr(reports, "resolve_role_template", lambda role: {"template_code": template})
    task = {
        "scope_name": "客户",
        "work_task": "入职？人",
        "task_source": "template",
        "task_template": "入职？人",
        "task_values": [""],
    }
    main = write.save(
        people[0],
        "delivery",
        {
            "month_key": "2026-10",
            "summary": "目标",
            "tasks": [task],
        },
    )
    plan_id = int(main["plan"]["id"])
    assert main["tasks"][0]["task_source"] == "template"
    assert main["tasks"][0]["task_values"] == [""]
    write.submit(people[0], "delivery", plan_id)
    write.decide(people[1], "manager", plan_id, {"action": "approve"})
    write.decide(people[2], "manager", plan_id, {"action": "approve"})
    child = change_write.create(people[0], "delivery", plan_id)
    change_id = int(child["change"]["id"])
    changed = {**child["snapshot"]["tasks"][0], "work_task": "入职10人", "task_values": ["10"]}
    change_write.save(
        people[0],
        "delivery",
        change_id,
        {
            "revision": child["change"]["revision"],
            "summary": "目标",
            "tasks": [changed],
        },
    )
    change_write.submit(people[0], "delivery", change_id)
    change_write.decide(people[1], "manager", change_id, {"action": "approve"})
    change_write.decide(people[2], "manager", change_id, {"action": "approve"})
    result = read.detail(people[0], "delivery", plan_id)["tasks"][0]
    assert result["work_task"] == "入职10人"
    assert result["task_source"] == "template"
    assert result["task_template"] == "入职？人"
    assert result["task_values"] == ["10"]
    assert read.gate(people[0], "delivery", "2026-10")["tasks"][0]["task_values"] == ["10"]


def test_identical_custom_text_is_not_inferred_as_template_and_source_only_changes_save(people):
    main = write.save(
        people[0],
        "delivery",
        {
            "month_key": "2026-10",
            "summary": "目标",
            "tasks": [{"scope_name": "客户", "work_task": "入职？人"}],
        },
    )
    assert main["tasks"][0]["task_source"] == "custom"
    original = main["tasks"][0]
    updated = write.save(
        people[0],
        "delivery",
        {
            "revision": main["plan"]["revision"],
            "summary": "目标",
            "tasks": [
                {
                    **original,
                    "task_source": "template",
                    "task_template": "入职？人",
                    "task_values": [""],
                }
            ],
        },
        int(main["plan"]["id"]),
    )
    assert updated["tasks"][0]["task_source"] == "template"
    assert updated["plan"]["revision"] == main["plan"]["revision"] + 1


def test_recruitment_dimension_and_task_metadata_survive_approval_change(people, monkeypatch):
    monkeypatch.setattr(
        reports, "resolve_role_template", lambda role: {"template_code": "recruitment_v1"}
    )
    task = {
        "scope_name": "招聘A组",
        "work_task": "入职4人",
        "dimension_source": "template",
        "dimension_template": "招聘？组",
        "dimension_values": ["A"],
        "task_source": "template",
        "task_template": "入职？人",
        "task_values": ["4"],
    }
    main = write.save(
        people[0], "delivery", {"month_key": "2026-10", "summary": "目标", "tasks": [task]}
    )
    plan_id = int(main["plan"]["id"])
    assert main["tasks"][0]["dimension_values"] == ["A"]
    write.submit(people[0], "delivery", plan_id)
    write.decide(people[1], "manager", plan_id, {"action": "approve"})
    write.decide(people[2], "manager", plan_id, {"action": "approve"})
    child = change_write.create(people[0], "delivery", plan_id)
    change_id = int(child["change"]["id"])
    changed = {
        **child["snapshot"]["tasks"][0],
        "scope_name": "招聘B组",
        "dimension_values": ["B"],
        "work_task": "入职5人",
        "task_values": ["5"],
    }
    change_write.save(
        people[0],
        "delivery",
        change_id,
        {
            "revision": child["change"]["revision"],
            "summary": "目标",
            "tasks": [changed],
        },
    )
    change_write.submit(people[0], "delivery", change_id)
    change_write.decide(people[1], "manager", change_id, {"action": "approve"})
    change_write.decide(people[2], "manager", change_id, {"action": "approve"})
    result = read.gate(people[0], "delivery", "2026-10")["tasks"][0]
    assert result["scope_name"] == "招聘B组" and result["dimension_values"] == ["B"]
    assert result["work_task"] == "入职5人" and result["task_values"] == ["5"]
    assert result["dimension_source"] == result["task_source"] == "template"


@pytest.mark.parametrize("template_code", ["ito_sales_v1", "innovation_sales_v1"])
def test_sales_customer_and_task_metadata_survive_approval_change(
    people, monkeypatch, template_code
):
    monkeypatch.setattr(
        reports, "resolve_role_template", lambda role: {"template_code": template_code}
    )
    task = {
        "scope_name": "客户A",
        "work_task": "入职4人",
        "customer_source": "template",
        "customer_template": "客户？",
        "customer_values": ["A"],
        "task_source": "template",
        "task_template": "入职？人",
        "task_values": ["4"],
    }
    main = write.save(
        people[0], "delivery", {"month_key": "2026-10", "summary": "目标", "tasks": [task]}
    )
    plan_id = int(main["plan"]["id"])
    assert main["tasks"][0]["customer_values"] == ["A"]
    write.submit(people[0], "delivery", plan_id)
    write.decide(people[1], "manager", plan_id, {"action": "approve"})
    write.decide(people[2], "manager", plan_id, {"action": "approve"})
    child = change_write.create(people[0], "delivery", plan_id)
    change_id = int(child["change"]["id"])
    changed = {
        **child["snapshot"]["tasks"][0],
        "scope_name": "客户B",
        "customer_values": ["B"],
        "work_task": "入职5人",
        "task_values": ["5"],
    }
    change_write.save(
        people[0],
        "delivery",
        change_id,
        {
            "revision": child["change"]["revision"],
            "summary": "目标",
            "tasks": [changed],
        },
    )
    change_write.submit(people[0], "delivery", change_id)
    change_write.decide(people[1], "manager", change_id, {"action": "approve"})
    change_write.decide(people[2], "manager", change_id, {"action": "approve"})
    result = read.gate(people[0], "delivery", "2026-10")["tasks"][0]
    assert result["scope_name"] == "客户B" and result["customer_values"] == ["B"]
    assert result["work_task"] == "入职5人" and result["task_values"] == ["5"]
    assert result["customer_source"] == result["task_source"] == "template"


def test_functional_template_plan_without_customer_or_dimension_survives_approval_change(
    people, monkeypatch
):
    monkeypatch.setattr(
        reports, "resolve_role_template", lambda role: {"template_code": "functional_group_v1"}
    )
    task = {
        "work_task": "完成4项",
        "task_source": "template",
        "task_template": "完成？项",
        "task_values": ["4"],
    }
    main = write.save(
        people[0], "delivery", {"month_key": "2026-10", "summary": "职能目标", "tasks": [task]}
    )
    plan_id = int(main["plan"]["id"])
    assert not main["tasks"][0]["scope_name"] and main["tasks"][0]["task_source"] == "template"
    write.submit(people[0], "delivery", plan_id)
    write.decide(people[1], "manager", plan_id, {"action": "approve"})
    write.decide(people[2], "manager", plan_id, {"action": "approve"})
    child = change_write.create(people[0], "delivery", plan_id)
    change_id = int(child["change"]["id"])
    changed = {**child["snapshot"]["tasks"][0], "work_task": "完成5项", "task_values": ["5"]}
    change_write.save(
        people[0],
        "delivery",
        change_id,
        {"revision": child["change"]["revision"], "summary": "职能目标", "tasks": [changed]},
    )
    change_write.submit(people[0], "delivery", change_id)
    change_write.decide(people[1], "manager", change_id, {"action": "approve"})
    change_write.decide(people[2], "manager", change_id, {"action": "approve"})
    result = read.gate(people[0], "delivery", "2026-10")["tasks"][0]
    assert not result["scope_name"] and result["task_source"] == "template"
    assert result["work_task"] == "完成5项" and result["task_values"] == ["5"]


@pytest.mark.parametrize("process", ["initial", "change"])
@pytest.mark.parametrize("approve", [True, False])
def test_approval_lists_only_show_activated_steps(people, process, approve):
    owner, first, second, _ = people
    plan_id = int(create(people)["plan"]["id"])
    if process == "change":
        write.submit(owner, "delivery", plan_id)
        write.decide(first, "manager", plan_id, {"action": "approve"})
        write.decide(second, "manager", plan_id, {"action": "approve"})
        child = change_write.create(owner, "delivery", plan_id)
        business_id = int(child["change"]["id"])
        change_write.save(
            owner,
            "delivery",
            business_id,
            {
                "revision": child["change"]["revision"],
                "summary": "变更目标",
                "tasks": child["snapshot"]["tasks"],
            },
        )
        change_write.submit(owner, "delivery", business_id)
        business_type = "monthly_plan_change"
    else:
        business_id, business_type = plan_id, "monthly_plan"
        write.submit(owner, "delivery", plan_id)
    request_id = str(
        ApprovalRequest.objects.get(
            business_type=business_type,
            business_id=business_id,
            status="pending",
        ).id
    )

    def records(user, **filters):
        return read.list_plans(user, "manager", {"view": "approvals", **filters})

    assert any(row["id"] == request_id for row in records(first)["approvals"])
    for filters in [{}, {"status": "pending"}, {"pending_only": "true"}, {"page_size": 1}]:
        assert all(row["id"] != request_id for row in records(second, **filters)["approvals"])
    decision = {"action": "approve" if approve else "reject", "reason": "需要修改"}
    if process == "change":
        change_write.decide(first, "manager", business_id, decision)
    else:
        write.decide(first, "manager", business_id, decision)
    own = [row for row in records(first)["approvals"] if row["id"] == request_id]
    assert len(own) == 1 and own[0]["my_status"] == ("approved" if approve else "rejected")
    next_rows = records(second, pending_only="true")
    assert next_rows["total"] == (1 if approve else 0)
    if approve:
        assert next_rows["approvals"][0]["id"] == request_id
        assert next_rows["approvals"][0]["can_approve"]
    else:
        for status in ["", "pending", "rejected"]:
            assert all(
                row["id"] != request_id for row in records(second, status=status)["approvals"]
            )
