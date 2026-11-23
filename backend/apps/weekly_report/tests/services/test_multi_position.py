"""多职位报告聚合、显式填写上下文及逐级审批的HTTP回归。"""

from datetime import timedelta

import pytest
from django.utils import timezone

from apps.accounts.models import Role, UserRole
from apps.accounts.services.monthly_approvers import set_monthly_approvers
from apps.approvals.models import ApprovalStep
from apps.core.authentication.token import create_access_token
from apps.weekly_report.models import MonthlyPlan, WeeklyReport
from apps.weekly_report.services import reports
from apps.weekly_report.services.monthly_plans import write
from apps.weekly_report.tests.services.test_monthly_plan_workflow import people as people

pytestmark = pytest.mark.django_db


@pytest.fixture
def multi(people, client):
    owner = people[0]
    role = Role.objects.create(
        role_code="sales",
        role_name="销售职位",
        scope="self",
        report_template_code="delivery_specialist_v1",
    )
    UserRole.objects.create(user_id=owner.id, role_id=role.id)
    set_monthly_approvers(owner.id, [])
    client.defaults["HTTP_AUTHORIZATION"] = "Bearer " + create_access_token(
        user_id=int(owner.id), role_code="delivery"
    )
    return owner, client


def plan_payload(month="2026-10"):
    return {
        "month_key": month,
        "summary": "目标",
        "tasks": [{"scope_name": "客户", "work_task": "任务"}],
    }


def test_monthly_create_selected_role_list_all_and_edit_record_role(multi):
    owner, client = multi
    write.save(owner, "delivery", plan_payload())
    result = client.post(
        "/api/v1/monthly-plan-management/",
        plan_payload(),
        content_type="application/json",
        HTTP_X_REPORT_ROLE="sales",
    )
    assert result.status_code == 200, result.content
    data = result.json()["data"]
    assert data["plan"]["role_code"] == "sales"
    plan_id = data["plan"]["id"]
    rows = client.get("/api/v1/monthly-plan-management/", {"view": "mine"}).json()["data"]
    assert rows["total"] == 2
    assert {row["role_code"] for row in rows["items"]} == {"delivery", "sales"}
    assert all(row["role_name"] for row in rows["items"])
    paged = client.get(
        "/api/v1/monthly-plan-management/", {"view": "mine", "page": 2, "page_size": 1}
    ).json()["data"]
    assert paged["page"] == 2 and paged["total"] == 2 and len(paged["items"]) == 1
    response = client.patch(
        f"/api/v1/monthly-plan-management/{plan_id}/",
        {**plan_payload(), "summary": "新目标", "revision": data["plan"]["revision"]},
        content_type="application/json",
    )
    assert response.status_code == 200, response.content
    assert response.json()["data"]["plan"]["role_code"] == "sales"
    assert client.post(f"/api/v1/monthly-plan-management/{plan_id}/submit/").status_code == 200
    gate = client.get(
        "/api/v1/monthly-plan-management/gate/2026-10/", HTTP_X_REPORT_ROLE="sales"
    ).json()["data"]
    assert gate["approved"]
    assert not client.get("/api/v1/monthly-plan-management/gate/2026-10/").json()["data"][
        "approved"
    ]


def test_weekly_selected_role_and_existing_record_actions(multi, monkeypatch, people):
    monkeypatch.setattr(
        reports,
        "resolve_role_template",
        lambda role: reports.get_template_by_code("delivery_specialist_v1", role_code=role),
    )
    owner, client = multi
    start = timezone.localdate()
    start -= timedelta(days=start.weekday())
    for role in ["delivery", "sales"]:
        MonthlyPlan.objects.create(
            employee_id=owner.id,
            role_code=role,
            month_key=start.strftime("%Y-%m"),
            status="approved",
            template_code="delivery_specialist_v1",
        )
    payload = {
        "period_start": start.isoformat(),
        "period_end": (start + timedelta(days=6)).isoformat(),
        "items": [],
        "metrics": [],
        "daily_tasks": [],
        "attachments": [],
    }
    for role in ["delivery", "sales"]:
        result = client.post(
            "/api/v1/weekly-reports/",
            payload,
            content_type="application/json",
            HTTP_X_REPORT_ROLE=role,
        )
        assert result.status_code == 201, result.content
    rows = client.get("/api/v1/weekly-reports/").json()["data"]
    assert rows["total"] == 2
    assert {row["role_code"] for row in rows["items"]} == {"delivery", "sales"}
    manager_token = "Bearer " + create_access_token(user_id=int(people[1].id), role_code="manager")
    team = client.get(
        "/api/v1/weekly-reports/", {"employee_scope": "team"}, HTTP_AUTHORIZATION=manager_token
    ).json()["data"]
    assert team["total"] == 2
    assert {row["role_code"] for row in team["items"]} == {"delivery", "sales"}
    report = WeeklyReport.objects.get(employee_id=owner.id, role_code="sales")
    edited = client.patch(
        f"/api/v1/weekly-reports/{report.id}/", payload, content_type="application/json"
    )
    assert edited.status_code == 200, edited.content
    assert edited.json()["data"]["report"]["role_code"] == "sales"
    daily = client.post(
        f"/api/v1/weekly-reports/{report.id}/daily-tasks/",
        {"work_date": start.isoformat(), "work_content": "每日总结"},
        content_type="application/json",
    )
    assert daily.status_code == 201, daily.content


def test_unassigned_header_and_other_users_record_are_rejected(multi, people):
    owner, client = multi
    assert (
        client.post(
            "/api/v1/monthly-plan-management/",
            plan_payload(),
            content_type="application/json",
            HTTP_X_REPORT_ROLE="leader",
        ).status_code
        == 403
    )
    other = write.save(people[1], "manager", plan_payload())
    url = f"/api/v1/monthly-plan-management/{other['plan']['id']}/"
    assert client.get(url).status_code == 403
    assert (
        client.patch(
            url, plan_payload(), content_type="application/json", HTTP_X_REPORT_ROLE="sales"
        ).status_code
        == 403
    )
    UserRole.objects.filter(
        user_id=owner.id, role_id=Role.objects.get(role_code="sales").id
    ).update(status="inactive")
    assert (
        client.get(
            "/api/v1/monthly-plan-management/context/", HTTP_X_REPORT_ROLE="sales"
        ).status_code
        == 403
    )


def test_approval_uses_assigned_step_role_not_token_default(people, client):
    owner, first, second, _ = people
    UserRole.objects.create(user_id=first.id, role_id=Role.objects.get(role_code="leader").id)
    data = write.save(owner, "delivery", plan_payload())
    plan_id = data["plan"]["id"]
    write.submit(owner, "delivery", int(plan_id))
    client.defaults["HTTP_AUTHORIZATION"] = "Bearer " + create_access_token(
        user_id=int(first.id), role_code="leader"
    )
    pending = client.get("/api/v1/monthly-plan-management/", {"view": "approvals"})
    assert pending.status_code == 200, pending.content
    assert pending.json()["data"]["total"] == 1
    assert pending.json()["data"]["approvals"][0]["can_approve"]
    assert (
        client.post(
            f"/api/v1/monthly-plan-management/{plan_id}/decide/",
            {"action": "approve"},
            content_type="application/json",
        ).status_code
        == 200
    )
    assert ApprovalStep.objects.get(approver_id=second.id).status == "pending"
