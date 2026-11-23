from datetime import date, timedelta
from types import SimpleNamespace

import pytest

from apps.weekly_report.models import WeeklyReport, WeeklyReportItem
from apps.weekly_report.services import reports

pytestmark = pytest.mark.django_db


def make_report(template="delivery_specialist_v1"):
    today = date.today()
    start = today - timedelta(days=today.weekday())
    return WeeklyReport.objects.create(
        employee_id=42,
        role_code="delivery",
        template_code=template,
        month_key=start.strftime("%Y-%m"),
        period_start=start,
        period_end=start + timedelta(days=6),
        as_of_date=today,
    )


@pytest.mark.parametrize("template", ["delivery_specialist_v1", "recruitment_v1"])
def test_quick_fill_draft_can_save_but_requires_completion_before_submit(monkeypatch, template):
    monkeypatch.setattr(reports, "_get_template_fields", lambda code: [])
    monkeypatch.setattr(reports, "_role_scope", lambda role: "self")
    report = make_report(template)
    reports._save_items(
        report,
        [
            {
                "task_code": "task_1",
                "task_name_snapshot": "回款目标：？万元",
                "customer_name_snapshot": "客户A",
                "work_content": "主要障碍：？？",
            }
        ],
        [],
        42,
    )
    item = WeeklyReportItem.objects.get(report_id=report.id)
    assert item.output_description == ""
    assert item.planned_completion_date is None
    assert item.owner_id == 42
    user = SimpleNamespace(id=42)
    with pytest.raises(reports.ReportError, match="输出成果"):
        reports.submit_report(user=user, role_code="delivery", report_id=report.id)
    item.output_description = "成果"
    item.save()
    with pytest.raises(reports.ReportError, match="计划完成时间"):
        reports.submit_report(user=user, role_code="delivery", report_id=report.id)
    item.planned_completion_date = report.period_end
    item.save()
    assert reports.submit_report(user=user, role_code="delivery", report_id=report.id)["submitted"]


@pytest.mark.parametrize(
    "template", ["delivery_assistant_v1", "functional_group_v1", "ito_sales_v1"]
)
def test_other_templates_allow_incomplete_drafts(monkeypatch, template):
    monkeypatch.setattr(reports, "_get_template_fields", lambda code: [])
    monkeypatch.setattr(reports, "_role_scope", lambda role: "self")
    report = make_report(template)
    reports._save_items(report, [{"task_name_snapshot": "", "work_content": ""}], [], 42)
    with pytest.raises(reports.ReportError, match="工作任务"):
        reports.submit_report(
            user=SimpleNamespace(id=42), role_code="delivery", report_id=report.id
        )


def test_recruitment_quick_fill_preserves_dimension_order_and_owner(monkeypatch):
    monkeypatch.setattr(reports, "_get_template_fields", lambda code: [{"field_code": "dimension"}])
    report = make_report("recruitment_v1")
    payload = [
        {
            "task_code": f"recruitment_{index}",
            "section_code": dimension,
            "task_name_snapshot": f"工作任务{index}\n第二行",
            "work_content": "工作内容\n第二行",
            "sort_order": index,
        }
        for index, dimension in enumerate(["自定义维度", "需求管理"])
    ]
    reports._save_items(report, payload, [], 42)
    rows = list(WeeklyReportItem.objects.filter(report_id=report.id).order_by("sort_order"))
    assert [row["section_code"] for row in reports.dao.get_report_items(report.id)] == [
        "自定义维度",
        "需求管理",
    ]
    assert all(row.dimension_text_id is not None for row in rows)
    assert [row.sort_order for row in rows] == [0, 1]
    assert all(row.owner_id == 42 and row.task_name_snapshot == "" for row in rows)
    assert all("\n" in row["task_name_snapshot"] for row in reports.dao.get_report_items(report.id))
    payload[0]["section_code"] = " "
    reports._save_items(report, payload, [], 42)
    monkeypatch.setattr(reports, "_role_scope", lambda role: "self")
    with pytest.raises(reports.ReportError, match="维度不能为空"):
        reports.submit_report(
            user=SimpleNamespace(id=42), role_code="delivery", report_id=report.id
        )
