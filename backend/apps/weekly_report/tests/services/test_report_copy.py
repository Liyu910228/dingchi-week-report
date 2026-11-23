from datetime import date, timedelta
from types import SimpleNamespace

import pytest
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage

from apps.accounts.models import Role
from apps.core.models import Attachment
from apps.weekly_report import dao
from apps.weekly_report.models import (
    MonthlyPlan,
    WeeklyReport,
    WeeklyReportDailyTask,
    WeeklyReportItem,
    WeeklyReportMetric,
    WeeklyTaskText,
)
from apps.weekly_report.services import report_copy, reports

pytestmark = pytest.mark.django_db


@pytest.fixture
def source():
    Role.objects.create(role_code="delivery", role_name="交付", scope="self")
    start = date(2026, 10, 26)
    report = WeeklyReport.objects.create(
        employee_id=42,
        role_code="delivery",
        template_code="delivery_specialist_v1",
        period_start=start,
        period_end=start + timedelta(days=6),
        month_key="2026-10",
        as_of_date=start,
        status="completed",
        summary="本周总结",
    )
    MonthlyPlan.objects.create(
        employee_id=42,
        role_code="delivery",
        month_key="2026-11",
        status="approved",
    )
    reports._save_items(
        report,
        [
            {
                "task_code": str(i),
                "task_group_key": "task",
                "work_content_group_key": "work",
                "task_source": "template",
                "task_template": "新增?人",
                "task_values": ["10"],
                "work_content": "多行内容\n第二行",
                "output_description": f"成果{i}",
                "progress_percent": 50,
                "planned_completion_date": "2026-11-01",
            }
            for i in range(2)
        ],
        [],
        42,
    )
    return report


def copy(source, user=42, role="delivery"):
    return report_copy.copy_report(
        user=SimpleNamespace(id=user), role_code=role, report_id=source.id
    )


def test_copy_preserves_contents_and_sharing_but_all_ids_are_new(source, settings):
    settings.STORAGES = {"default": {"BACKEND": "django.core.files.storage.InMemoryStorage"}}
    original = dao.get_report_items(source.id)
    metric = WeeklyReportMetric.objects.create(
        report_id=source.id,
        item_id=original[0]["id"],
        metric_code="m",
        metric_name_snapshot="指标",
        target_value_decimal=10,
        actual_value_decimal=5,
    )
    daily = WeeklyReportDailyTask.objects.create(
        report_id=source.id,
        work_date=source.period_start,
        work_content="日报内容",
    )
    key = default_storage.save("source/test.txt", ContentFile(b"independent attachment"))
    attachment = Attachment.objects.create(
        attachment_type="weekly_report",
        relation_id=source.id,
        relation_sub_id=original[0]["id"],
        storage_key=key,
        file_name="test.txt",
    )
    result = copy(source)
    target = WeeklyReport.objects.get(id=result["id"])
    assert target.period_start == date(2026, 11, 2)
    assert target.period_end == date(2026, 11, 8)
    assert target.month_key == "2026-11" and target.status != "completed"
    assert target.summary == source.summary
    copied = dao.get_report_items(target.id)
    assert len(copied) == 2
    for old, new in zip(original, copied, strict=True):
        for field in ["id", "task_text_id", "work_content_text_id"]:
            assert old[field] != new[field]
        for field in [
            "task_name_snapshot",
            "work_content",
            "task_source",
            "task_template",
            "task_values",
            "output_description",
            "progress_percent",
            "planned_completion_date",
        ]:
            assert old[field] == new[field]
    assert copied[0]["task_text_id"] == copied[1]["task_text_id"]
    assert copied[0]["work_content_text_id"] == copied[1]["work_content_text_id"]
    new_metric = WeeklyReportMetric.objects.get(report_id=target.id)
    assert new_metric.id != metric.id and new_metric.item_id == copied[0]["id"]
    assert not WeeklyReportDailyTask.objects.filter(report_id=target.id).exists()
    assert WeeklyReportDailyTask.objects.get(id=daily.id).work_content == "日报内容"
    new_file = Attachment.objects.get(relation_id=target.id)
    assert new_file.id != attachment.id and new_file.storage_key != key
    assert new_file.relation_sub_id == copied[0]["id"]
    with default_storage.open(new_file.storage_key) as content:
        assert content.read() == b"independent attachment"
    WeeklyTaskText.objects.filter(id=copied[0]["work_content_text_id"]).update(content="新内容")
    assert dao.get_report_items(source.id)[0]["work_content"] == "多行内容\n第二行"
    default_storage.delete(new_file.storage_key)
    assert default_storage.exists(key)
    with pytest.raises(reports.ReportConflictError, match="^下个周期的周报已存在。$"):
        copy(source)
    assert WeeklyReport.objects.count() == 2


