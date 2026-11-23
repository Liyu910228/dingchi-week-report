from datetime import date
from io import StringIO

import pytest
from django.core.management import call_command
from django.db import transaction

from apps.accounts.models import Role
from apps.dictionary.models import DictionaryItem
from apps.weekly_report import dao
from apps.weekly_report.models import WeeklyReport, WeeklyReportItem, WeeklyTaskText
from apps.weekly_report.services import reports
from apps.weekly_report.services.dashboard_tasks import group_work_tasks
from apps.weekly_report.services.monthly_plan_tasks import validate_report_monthly_data
from apps.weekly_report.templates import get_default_template

pytestmark = pytest.mark.django_db


def report():
    return WeeklyReport.objects.create(
        employee_id=42,
        role_code="human_resources",
        template_code="human_resources_v1",
        period_start=date(2026, 10, 19),
        period_end=date(2026, 10, 25),
        month_key="2026-10",
        as_of_date=date(2026, 10, 19),
    )


def details():
    return [
        {
            "task_code": f"hr-{i}",
            "dimension_group_key": "module",
            "dimension_source": "template",
            "dimension_template": "人力资源管理",
            "dimension_values": [],
            "task_group_key": "task",
            "task_source": "template",
            "task_template": "事项？",
            "task_values": ["1"],
            "work_content_group_key": f"work-{i}",
            "work_content": f"工作内容{i}",
            "output_description": f"输出成果{i}",
            "progress_percent": progress,
            "quality_percent": None,
            "planned_completion_date": "2026-10-25",
            "sort_order": i,
        }
        for i, progress in enumerate([20, 80])
    ]


def test_human_resources_fields_are_independent_and_excel_ordered():
    template = get_default_template("human_resources_v1", role_code="custom_hr")
    assert template["template_name"] == "人资周报"
    assert [field["field_code"] for field in template["fields"]] == [
        "dimension",
        "task_name",
        "work_content",
        "output_description",
        "planned_completion_date",
        "progress_text",
        "progress_percent",
        "delay_reason",
        "on_time_status",
        "actual_completion_date",
        "owner_name",
        "collaborator_names",
        "document_links",
    ]
    assert [field["label"] for field in template["fields"][:2]] == ["模块", "工作事项"]
    assert all(field["default_visible"] for field in template["fields"])
    assert len(template["sections"]) == 5
    assert len(template["tasks"]) == 13
    assert template["metrics"] == []
    template["fields"][0]["label"] = "不能污染定义"
    assert get_default_template("human_resources_v1")["fields"][0]["label"] == "模块"


def test_human_resources_registration_is_idempotent_and_does_not_bind_roles():
    role = Role.objects.create(role_code="hr_custom", role_name="人资专员")
    call_command("register_human_resources_template", stdout=StringIO())
    call_command("register_human_resources_template", stdout=StringIO())
    assert (
        DictionaryItem.objects.filter(
            dict_type="report_template", dict_code="human_resources_v1"
        ).count()
        == 1
    )
    assert (
        DictionaryItem.objects.filter(dict_type="weekly_report_fields_human_resources_v1").count()
        == 13
    )
    role.refresh_from_db()
    assert role.report_template_code == ""
    registered = reports.get_template_by_code("human_resources_v1")
    assert registered["fields"][0]["label"] == "模块"
    assert len(registered["tasks"]) == 13
    assert len(registered["sections"]) == 5


def test_human_resources_shared_text_roundtrip_and_statistics():
    saved_report = report()
    reports._save_items(saved_report, details(), [], 42)
    rows = dao.get_report_items(saved_report.id)
    assert rows[0]["dimension_text_id"] == rows[1]["dimension_text_id"]
    assert rows[0]["task_text_id"] == rows[1]["task_text_id"]
    assert rows[0]["work_content_text_id"] != rows[1]["work_content_text_id"]
    assert all(row["section_code"] == "人力资源管理" for row in rows)
    assert [row["output_description"] for row in rows] == ["输出成果0", "输出成果1"]
    assert [row["progress_percent"] for row in rows] == [20, 80]
    tasks = group_work_tasks(rows)
    assert len(tasks) == 1
    assert tasks[0]["progress_percent"] == 50
    assert tasks[0]["completion_rate"] == 50
    for row in rows:
        row["task_values"] = ["2"]
    rows[1]["work_content"] = "独立改动"
    WeeklyReportItem.objects.filter(report_id=saved_report.id).delete()
    reports._save_items(saved_report, rows, [], 42)
    saved = dao.get_report_items(saved_report.id)
    assert [row["task_name_snapshot"] for row in saved] == ["事项2", "事项2"]
    assert [row["work_content"] for row in saved] == ["工作内容0", "独立改动"]
    assert WeeklyTaskText.objects.filter(report_id=saved_report.id).count() == 4


@pytest.mark.parametrize("field", ["dimension_template", "task_template"])
def test_human_resources_template_descriptions_are_immutable(field):
    saved_report = report()
    reports._save_items(saved_report, details(), [], 42)
    row = dao.get_report_items(saved_report.id)[0]
    row[field] = "篡改" if field == "dimension_template" else "篡改？"
    with transaction.atomic(), pytest.raises(reports.ReportError, match="描述文字"):
        reports._save_items(saved_report, [row], [], 42)


def test_human_resources_monthly_module_is_required():
    with pytest.raises(ValueError, match="模块"):
        validate_report_monthly_data("人资目标", [{"work_task": "人资事项"}], "human_resources_v1")
    validate_report_monthly_data(
        "人资目标",
        [{"scope_name": "人力资源管理", "work_task": "人资事项", "work_content": "内容"}],
        "human_resources_v1",
    )


def test_human_resources_drafts_can_be_incomplete_but_submission_requires_fields():
    from apps.weekly_report.services.submission_validation import submission_errors

    saved_report = report()
    reports._save_items(saved_report, [{"task_code": "blank", "work_content": ""}], [], 42)
    template = get_default_template("human_resources_v1")
    errors = submission_errors(
        saved_report, dao.get_report_items(saved_report.id), template["fields"], template
    )
    assert any("模块不能为空" in error for error in errors)
    assert any("工作事项不能为空" in error for error in errors)
    assert any("计划完成时间不能为空" in error for error in errors)
    WeeklyReportItem.objects.filter(report_id=saved_report.id).delete()
    reports._save_items(saved_report, details(), [], 42)
    assert (
        submission_errors(
            saved_report, dao.get_report_items(saved_report.id), template["fields"], template
        )
        == []
    )
