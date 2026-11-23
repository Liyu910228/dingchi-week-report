from datetime import UTC, datetime, timedelta
from unittest.mock import patch

import pytest

from apps.todos.dao import read_history_cutoff
from apps.todos.models import TodoItem
from apps.todos.public import publish
from apps.todos.services import items
from apps.weekly_report.services.monthly_plans import write
from apps.weekly_report.tests.services.test_monthly_plan_workflow import create
from apps.weekly_report.tests.services.test_monthly_plan_workflow import people as people

pytestmark = pytest.mark.django_db


def make_item(user, key, created, *, read=False, role="delivery", status="pending"):
    item = publish(
        recipient_id=user.id,
        role_code=role,
        source="other",
        dedupe_key=key,
        title=key,
        target={"kind": "other"},
    )
    TodoItem.objects.filter(id=item.id).update(
        created_at=created, read_at=created if read else None, status=status
    )
    return str(item.id)


def test_unread_first_and_recent_read_filter_before_pagination(people):
    owner = people[0]
    now = datetime(2026, 10, 14, 12, tzinfo=UTC)
    cutoff = datetime(2026, 7, 14, 12, tzinfo=UTC)
    recent_read = make_item(owner, "read-recent", now - timedelta(hours=1), read=True)
    boundary_read = make_item(owner, "read-boundary", cutoff, read=True)
    unread_old = make_item(owner, "unread-old", now - timedelta(days=500))
    unread_new = make_item(owner, "unread-new", now - timedelta(days=1))
    for index in range(12):
        make_item(owner, f"expired-read-{index}", cutoff - timedelta(seconds=index + 1), read=True)
    make_item(owner, "other-role", now, role="manager")
    make_item(owner, "completed", now, status="completed")
    make_item(people[1], "other-user", now)
    with patch("apps.todos.dao.timezone.now", return_value=now):
        result = items.list_items(owner.id, "delivery")
    assert result["total"] == 4 and result["total_pages"] == 1 and result["unread_count"] == 2
    assert [row["id"] for row in result["items"]] == [
        unread_new,
        unread_old,
        recent_read,
        boundary_read,
    ]
    assert TodoItem.objects.filter(recipient_id=owner.id).count() == 18


def test_calendar_month_cutoff_handles_month_end_and_year_boundary():
    for now, expected in [
        (
            datetime(2026, 5, 31, 12, tzinfo=UTC),
            datetime(2026, 2, 28, 12, tzinfo=UTC),
        ),
        (
            datetime(2026, 1, 31, 12, tzinfo=UTC),
            datetime(2025, 10, 31, 12, tzinfo=UTC),
        ),
    ]:
        with patch("apps.todos.dao.timezone.now", return_value=now):
            assert read_history_cutoff() == expected


def test_approval_title_contains_applicant_and_refresh_preserves_read(people):
    owner, first, *_ = people
    plan_id = int(create(people)["plan"]["id"])
    write.submit(owner, "delivery", plan_id)
    todo = TodoItem.objects.get(recipient_id=first.id, source="approval")
    assert todo.title == f"2026-10 {owner.display_name}的月度计划待审批"
    items.mark_read(first.id, "manager", todo.id)
    TodoItem.objects.filter(id=todo.id).update(title="2026-10 月度计划待审批")
    from apps.approvals.public import pending_todo_entries

    items.reconcile(first.id, "manager", "approval", pending_todo_entries(first.id, "manager"))
    todo.refresh_from_db()
    assert owner.display_name in todo.title and todo.read_at and todo.status == "pending"