@pytest.mark.parametrize("status", [None, "draft", "pending", "rejected"])
def test_unapproved_target_month_blocks_copy_without_partial_data(source, status):
    if status is None:
        MonthlyPlan.objects.all().delete()
    else:
        MonthlyPlan.objects.update(status=status)
    message = "^下个月度计划不存在。$" if status is None else "审批"
    with pytest.raises(ValueError, match=message):
        copy(source)
    assert WeeklyReport.objects.count() == 1
    assert WeeklyTaskText.objects.count() == 2


@pytest.mark.parametrize("status", ["in_progress", "not_started"])
def test_only_completed_can_copy(source, status):
    source.status = status
    source.save()
    with pytest.raises(reports.ReportError, match="只有已完成"):
        copy(source)


@pytest.mark.parametrize("user,role", [(43, "delivery"), (42, "other")])
def test_cannot_copy_another_owner_or_position(source, user, role):
    with pytest.raises(reports.ReportPermissionError):
        copy(source, user, role)


def test_rollback_when_copying_details_fails(source, monkeypatch):
    def fail(*args):
        raise ValueError("复制失败")

    monkeypatch.setattr(report_copy.dao, "copy_details", fail)
    with pytest.raises(ValueError, match="复制失败"):
        copy(source)
    assert WeeklyReport.objects.count() == 1
    assert WeeklyReportItem.objects.count() == 2


def test_http_copy_contract_and_duplicate_conflict(source, monkeypatch):
    import json

    from django.test import RequestFactory
    from django.urls import resolve

    from apps.weekly_report import views

    monkeypatch.setattr(
        views, "require_report_user", lambda request: (SimpleNamespace(id=42), "delivery")
    )
    request = RequestFactory().post(f"/api/v1/weekly-reports/{source.id}/copy/")
    match = resolve(request.path)
    response = match.func(request, **match.kwargs)
    assert response.status_code == 201
    payload = json.loads(response.content)
    assert isinstance(payload["data"]["id"], str)
    assert payload["data"]["period_start"] == "2026-11-02"
    response = match.func(request, **match.kwargs)
    assert response.status_code == 409


def test_http_unapproved_plan_returns_user_warning(source, monkeypatch):
    import json

    from django.test import RequestFactory

    from apps.weekly_report import views

    MonthlyPlan.objects.update(status="pending")
    monkeypatch.setattr(
        views, "require_report_user", lambda request: (SimpleNamespace(id=42), "delivery")
    )
    response = views.report_copy_view(RequestFactory().post("/"), str(source.id))
    assert response.status_code == 400
    assert "审批" in json.loads(response.content)["error"]["message"]
    assert WeeklyReport.objects.count() == 1


def test_future_copied_report_can_save_with_unchanged_daily_tasks(source, monkeypatch):
    monkeypatch.setattr(report_copy.timezone, "localdate", lambda: date(2026, 10, 16))
    WeeklyReportDailyTask.objects.create(
        report_id=source.id,
        work_date=source.period_start,
        work_content="已复制日报",
    )
    result = copy(source)
    target = WeeklyReport.objects.get(id=result["id"])
    assert target.status == "not_started"
    daily = WeeklyReportDailyTask.objects.create(
        report_id=target.id,
        work_date=target.period_start,
        work_content="原日报",
    )
    updated_at = daily.updated_at
    monkeypatch.setattr(reports, "get_report_detail", lambda **kwargs: {"saved": True})
    monkeypatch.setattr(reports, "complete_todo", lambda **kwargs: None)
    saved = reports.create_or_update_report(
        user=SimpleNamespace(id=42, group_id=None),
        role_code="delivery",
        report_id=target.id,
        payload={
            "period_start": target.period_start.isoformat(),
            "summary": "调整后的总结",
            "items": dao.get_report_items(target.id),
            "attachments": [],
            "daily_tasks": [
                {
                    "id": str(daily.id),
                    "work_date": daily.work_date.isoformat(),
                    "work_content": daily.work_content,
                }
            ],
        },
    )
    assert saved == {"saved": True}
    target.refresh_from_db()
    daily.refresh_from_db()
    assert target.summary == "调整后的总结" and target.status == "not_started"
    assert daily.updated_at == updated_at and daily.work_content == "原日报"


