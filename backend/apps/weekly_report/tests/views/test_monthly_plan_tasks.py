from types import SimpleNamespace
from unittest.mock import patch

import pytest
from django.urls import reverse

from apps.accounts.services.auth import AuthenticationError
from apps.weekly_report.services.monthly_plan_tasks import save_monthly_plan_tasks

pytestmark = pytest.mark.django_db


def test_list_monthly_tasks_only_returns_current_user_role(client):
    for employee_id, role in [(101, "delivery_specialist"), (102, "delivery_specialist"),
                              (101, "recruitment")]:
        save_monthly_plan_tasks(
            employee_id=employee_id, role_code=role, month_key="2026-10",
            value=[{"work_task": f"{employee_id}-{role}"}],
        )
    with patch("apps.weekly_report.monthly_plan_task_views.require_report_user",
               return_value=(SimpleNamespace(id=101), "delivery_specialist")):
        response = client.get(
            reverse("weekly_report:monthly-plan-tasks", args=["2026-10"]),
            {"employee_id": "102", "role_code": "recruitment"},
        )
    assert response.status_code == 200
    assert [item["work_task"] for item in response.json()["data"]["items"]] == [
        "101-delivery_specialist"
    ]
    assert response.headers.get("X-Trace-ID")


def test_list_monthly_tasks_returns_empty_array(client):
    with patch("apps.weekly_report.monthly_plan_task_views.require_report_user",
               return_value=(SimpleNamespace(id=101), "delivery_specialist")):
        response = client.get(reverse("weekly_report:monthly-plan-tasks", args=["2026-10"]))
    assert response.status_code == 200
    assert response.json()["data"] == {"items": []}


def test_list_monthly_tasks_requires_authentication(client):
    with patch("apps.weekly_report.monthly_plan_task_views.require_report_user",
               side_effect=AuthenticationError("请登录")):
        response = client.get(reverse("weekly_report:monthly-plan-tasks", args=["2026-10"]))
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "AUTHENTICATION_FAILED"


def test_list_monthly_tasks_rejects_invalid_month(client):
    with patch("apps.weekly_report.monthly_plan_task_views.require_report_user",
               return_value=(SimpleNamespace(id=101), "delivery_specialist")):
        response = client.get(reverse("weekly_report:monthly-plan-tasks", args=["2026-13"]))
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_REQUEST"
