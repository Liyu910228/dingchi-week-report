"""共享列表、只读详情、撤销及附件权限回归。"""

from datetime import date, timedelta
from unittest.mock import patch

import pytest

from apps.accounts.dao import list_users
from apps.accounts.models import Role, UserAccount, UserRole
from apps.accounts.report_share_dao import recipients
from apps.accounts.services.auth import create_user, serialize_user, update_user
from apps.accounts.services.report_sharing import set_shared_users
from apps.core.security.asymmetric import get_crypto
from apps.weekly_report.models import MonthlyPlan, WeeklyReport
from apps.weekly_report.services import (
    submission_copy,
    submission_list,
    submission_read,
    submission_write,
)
from apps.weekly_report.services.monthly_attachment_access import authorize_monthly_file
from apps.weekly_report.services.reports import ReportPermissionError, _get_accessible_report
from apps.weekly_report.submission_models import ReportSubmission
from apps.weekly_report.tests.services.test_monthly_plan_workflow import people as people

pytestmark = pytest.mark.django_db


@pytest.fixture
def sharing(people, monkeypatch):
    owner = people[0]
    viewer = UserAccount.objects.create(
        username="shared.viewer",
        employee_no="DC000100",
        display_name="接收人",
        password_ciphertext="test-secret-8",
    )
    UserRole.objects.create(user_id=viewer.id, role_id=Role.objects.get(role_code="delivery").id)
    monkeypatch.setattr(
        "apps.weekly_report.services.reports.get_template_by_code",
        lambda code, **kwargs: {"template_code": code, "fields": [], "items": []},
    )
    return owner, viewer, people[3]


def root(owner, kind, month="2026-10", role="delivery"):
    start = date.fromisoformat(month + "-05")
    parent = ReportSubmission.objects.create(
        employee_id=owner.id,
        kind=kind,
        month_key=month,
        period_start=start if kind == "weekly" else None,
        period_end=start + timedelta(days=6) if kind == "weekly" else None,
        status="draft",
    )
    fields = dict(
        employee_id=owner.id,
        role_code=role,
        month_key=month,
        template_code="delivery_specialist_v1",
        submission_id=parent.id,
        status="draft",
    )
    part = (
        MonthlyPlan.objects.create(**fields, summary="共享目标")
        if kind == "monthly"
        else WeeklyReport.objects.create(
            **fields, period_start=start, period_end=start + timedelta(days=6), as_of_date=start
        )
    )
    return parent, part


@pytest.mark.parametrize("kind", ["monthly", "weekly"])
def test_shared_lists_filter_and_paginate_only_direct_owners(sharing, kind):
    owner, viewer, other = sharing
    parent, _ = root(owner, kind)
    root(owner, kind, "2026-11")
    root(other, kind)
    assert (
        submission_list.list_submissions(viewer, "delivery", kind, {"view": "shared"})["total"] == 0
    )
    set_shared_users(owner.id, [str(viewer.id)])
    data = submission_list.list_submissions(
        viewer, "delivery", kind, {"view": "shared", "page_size": 1}
    )
    assert data["total"] == 2 and data["total_pages"] == 2
    assert len(data["items"]) == 1 and data["items"][0]["employee_id"] == str(owner.id)
    filtered = submission_list.list_submissions(
        viewer, "delivery", kind, {"view": "shared", "month_key": "2026-10", "employee_name": "own"}
    )
    assert [item["id"] for item in filtered["items"]] == [str(parent.id)]
    assert (
        submission_list.list_submissions(
            viewer, "delivery", kind, {"view": "shared", "employee_id": str(other.id)}
        )["total"]
        == 0
    )
    assert (
        submission_list.list_submissions(
            viewer, "delivery", kind, {"view": "shared", "employee_name": "不存在"}
        )["total"]
        == 0
    )
    # A -> B 不允许B反向或传递共享A的数据给C。
    set_shared_users(viewer.id, [str(other.id)])
    assert submission_list.list_submissions(other, "leader", kind, {"view": "shared"})["total"] == 0


@pytest.mark.parametrize("kind", ["monthly", "weekly"])
def test_shared_detail_is_readonly_and_revocation_immediate(sharing, kind):
    owner, viewer, _ = sharing
    parent, part = root(owner, kind)
    set_shared_users(owner.id, [viewer.id])
    result = submission_read.detail(viewer, "delivery", parent.id)
    assert not result["can_edit"] and not result["plan"]["can_create_change"]
    assert result["parts"][0]["id"] == str(part.id)
    for handler in [submission_write.delete, submission_write.submit, submission_copy.copy]:
        with pytest.raises(PermissionError):
            handler(viewer, "delivery", parent.id)
    with pytest.raises(PermissionError):
        submission_write.save(viewer, "delivery", kind, {"revision": 0, "parts": []}, parent.id)
    if kind == "monthly":
        authorize_monthly_file(viewer, "delivery", part.id)
    else:
        assert _get_accessible_report(user=viewer, role_code="delivery", report_id=part.id)
    set_shared_users(owner.id, [])
    with pytest.raises(PermissionError):
        submission_read.detail(viewer, "delivery", parent.id)
    if kind == "monthly":
        with pytest.raises(PermissionError):
            authorize_monthly_file(viewer, "delivery", part.id)
    else:
        with pytest.raises(ReportPermissionError):
            _get_accessible_report(user=viewer, role_code="delivery", report_id=part.id)


def test_user_share_create_update_serialize_and_invalid_input(sharing):
    owner, viewer, _ = sharing
    account = create_user(
        payload={
            "username": "shared.new",
            "display_name": "新增共享",
            "password": get_crypto().encrypt("test-secret-8"),
            "role_codes": ["delivery"],
            "shared_user_ids": [str(viewer.id)],
        }
    )
    assert serialize_user(account)["shared_user_ids"] == [str(viewer.id)]
    assert next(item for item in list_users() if item["id"] == str(account.id))[
        "shared_user_ids"
    ] == [str(viewer.id)]
    update_user(user=account, payload={"display_name": "仍共享"})
    assert recipients(account.id) == [viewer.id]
    for invalid in [[account.id], [viewer.id, viewer.id], [True], ["invalid"], [999999]]:
        with pytest.raises(ValueError):
            update_user(user=account, payload={"shared_user_ids": invalid})
    assert recipients(account.id) == [viewer.id]
    update_user(user=account, payload={"shared_user_ids": []})
    assert recipients(account.id) == []


def test_shared_api_authorizes_before_filters_and_rejects_update(client, sharing):
    owner, viewer, _ = sharing
    parent, _ = root(owner, "monthly")
    set_shared_users(owner.id, [viewer.id])
    with patch(
        "apps.weekly_report.submission_views.require_user", return_value=(viewer, "delivery")
    ):
        result = client.get(
            "/api/v1/report-submissions/monthly/", {"view": "shared", "employee_name": "own"}
        )
        assert result.status_code == 200 and result.json()["data"]["total"] == 1
        assert client.get(f"/api/v1/report-submissions/monthly/{parent.id}/").status_code == 200
        assert client.delete(f"/api/v1/report-submissions/monthly/{parent.id}/").status_code == 403
        set_shared_users(owner.id, [])
        assert client.get(f"/api/v1/report-submissions/monthly/{parent.id}/").status_code == 403
