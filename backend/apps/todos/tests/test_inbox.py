from datetime import timedelta
from unittest.mock import patch

import pytest
from django.utils import timezone

from apps.accounts.models import Role, UserRole
from apps.approvals.public import pending_monthly_count
from apps.todos.models import TodoItem
from apps.todos.public import complete, publish
from apps.todos.services import inbox, items
from apps.weekly_report.models import WeeklyReport
from apps.weekly_report.services.monthly_plans import approval_read, change_write, read, write
from apps.weekly_report.tests.services.test_monthly_plan_workflow import create
from apps.weekly_report.tests.services.test_monthly_plan_workflow import people as people

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def isolated_weekly_source(monkeypatch, request):
    if not request.node.name.startswith("test_weekly"):
        monkeypatch.setattr("apps.todos.services.sources.weekly_reminder_entries", lambda *args: [])


def test_approval_todo_read_does_not_process_business(people):
    owner, first, second, _ = people
    main = create(people)
    plan_id = int(main["plan"]["id"])
    submission = write.submit(owner, "delivery", plan_id)["approvals"][0]
    assert pending_monthly_count(first.id, "manager") == 1
    assert pending_monthly_count(second.id, "manager") == 0
    data = inbox.list_for_user(first, "manager")
    assert data["total"] == 1 and data["unread_count"] == 1
    todo_id = int(data["items"][0]["id"])
    items.mark_read(first.id, "manager", todo_id)
    again = inbox.list_for_user(first, "manager")
    assert again["total"] == 1 and again["unread_count"] == 0
    assert again["pending_approval_count"] == 1
    assert read.context(first, "manager")["pending_approval_count"] == 1
    record = approval_read.detail_assigned(first, "manager", int(submission["id"]))
    assert record["can_approve"] and record["plan_id"] == str(plan_id)
    with pytest.raises(PermissionError):
        approval_read.detail_assigned(owner, "delivery", int(submission["id"]))
    write.decide(first, "manager", plan_id, {"action": "approve"})
    assert inbox.list_for_user(first, "manager")["total"] == 0
    archived = TodoItem.objects.get(id=todo_id)
    assert archived.status == "completed" and archived.read_at and archived.completed_at
    next_data = inbox.list_for_user(second, "manager")
    assert next_data["total"] == 1 and next_data["pending_approval_count"] == 1
    write.decide(second, "manager", plan_id, {"action": "reject", "reason": "调整目标"})
    assert inbox.list_for_user(second, "manager")["total"] == 0


def test_generic_todo_pagination_idempotence_and_ownership(people):
    owner, first, *_ = people
    for index in range(23):
        publish(
            recipient_id=owner.id,
            role_code="delivery",
            source="other",
            dedupe_key=f"other:{index}",
            title="其他待办",
            target={"kind": "other"},
        )
    first_page = inbox.list_for_user(owner, "delivery")
    assert len(first_page["items"]) == 10 and first_page["total_pages"] == 3
    assert len(inbox.list_for_user(owner, "delivery", 3)["items"]) == 3
    key = TodoItem.objects.get(id=first_page["items"][0]["id"]).dedupe_key
    item = publish(
        recipient_id=owner.id,
        role_code="delivery",
        source="other",
        dedupe_key=key,
        title="其他待办",
        target={"kind": "other"},
    )
    with pytest.raises(LookupError):
        items.mark_read(first.id, "manager", item.id)
    items.mark_read(owner.id, "delivery", item.id)
    publish(
        recipient_id=owner.id,
        role_code="delivery",
        source="other",
        dedupe_key=key,
        title="其他待办",
        target={"kind": "other"},
    )
    assert inbox.list_for_user(owner, "delivery")["unread_count"] == 22
    complete(recipient_id=owner.id, role_code="delivery", dedupe_key=key)
    assert inbox.list_for_user(owner, "delivery")["total"] == 22
    with pytest.raises(ValueError):
        inbox.list_for_user(owner, "delivery", 0)


