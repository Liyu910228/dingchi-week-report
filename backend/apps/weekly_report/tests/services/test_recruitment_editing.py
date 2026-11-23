from copy import deepcopy
from datetime import date
from types import SimpleNamespace

import pytest
from django.db import transaction

from apps.accounts.models import Role
from apps.weekly_report import dao
from apps.weekly_report.models import MonthlyPlan, WeeklyReport, WeeklyReportItem, WeeklyTaskText
from apps.weekly_report.services import report_copy, reports
from apps.weekly_report.services.dashboard_tasks import group_work_tasks
from apps.weekly_report.services.monthly_task_metadata import (
    restore_metadata,
    snapshot_with_metadata,
)
from apps.weekly_report.services.submission_validation import submission_errors

pytestmark = pytest.mark.django_db


@pytest.fixture
def recruitment_report():
    return WeeklyReport.objects.create(
        employee_id=42,
        role_code="recruitment_specialist",
        template_code="recruitment_v1",
        period_start=date(2026, 10, 19),
        period_end=date(2026, 10, 25),
        month_key="2026-10",
        as_of_date=date(2026, 10, 19),
    )


def details():
    return [
        {
            "task_code": str(i),
            "dimension_group_key": "dimension",
            "dimension_source": "template",
            "dimension_template": "招聘？组",
            "dimension_values": ["A"],
            "task_group_key": "task" if i < 3 else "other",
            "task_source": "template",
            "task_template": "入职？人",
            "task_values": ["4"],
            "work_content_group_key": "work" if i < 2 else f"work-{i}",
            "work_content": "共享内容" if i < 2 else f"内容{i}",
            "output_description": f"成果{i}",
            "progress_percent": [20, 80, 50, 100][i],
            "quality_percent": [40, 60, 20, 100][i],
            "planned_completion_date": "2026-10-25",
        }
        for i in range(4)
    ]


def test_recruitment_hierarchy_round_trip_shared_edit_and_dashboard_mean(recruitment_report):
    report = recruitment_report
    reports._save_items(report, details(), [], 42)
    rows = dao.get_report_items(report.id)
    assert len({row["dimension_text_id"] for row in rows}) == 1
    assert len({row["task_text_id"] for row in rows}) == 2
    assert rows[0]["work_content_text_id"] == rows[1]["work_content_text_id"]
    assert rows[2]["work_content_text_id"] != rows[0]["work_content_text_id"]
    assert all(row["section_code"] == "招聘A组" for row in rows)
    assert WeeklyTaskText.objects.filter(report_id=report.id).count() == 6
    tasks = group_work_tasks(rows)
    assert len(tasks) == 2
    assert tasks[0]["progress_percent"] == 50
    assert tasks[0]["completion_rate"] == 45
    assert [row["output_description"] for row in rows] == [f"成果{i}" for i in range(4)]
    for row in rows:
        row["dimension_values"] = ["B"]
        if row["task_text_id"] == rows[0]["task_text_id"]:
            row["task_values"] = ["5"]
        if row["work_content_text_id"] == rows[0]["work_content_text_id"]:
            row["work_content"] = "统一修改内容"
    WeeklyReportItem.objects.filter(report_id=report.id).delete()
    reports._save_items(report, rows, [], 42)
    rows = dao.get_report_items(report.id)
    assert all(row["section_code"] == "招聘B组" for row in rows)
    assert [row["task_name_snapshot"] for row in rows] == ["入职5人"] * 3 + ["入职4人"]
    assert [row["work_content"] for row in rows[:2]] == ["统一修改内容"] * 2


@pytest.mark.parametrize("field", ["task_template", "dimension_template"])
def test_template_descriptions_cannot_be_changed(recruitment_report, field):
    reports._save_items(recruitment_report, details()[:1], [], 42)
    row = dao.get_report_items(recruitment_report.id)[0]
    row[field] = "篡改？"
    with transaction.atomic(), pytest.raises(reports.ReportError, match="描述文字"):
        reports._save_items(recruitment_report, [row], [], 42)


def test_dimension_reference_cannot_cross_reports(recruitment_report):
    reports._save_items(recruitment_report, details()[:1], [], 42)
    row = dao.get_report_items(recruitment_report.id)[0]
    other = WeeklyReport.objects.create(
        employee_id=43,
        role_code="recruitment_specialist",
        template_code="recruitment_v1",
        period_start=date(2026, 10, 19),
        period_end=date(2026, 10, 25),
        month_key="2026-10",
        as_of_date=date(2026, 10, 19),
    )
    with transaction.atomic(), pytest.raises(reports.ReportError, match="不属于"):
        reports._save_items(other, [row], [], 43)


def test_submission_requires_dimension_placeholders(recruitment_report):
    raw = details()[0]
    raw["dimension_values"] = [""]
    reports._save_items(recruitment_report, [raw], [], 42)
    errors = submission_errors(
        recruitment_report, dao.get_report_items(recruitment_report.id), [], {}
    )
    assert any("维度的模板占位值" in error for error in errors)


def test_copy_recruitment_remaps_dimension_task_and_work_ids(recruitment_report, monkeypatch):
    report = recruitment_report
    Role.objects.create(role_code=report.role_code, role_name="招聘", scope="self")
    MonthlyPlan.objects.create(
        employee_id=42, role_code=report.role_code, month_key="2026-10", status="approved"
    )
    monkeypatch.setattr(report_copy.timezone, "localdate", lambda: date(2026, 10, 19))
    reports._save_items(report, details(), [], 42)
    report.status = "completed"
    report.save()
    result = report_copy.copy_report(
        user=SimpleNamespace(id=42), role_code=report.role_code, report_id=report.id
    )
    copied = dao.get_report_items(int(result["id"]))
    original = dao.get_report_items(report.id)
    for old, new in zip(original, copied, strict=True):
        for field in ["id", "dimension_text_id", "task_text_id", "work_content_text_id"]:
            assert old[field] != new[field]
        assert old["section_code"] == new["section_code"]
    assert len({row["dimension_text_id"] for row in copied}) == 1


def test_monthly_dimension_metadata_restores_and_custom_is_not_inferred():
    task = {
        "id": "1",
        "scope_name": "招聘A组",
        "work_task": "入职4人",
        "dimension_source": "template",
        "dimension_template": "招聘？组",
        "dimension_values": ["A"],
        "task_source": "template",
        "task_template": "入职？人",
        "task_values": ["4"],
    }
    import json

    snapshot = snapshot_with_metadata({"tasks": [deepcopy(task)]}, [task])
    restored = restore_metadata(
        [{"id": "1", "scope_name": "招聘A组", "work_task": "入职4人"}], json.dumps(snapshot)
    )
    assert restored[0]["dimension_values"] == ["A"]
    assert restored[0]["task_values"] == ["4"]
    custom = restore_metadata(
        [{"id": "2", "scope_name": "招聘A组", "work_task": "入职4人"}], json.dumps(snapshot)
    )
    assert custom[0].get("dimension_source", "custom") == "custom"
