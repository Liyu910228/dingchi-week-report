"""月度只读聚合的权限、跨月、旧多职位和分页回归。"""

from datetime import date

import pytest

from apps.weekly_report.services import monthly_overview as service
from apps.weekly_report.submission_models import ReportSubmission
from apps.weekly_report.tests.services.test_monthly_plan_workflow import people as people
from apps.weekly_report.tests.services.test_submissions import legacy_week
from apps.weekly_report.tests.services.test_submissions import multi as multi

pytestmark = pytest.mark.django_db


def test_month_groups_and_all_positions_submitted(multi):
    owner, _, _, outsider = multi
    first = legacy_week(owner, "delivery", date(2026, 11, 30))
    second = legacy_week(owner, "sales", date(2026, 11, 30))
    second.status = "completed"
    second.save()
    legacy_week(owner, "delivery", date(2026, 10, 26))
    result = service.list_months(owner, "delivery", {"page_size": "1"})
    assert result["total"] == 2 and result["total_pages"] == 2
    month = result["items"][0]
    assert month["month_key"] == "2026-11"
    assert month["week_count"] == 1 and month["completed_count"] == 0
    assert "销售" in month["role_name"]
    first.status = "completed"
    first.save()
    assert service.list_months(owner, "delivery", {})["items"][0]["completed_count"] == 1
    assert service.list_months(outsider, "leader", {"view": "mine"})["total"] == 0


def test_detail_preserves_saved_positions_and_cross_month_week_without_writes(multi):
    owner, _, _, outsider = multi
    legacy_week(owner, "delivery", date(2026, 11, 30))
    legacy_week(owner, "sales", date(2026, 11, 30))
    legacy_week(owner, "delivery", date(2026, 11, 2))
    before = list(ReportSubmission.objects.values())
    detail = service.detail(owner, "delivery", owner.id, "2026-11")
    assert len(detail["weeks"]) == 2
    assert detail["weeks"][1]["plan"]["period_end"] == "2026-12-06"
    assert len(detail["weeks"][1]["sources"]) == 2
    assert len(detail["weeks"][0]["parts"]) == 1
    assert {part["role_code"] for part in detail["monthly_parts"]} == {"delivery", "sales"}
    assert not any(part["monthly_approved"] for part in detail["monthly_parts"])
    assert list(ReportSubmission.objects.values()) == before
    with pytest.raises(LookupError):
        service.detail(outsider, "delivery", owner.id, "2026-11")


@pytest.mark.parametrize(
    "filters", [{"page": "0"}, {"page_size": "101"}, {"month_key": "bad"}, {"view": "invalid"}]
)
def test_invalid_filters(multi, filters):
    with pytest.raises(ValueError):
        service.list_months(multi[0], "delivery", filters)


def test_approved_month_plan_and_endpoint_contract(multi, client, monkeypatch):
    from apps.weekly_report.models import MonthlyPlan

    owner = multi[0]
    legacy_week(owner, "delivery", date(2026, 11, 2))
    MonthlyPlan.objects.create(
        employee_id=owner.id,
        role_code="delivery",
        month_key="2026-11",
        template_code="delivery_specialist_v1",
        status="approved",
        summary="已生效目标",
    )
    detail = service.detail(owner, "delivery", owner.id, "2026-11")
    assert detail["monthly_parts"][0]["monthly_approved"]
    assert detail["monthly_parts"][0]["payload"]["summary"] == "已生效目标"
    path = "/api/v1/monthly-weekly-reports/"
    assert client.get(path).status_code == 401
    monkeypatch.setattr(
        "apps.weekly_report.submission_views.require_user", lambda request: (owner, "delivery")
    )
    response = client.get(path)
    assert response.status_code == 200
    assert response.json()["data"]["items"][0]["employee_id"] == str(owner.id)
    assert response.headers.get("X-Trace-ID")
    assert client.get(f"{path}{owner.id}/2026-11/").status_code == 200
    assert client.get(path, {"page": "bad"}).status_code == 400
    assert client.get(f"{path}{owner.id}/2026-12/").status_code == 404


def test_default_scope_includes_own_team_or_all_without_exceeding_permissions(multi):
    owner, manager, _, leader = multi
    for user, code in [(owner, "delivery"), (manager, "manager"), (leader, "leader")]:
        legacy_week(user, code, date(2026, 11, 2))
    own = service.list_months(owner, "delivery", {})
    assert {item["employee_id"] for item in own["items"]} == {str(owner.id)}
    team = service.list_months(manager, "manager", {})
    assert {item["employee_id"] for item in team["items"]} == {str(owner.id), str(manager.id)}
    everyone = service.list_months(leader, "leader", {})
    assert everyone["total"] == 3
    assert service.list_months(manager, "manager", {"view": "mine"})["total"] == 1
    assert service.list_months(owner, "delivery", {"employee_id": str(manager.id)})["total"] == 0
    assert service.detail(manager, "manager", owner.id, "2026-11")["employee_id"] == str(owner.id)