def test_weekly_reminder_once_per_user_role_week(people):
    owner = people[0]
    role = Role.objects.get(role_code="delivery")
    UserRole.objects.get_or_create(user_id=owner.id, role_id=role.id)
    data = inbox.list_for_user(owner, "delivery")
    assert data["total"] == 1 and data["items"][0]["source"] == "weekly_report"
    items.mark_read(owner.id, "delivery", int(data["items"][0]["id"]))
    TodoItem.objects.filter(id=data["items"][0]["id"]).update(title="交付专员：旧提醒文案")
    refreshed = inbox.list_for_user(owner, "delivery")
    assert refreshed["unread_count"] == 0
    assert refreshed["items"][0]["id"] == data["items"][0]["id"]
    today = timezone.localdate()
    start = today - timedelta(days=today.weekday())
    assert refreshed["items"][0]["title"] == (
        f"本周（{start} 至 {start + timedelta(days=6)}）周报提醒，请及时填写"
    )
    WeeklyReport.objects.create(
        employee_id=owner.id,
        role_code="delivery",
        template_code="delivery_specialist_v1",
        month_key=start.strftime("%Y-%m"),
        period_start=start,
        period_end=start + timedelta(days=6),
        as_of_date=today,
    )
    assert inbox.list_for_user(owner, "delivery")["total"] == 0
    assert TodoItem.objects.get(recipient_id=owner.id).completed_at


def test_todo_api_only_own_records_and_trace(client, people):
    owner, first, *_ = people
    item = publish(
        recipient_id=owner.id,
        role_code="delivery",
        source="other",
        dedupe_key="other:1",
        title="待办",
        target={"kind": "other"},
    )
    assert client.get("/api/v1/todos/").status_code == 401
    with patch("apps.todos.views.require_user", return_value=(owner, "delivery")):
        response = client.get("/api/v1/todos/", {"recipient_id": str(first.id)})
        assert response.status_code == 200 and response.json()["data"]["total"] == 1
        assert response.headers.get("X-Trace-ID")
        assert client.get("/api/v1/todos/", {"page": "bad"}).status_code == 400
        assert client.post(f"/api/v1/todos/{item.id}/read/").json()["data"]["read_at"]
    with patch("apps.todos.views.require_user", return_value=(first, "manager")):
        assert client.post(f"/api/v1/todos/{item.id}/read/").status_code == 404


def test_change_deep_link_and_publish_failure_roll_back_todo(people, monkeypatch):
    owner, first, second, _ = people
    main = create(people)
    plan_id = int(main["plan"]["id"])
    write.submit(owner, "delivery", plan_id)
    write.decide(first, "manager", plan_id, {"action": "approve"})
    write.decide(second, "manager", plan_id, {"action": "approve"})
    child = change_write.create(owner, "delivery", plan_id)
    change_id = int(child["change"]["id"])
    change_write.save(
        owner,
        "delivery",
        change_id,
        {
            "revision": 0,
            "summary": "新目标",
            "tasks": child["snapshot"]["tasks"],
        },
    )
    child = change_write.submit(owner, "delivery", change_id)
    record = approval_read.detail_assigned(first, "manager", int(child["approvals"][0]["id"]))
    assert record["base_snapshot"]["summary"] == "原目标"
    assert record["snapshot"]["summary"] == "新目标" and record["change_id"] == str(change_id)
    filtered = read.list_plans(first, "manager", {"view": "approvals", "month_key": "2026-11"})
    assert filtered["total"] == 0 and filtered["pending_approval_count"] == 1
    change_write.decide(first, "manager", change_id, {"action": "approve"})

    def fail_publish(*args):
        raise ValueError("模拟发布失败")

    monkeypatch.setattr(change_write, "publish", fail_publish)
    with pytest.raises(ValueError, match="发布失败"):
        change_write.decide(second, "manager", change_id, {"action": "approve"})
    assert pending_monthly_count(second.id, "manager") == 1
    assert inbox.list_for_user(second, "manager")["total"] == 1
    assert read.gate(owner, "delivery", "2026-10")["plan"]["summary"] == "原目标"


