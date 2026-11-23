"""职位筛选必须在权限约束内、分页前生效，审批按申请人的职位过滤。"""

from datetime import date, timedelta

import pytest

from apps.accounts.models import Role
from apps.accounts.services.monthly_approvers import set_monthly_approvers
from apps.core.authentication.token import create_access_token
from apps.weekly_report.models import WeeklyReport
from apps.weekly_report.services.monthly_plans import write

from .test_monthly_plan_workflow import people as people
from .test_multi_position import multi as multi
from .test_multi_position import plan_payload

pytestmark = pytest.mark.django_db


def bearer(user, role):
    return "Bearer " + create_access_token(user_id=int(user.id), role_code=role)


def test_position_options_are_public_to_authenticated_users_not_management(multi, client):
    Role.objects.create(role_code="inactive_filter", role_name="停用职位", status="inactive")
    Role.objects.create(role_code="deleted_filter", role_name="已删除职位", status="deleted")
    response = client.get("/api/v1/roles/options/")
    assert response.status_code == 200
    rows = response.json()["data"]["items"]
    assert {"delivery", "sales", "manager", "leader"} <= {row["role_code"] for row in rows}
    assert "inactive_filter" not in {row["role_code"] for row in rows}
    assert "deleted_filter" not in {row["role_code"] for row in rows}
    assert all(set(row) == {"role_code", "role_name"} for row in rows)
    assert client.get("/api/v1/roles/").status_code == 403
    assert client.get("/api/v1/roles/options/", HTTP_AUTHORIZATION="").status_code == 401


def test_monthly_role_filter_for_personal_team_all_and_approval(multi, people):
    owner, client = multi
    set_monthly_approvers(owner.id, [str(people[1].id), str(people[2].id)])
    for role in ["delivery", "sales"]:
        data = write.save(owner, role, plan_payload())
        write.submit(owner, role, int(data["plan"]["id"]))
    write.save(owner, "sales", plan_payload("2026-11"))
    write.save(people[1], "manager", plan_payload())
    url = "/api/v1/monthly-plan-management/"
    own = client.get(url, {"view": "mine", "role_code": "sales", "page_size": 1, "page": 2}).json()[
        "data"
    ]
    assert own["total"] == 2 and own["total_pages"] == 2 and len(own["items"]) == 1
    assert own["items"][0]["role_code"] == "sales"
    assert client.get(url, {"view": "mine", "role_code": "manager"}).json()["data"]["total"] == 0
    assert client.get(url, {"view": "mine", "role_code": "unknown"}).json()["data"]["total"] == 0
    manager = bearer(people[1], "manager")
    team = client.get(
        url, {"view": "members", "role_code": "sales"}, HTTP_AUTHORIZATION=manager
    ).json()["data"]
    assert team["total"] == 2
    approval = client.get(
        url, {"view": "approvals", "role_code": "sales"}, HTTP_AUTHORIZATION=manager
    ).json()["data"]
    assert approval["total"] == 1
    assert approval["approvals"][0]["role_code"] == "sales"
    assert approval["approvals"][0]["can_approve"]
    waiting = client.get(
        url,
        {"view": "approvals", "role_code": "sales"},
        HTTP_AUTHORIZATION=bearer(people[2], "manager"),
    ).json()["data"]
    assert waiting["total"] == 0
    everyone = client.get(
        url,
        {"view": "members", "role_code": "manager"},
        HTTP_AUTHORIZATION=bearer(people[3], "leader"),
    ).json()["data"]
    assert everyone["total"] == 1 and everyone["items"][0]["role_code"] == "manager"
    assert client.get(url, {"role_code": "x" * 65}).status_code == 400


def test_weekly_role_filter_before_pagination_preserves_visibility(multi, people):
    owner, client = multi
    for user, role, start in [
        (owner, "delivery", date(2026, 10, 19)),
        (owner, "sales", date(2026, 10, 19)),
        (owner, "sales", date(2026, 10, 26)),
        (people[1], "manager", date(2026, 10, 19)),
    ]:
        WeeklyReport.objects.create(
            employee_id=user.id,
            role_code=role,
            template_code="delivery_specialist_v1",
            period_start=start,
            period_end=start + timedelta(days=6),
            month_key="2026-10",
            as_of_date=start,
        )
    url = "/api/v1/weekly-reports/"
    own = client.get(url, {"role_code": "sales", "page": 2, "page_size": 1}).json()["data"]
    assert own["total"] == 2 and own["total_pages"] == 2 and len(own["items"]) == 1
    assert own["items"][0]["role_code"] == "sales"
    assert client.get(url, {"role_code": "manager"}).json()["data"]["total"] == 0
    team = client.get(
        url,
        {"employee_scope": "team", "role_code": "sales"},
        HTTP_AUTHORIZATION=bearer(people[1], "manager"),
    ).json()["data"]
    assert team["total"] == 2
    everyone = client.get(
        url, {"role_code": "manager"}, HTTP_AUTHORIZATION=bearer(people[3], "leader")
    ).json()["data"]
    assert everyone["total"] == 1 and everyone["items"][0]["role_code"] == "manager"
    assert client.get(url, {"role_code": "' OR 1=1 --"}).json()["data"]["total"] == 0
    assert client.get(url, {"role_code": "x" * 65}).status_code == 400
