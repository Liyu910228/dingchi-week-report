from datetime import date, timedelta
from io import StringIO
from types import SimpleNamespace

import pytest
from django.core.management import call_command
from django.db import transaction

from apps.weekly_report import dao
from apps.weekly_report.models import WeeklyReport, WeeklyReportItem, WeeklyTaskText
from apps.weekly_report.services import reports
from apps.weekly_report.services.task_texts import remove_unused_texts

pytestmark = pytest.mark.django_db


def report_for(template="delivery_specialist_v1", employee=42):
    start = date.today() - timedelta(days=date.today().weekday())
    return WeeklyReport.objects.create(
        employee_id=employee,
        role_code="delivery",
        template_code=template,
        period_start=start,
        period_end=start + timedelta(days=6),
        month_key=start.strftime("%Y-%m"),
        as_of_date=date.today(),
    )


@pytest.mark.parametrize(
    "template", ["delivery_specialist_v1", "delivery_assistant_v1", "functional_group_v1"]
)
def test_shared_text_round_trip_updates_once_and_keeps_independent_rows(template):
    report = report_for(template)
    payload = [
        {
            "task_code": str(i),
            "task_group_key": "task-a",
            "work_content_group_key": "work-a",
            "task_name_snapshot": "任务",
            "work_content": "内容",
            "output_description": str(i),
        }
        for i in range(2)
    ]
    reports._save_items(report, payload, [], 42)
    rows = dao.get_report_items(report.id)
    assert rows[0]["task_text_id"] == rows[1]["task_text_id"]
    assert rows[0]["work_content_text_id"] == rows[1]["work_content_text_id"]
    assert WeeklyTaskText.objects.filter(report_id=report.id).count() == 2
    assert list(
        WeeklyReportItem.objects.filter(report_id=report.id).values_list(
            "task_name_snapshot", flat=True
        )
    ) == ["", ""]
    for row in rows:
        row["task_name_snapshot"] = "修改一次"
    WeeklyReportItem.objects.filter(report_id=report.id).delete()
    reports._save_items(report, rows, [], 42)
    remove_unused_texts(report.id)
    rows = dao.get_report_items(report.id)
    assert [row["task_name_snapshot"] for row in rows] == ["修改一次", "修改一次"]
    assert [row["output_description"] for row in rows] == ["0", "1"]


@pytest.mark.parametrize(
    "template",
    [
        "delivery_specialist_v1",
        "delivery_assistant_v1",
        "recruitment_v1",
        "ito_sales_v1",
        "innovation_sales_v1",
        "functional_group_v1",
    ],
)
def test_all_templates_accept_long_and_incomplete_drafts_but_reject_submission(
    monkeypatch, template
):
    report = report_for(template)
    body = "多行长文本\n" * 20000
    reports._save_items(report, [{"task_name_snapshot": body, "work_content": body}], [], 42)
    assert dao.get_report_items(report.id)[0]["task_name_snapshot"] == body.strip()
    monkeypatch.setattr(reports, "_role_scope", lambda role: "self")
    monkeypatch.setattr(
        reports, "_get_template_fields", lambda code: [{"field_code": "customer_name"}]
    )
    with pytest.raises(reports.ReportError) as error:
        reports.submit_report(
            user=SimpleNamespace(id=42), role_code="delivery", report_id=report.id
        )
    assert (
        "输出成果" in str(error.value)
        and "计划完成时间" in str(error.value)
        and "客户" in str(error.value)
    )
    report.refresh_from_db()
    assert report.status != "completed"


@pytest.mark.parametrize(
    "template", ["delivery_specialist_v1", "delivery_assistant_v1", "functional_group_v1"]
)
def test_template_values_persist_and_descriptions_are_immutable(template):
    report = report_for(template)
    reports._save_items(
        report,
        [
            {
                "task_source": "template",
                "task_template": "新增?人，目标？个",
                "task_values": ["10", "20"],
            }
        ],
        [],
        42,
    )
    row = dao.get_report_items(report.id)[0]
    assert row["task_name_snapshot"] == "新增10人，目标20个"
    assert row["task_values"] == ["10", "20"]
    row["task_values"] = ["11", "21"]
    WeeklyReportItem.objects.filter(report_id=report.id).delete()
    reports._save_items(report, [row], [], 42)
    assert dao.get_report_items(report.id)[0]["task_name_snapshot"] == "新增11人，目标21个"
    row["task_template"] = "非法修改?？"
    with transaction.atomic(), pytest.raises(reports.ReportError, match="描述文字"):
        reports._save_items(report, [row], [], 42)


def test_foreign_report_text_reference_is_rejected():
    first = report_for()
    second = report_for(employee=43)
    reports._save_items(first, [{"task_name_snapshot": "私有内容"}], [], 42)
    ref = dao.get_report_items(first.id)[0]["task_text_id"]
    with pytest.raises(reports.ReportError, match="不属于当前周报"):
        reports._save_items(second, [{"task_text_id": str(ref)}], [], 43)


def test_old_text_backfill_preserves_ids_and_timestamps_and_is_repeatable():
    report = report_for()
    item = WeeklyReportItem.objects.create(
        report_id=report.id,
        task_code="old",
        section_code="",
        task_name_snapshot="旧任务",
        work_content="旧内容",
    )
    before = (item.id, item.created_at, item.updated_at)
    call_command("normalize_weekly_task_texts", apply=True, stdout=StringIO())
    call_command("normalize_weekly_task_texts", apply=True, stdout=StringIO())
    item.refresh_from_db()
    assert (item.id, item.created_at, item.updated_at) == before
    assert item.task_name_snapshot == "" and item.work_content == ""
    assert WeeklyTaskText.objects.filter(report_id=report.id).count() == 2
    assert dao.get_report_items(report.id)[0]["task_name_snapshot"] == "旧任务"