@pytest.mark.parametrize("change", ["edit", "add", "delete"])
def test_future_copied_daily_tasks_still_cannot_be_changed(source, monkeypatch, change):
    monkeypatch.setattr(report_copy.timezone, "localdate", lambda: date(2026, 10, 16))
    WeeklyReportDailyTask.objects.create(
        report_id=source.id,
        work_date=source.period_start,
        work_content="原日报",
    )
    result = copy(source)
    target = WeeklyReport.objects.get(id=result["id"])
    daily = WeeklyReportDailyTask.objects.create(
        report_id=target.id,
        work_date=target.period_start,
        work_content="原日报",
    )
    payload = [
        {
            "id": str(daily.id),
            "work_date": daily.work_date.isoformat(),
            "work_content": daily.work_content,
        }
    ]
    if change == "edit":
        payload[0]["work_content"] = "修改日报"
    elif change == "add":
        payload.append(
            {
                "work_date": (daily.work_date + timedelta(days=1)).isoformat(),
                "work_content": "新增日报",
            }
        )
    else:
        payload = []
    with pytest.raises(reports.ReportError, match="仅进行中"):
        reports._save_daily_tasks(target, payload)
    daily.refresh_from_db()
    assert daily.work_content == "原日报"
    assert WeeklyReportDailyTask.objects.filter(report_id=target.id).count() == 1


@pytest.mark.parametrize("mode", ["success", "conflict", "unapproved", "past"])
def test_edit_report_period_uses_common_validation(source, monkeypatch, mode):
    monkeypatch.setattr(report_copy.timezone, "localdate", lambda: date(2026, 10, 16))
    WeeklyReportDailyTask.objects.create(
        report_id=source.id,
        work_date=source.period_start,
        work_content="日报正文",
    )
    result = copy(source)
    target = WeeklyReport.objects.get(id=result["id"])
    original_start = target.period_start
    daily = WeeklyReportDailyTask.objects.create(
        report_id=target.id,
        work_date=target.period_start,
        work_content="原日报",
    )
    start = date(2026, 11, 9)
    if mode == "conflict":
        WeeklyReport.objects.create(
            employee_id=42,
            role_code="delivery",
            template_code=target.template_code,
            month_key="2026-11",
            period_start=start,
            period_end=start + timedelta(days=6),
            as_of_date=start,
        )
    elif mode == "unapproved":
        start = date(2026, 12, 7)
    elif mode == "past":
        start = date(2026, 10, 5)
    monkeypatch.setattr(reports, "get_report_detail", lambda **kwargs: {"saved": True})
    monkeypatch.setattr(reports, "complete_todo", lambda **kwargs: None)
    payload = {
        "period_start": start.isoformat(),
        "period_end": (start + timedelta(days=6)).isoformat(),
        "items": dao.get_report_items(target.id),
        "attachments": [],
        "daily_tasks": [
            {
                "id": str(daily.id),
                "work_date": start.isoformat(),
                "work_content": daily.work_content,
            }
        ],
    }

    def save():
        return reports.create_or_update_report(
            user=SimpleNamespace(id=42, group_id=None),
            role_code="delivery",
            report_id=target.id,
            payload=payload,
        )

    if mode == "success":
        assert save() == {"saved": True}
    else:
        with pytest.raises(ValueError):
            save()
    target.refresh_from_db()
    daily.refresh_from_db()
    expected = start if mode == "success" else original_start
    assert target.period_start == expected
    assert target.period_end == expected + timedelta(days=6)
    assert target.month_key == expected.strftime("%Y-%m")
    assert daily.work_date == expected and daily.work_content == "原日报"
    assert source.period_start == date(2026, 10, 26)


def test_copied_future_report_saves_with_empty_daily_list(source, monkeypatch):
    monkeypatch.setattr(report_copy.timezone, "localdate", lambda: date(2026, 10, 16))
    original_daily = WeeklyReportDailyTask.objects.create(
        report_id=source.id,
        work_date=source.period_start,
        work_content="本周日报不复制",
    )
    result = copy(source)
    target = WeeklyReport.objects.get(id=result["id"])
    assert not WeeklyReportDailyTask.objects.filter(report_id=target.id).exists()
    monkeypatch.setattr(reports, "get_report_detail", lambda **kwargs: {"saved": True})
    monkeypatch.setattr(reports, "complete_todo", lambda **kwargs: None)
    assert reports.create_or_update_report(
        user=SimpleNamespace(id=42, group_id=None),
        role_code="delivery",
        report_id=target.id,
        payload={
            "period_start": target.period_start.isoformat(),
            "items": dao.get_report_items(target.id),
            "attachments": [],
            "daily_tasks": [],
        },
    ) == {"saved": True}
    assert not WeeklyReportDailyTask.objects.filter(report_id=target.id).exists()
    assert WeeklyReportDailyTask.objects.get(id=original_daily.id).work_content == "本周日报不复制"
