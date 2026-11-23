"""管理员恢复周报状态：权限、整单事务和填写数据保留。"""

from unittest.mock import patch

import pytest
from django.utils import timezone

from apps.accounts.models import Role, UserRole
from apps.core.models.attachment import Attachment
from apps.weekly_report import submission_dao as dao
from apps.weekly_report.models import WeeklyReport, WeeklyReportDailyTask, WeeklyReportItem
from apps.weekly_report.services import reports, submission_read
from apps.weekly_report.services.submission_reopen import reopen
from apps.weekly_report.submission_models import ReportSubmission
from apps.weekly_report.tests.services.test_monthly_plan_workflow import people as people
from apps.weekly_report.tests.services.test_submissions import legacy_week
from apps.weekly_report.tests.services.test_submissions import multi as multi

pytestmark = pytest.mark.django_db


def administrator(multi):
    user = multi[3]
    role = Role.objects.create(role_code="system_admin", role_name="系统管理员", scope="all")
    UserRole.objects.create(user_id=user.id, role_id=role.id)
    return user


def completed_week(multi, legacy=False):
    owner = multi[0]
    first = legacy_week(owner, "delivery", reports._current_period_start())
    second = legacy_week(owner, "sales", first.period_start)
    WeeklyReport.objects.filter(id__in=[first.id, second.id]).update(
        submission_id=first.submission_id, status="completed"
    )
    ReportSubmission.objects.filter(id=first.submission_id).update(
        status="completed", submitted_at=timezone.now(), revision=4, legacy=legacy
    )
    return first.submission_id, first.id, second.id


@pytest.mark.parametrize("legacy", [False, True])
def test_admin_reopens_all_position_parts_and_preserves_every_content(multi, legacy):
    admin = administrator(multi)
    sid, first, second = completed_week(multi, legacy)
    item = WeeklyReportItem.objects.create(
        report_id=first, task_code="task", task_name_snapshot="任务原文",
        work_content="工作内容", output_description="成果", progress_percent=100,
    )
    WeeklyReportDailyTask.objects.create(
        report_id=second, work_date=timezone.localdate(), work_content="日报原文"
    )
    Attachment.objects.create(
        attachment_type="weekly_report", relation_id=first,
        relation_sub_id=item.id, file_name="证明材料.pdf", storage_key="original.pdf"
    )
    models = [WeeklyReportItem, WeeklyReportDailyTask, Attachment]
    before = [list(model.objects.values()) for model in models]
    headers = list(WeeklyReport.objects.filter(id__in=[first, second]).order_by("id").values())
    result = reopen(admin, "system_admin", sid)
    assert result == {"id": str(sid), "status": "in_progress", "revision": 5, "restored": True}
    assert before == [list(model.objects.values()) for model in models]
    after = list(WeeklyReport.objects.filter(id__in=[first, second]).order_by("id").values())
    for old, new in zip(headers, after, strict=True):
        assert new["status"] == "in_progress"
        assert {k: v for k, v in old.items() if k not in {"status", "updated_at"}} == {
            k: v for k, v in new.items() if k not in {"status", "updated_at"}
        }
    assert ReportSubmission.objects.get(id=sid).submitted_at is None
    assert submission_read.detail(multi[0], "delivery", sid)["can_edit"]
    with pytest.raises(ValueError, match="只有已完成"):
        reopen(admin, "system_admin", sid)


def test_reopen_requires_actual_admin_assignment_even_with_forged_role(multi):
    sid, first, _ = completed_week(multi)
    for user in [multi[0], multi[1], multi[3]]:
        with pytest.raises(PermissionError, match="仅系统管理员"):
            reopen(user, "system_admin", sid)
    assert WeeklyReport.objects.get(id=first).status == "completed"
    assert ReportSubmission.objects.get(id=sid).status == "completed"


def test_reopen_failure_rolls_back_all_part_statuses(multi, monkeypatch):
    admin = administrator(multi)
    sid, first, second = completed_week(multi)
    def failed_save(row):
        raise RuntimeError("模拟写入失败")
    monkeypatch.setattr(dao, "save", failed_save)
    with pytest.raises(RuntimeError):
        reopen(admin, "system_admin", sid)
    assert set(WeeklyReport.objects.filter(id__in=[first, second]).values_list(
        "status", flat=True
    )) == {"completed"}
    assert ReportSubmission.objects.get(id=sid).revision == 4


def test_reopen_endpoint_methods_permissions_and_status(multi, client):
    sid, _, _ = completed_week(multi)
    url = f"/api/v1/report-submissions/weekly/{sid}/reopen/"
    with patch(
        "apps.weekly_report.submission_views.require_user",
        return_value=(multi[0], "system_admin"),
    ):
        assert client.post(url).status_code == 403
    admin = administrator(multi)
    with patch(
        "apps.weekly_report.submission_views.require_user", return_value=(admin, "system_admin")
    ):
        assert client.get(url).status_code == 405
        response = client.post(url)
        assert response.status_code == 200 and response.json()["data"]["status"] == "in_progress"
        assert client.post(url).status_code == 400
        assert client.post(f"/api/v1/report-submissions/monthly/{sid}/reopen/").status_code == 405