def test_multi_role_inbox_and_approvals_aggregate_without_switching(people, client):
    owner, first, *_ = people
    UserRole.objects.create(user_id=owner.id, role_id=Role.objects.get(role_code="manager").id)
    for role in ["delivery", "manager"]:
        publish(
            recipient_id=owner.id,
            role_code=role,
            source="other",
            dedupe_key="same-event",
            title="职位提醒",
            target={"kind": "other"},
        )
    own = inbox.list_for_user(owner, "delivery")
    assert own["total"] == inbox.list_for_user(owner, "manager")["total"] == 2
    assert {item["role_code"] for item in own["items"]} == {"delivery", "manager"}
    items.mark_read(owner.id, "delivery", int(own["items"][0]["id"]))
    assert inbox.list_for_user(owner, "manager")["unread_count"] == 1
    with patch("apps.todos.views.require_user", return_value=(owner, "delivery")):
        assert client.post(f"/api/v1/todos/{own['items'][1]['id']}/read/").status_code == 200
    with pytest.raises(LookupError):
        items.mark_read(first.id, "manager", int(own["items"][0]["id"]))
    plan_id = int(create(people)["plan"]["id"])
    record = write.submit(owner, "delivery", plan_id)["approvals"][0]
    assert pending_monthly_count(first.id, "delivery") == 1
    assert read.list_plans(first, "delivery", {"view": "approvals"})["total"] == 1
    assert read.context(first, "delivery")["has_approval_tasks"]
    assert approval_read.detail_assigned(first, "delivery", int(record["id"]))["can_approve"]
    write.decide(first, "delivery", plan_id, {"action": "approve"})


def test_weekly_reminders_share_one_read_state_across_positions(people):
    owner = people[0]
    UserRole.objects.create(user_id=owner.id, role_id=Role.objects.get(role_code="manager").id)
    data = inbox.list_for_user(owner, "delivery")
    assert data["total"] == inbox.list_for_user(owner, "manager")["total"] == 1
    assert data["items"][0]["role_code"] == ""
    items.mark_read(owner.id, "delivery", int(data["items"][0]["id"]))
    assert inbox.list_for_user(owner, "manager")["unread_count"] == 0


def test_role_backfill_keeps_read_state(people):
    import importlib
    from types import SimpleNamespace

    from django.apps import apps
    from django.db import connection

    from apps.approvals.models import ApprovalStep

    owner, first, *_ = people
    plan_id = int(create(people)["plan"]["id"])
    approval_id = int(write.submit(owner, "delivery", plan_id)["approvals"][0]["id"])
    item = TodoItem.objects.get(recipient_id=first.id, source="approval")
    items.mark_read(first.id, "manager", item.id)
    TodoItem.objects.filter(id=item.id).update(role_code="")
    ApprovalStep.objects.filter(approval_id=approval_id).update(approver_role_code="")
    schema = SimpleNamespace(connection=connection)
    importlib.import_module("apps.approvals.migrations.0003_backfill_step_roles").backfill(
        apps, schema
    )
    importlib.import_module("apps.todos.migrations.0003_backfill_roles").backfill(apps, schema)
    item.refresh_from_db()
    assert item.role_code == "manager" and item.read_at
    assert pending_monthly_count(first.id, "manager") == 1
    assert inbox.list_for_user(first, "delivery")["total"] == 1


def test_weekly_multi_position_deduplicates_and_preserves_read_state(people):
    import json

    owner = people[0]
    role = Role.objects.create(
        role_code="extra",
        role_name="额外职位",
        scope="self",
        report_template_code="delivery_specialist_v1",
    )
    UserRole.objects.create(user_id=owner.id, role_id=role.id)
    start = timezone.localdate() - timedelta(days=timezone.localdate().weekday())
    old = []
    for code in ["delivery", "extra"]:
        old.append(
            TodoItem.objects.create(
                recipient_id=owner.id,
                role_code=code,
                source="weekly_report",
                dedupe_key=f"weekly:{code}:{start}",
                title="旧提醒",
                target_json=json.dumps(
                    {"kind": "weekly_report", "period_start": str(start), "role_code": code}
                ),
            )
        )
    old[0].read_at = timezone.now()
    old[0].save()
    data = inbox.list_for_user(owner, "delivery")
    assert data["total"] == 1 and data["unread_count"] == 0
    assert data["items"][0]["target"] == {"kind": "weekly_report", "period_start": str(start)}
    assert inbox.list_for_user(owner, "extra")["items"][0]["id"] == data["items"][0]["id"]
    assert (
        TodoItem.objects.filter(
            recipient_id=owner.id, source="weekly_report", status="pending"
        ).count()
        == 1
    )
    items.mark_read(owner.id, "extra", int(data["items"][0]["id"]))
    WeeklyReport.objects.create(
        employee_id=owner.id,
        role_code="delivery",
        template_code="delivery_specialist_v1",
        month_key=start.strftime("%Y-%m"),
        period_start=start,
        period_end=start + timedelta(days=6),
        as_of_date=start,
    )
    assert inbox.list_for_user(owner, "extra")["total"] == 0
