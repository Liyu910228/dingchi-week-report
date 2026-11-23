from datetime import date
from types import SimpleNamespace

import pytest

from apps.accounts.models import Role
from apps.weekly_report import dao
from apps.weekly_report.models import MonthlyPlan, WeeklyReport, WeeklyTaskText
from apps.weekly_report.services import report_copy, reports
from apps.weekly_report.services.dashboard_tasks import group_work_tasks

pytestmark = pytest.mark.django_db


def test_functional_shared_rows_have_no_customer_or_dimension_and_average_by_task(monkeypatch):
    report = WeeklyReport.objects.create(
        employee_id=42,
        role_code="functional_group",
        template_code="functional_group_v1",
        period_start=date(2026, 10, 19),
        period_end=date(2026, 10, 25),
        month_key="2026-10",
        as_of_date=date(2026, 10, 19),
    )
    raw = [
        {
            "task_code": str(index),
            "task_source": "template",
            "task_template": "完成？项",
            "task_values": ["10"],
            "task_group_key": "first" if index < 3 else "second",
            "work_content_group_key": "work" if index < 2 else f"work-{index}",
            "work_content": "主要内容" if index < 2 else f"内容{index}",
            "output_description": f"成果{index}",
            "progress_percent": progress,
            "planned_completion_date": "2026-10-25",
        }
        for index, progress in enumerate([20, 80, 50, 100])
    ]
    reports._save_items(report, raw, [], 42)
    rows = dao.get_report_items(report.id)
    assert len({row["task_text_id"] for row in rows}) == 2
    assert rows[0]["work_content_text_id"] == rows[1]["work_content_text_id"]
    assert rows[2]["work_content_text_id"] != rows[0]["work_content_text_id"]
    assert all(
        not row["customer_name_snapshot"]
        and row["customer_text_id"] is None
        and row["dimension_text_id"] is None
        for row in rows
    )
    assert set(
        WeeklyTaskText.objects.filter(report_id=report.id).values_list("content_type", flat=True)
    ) == {"task", "work"}
    tasks = group_work_tasks(rows)
    assert len(tasks) == 2 and tasks[0]["detail_count"] == 3
    assert tasks[0]["progress_percent"] == tasks[0]["completion_rate"] == 50
    assert tasks[1]["progress_percent"] == 100
    assert [row["output_description"] for row in rows] == [f"成果{i}" for i in range(4)]
    Role.objects.create(role_code=report.role_code, role_name="职能", scope="self")
    MonthlyPlan.objects.create(
        employee_id=42, role_code=report.role_code, month_key="2026-10", status="approved"
    )
    monkeypatch.setattr(report_copy.timezone, "localdate", lambda: date(2026, 10, 19))
    report.status = "completed"
    report.save()
    result = report_copy.copy_report(
        user=SimpleNamespace(id=42), role_code=report.role_code, report_id=report.id
    )
    copied = dao.get_report_items(int(result["id"]))
    assert len({row["task_text_id"] for row in copied}) == 2
    for old, new in zip(rows, copied, strict=True):
        assert old["id"] != new["id"] and old["task_text_id"] != new["task_text_id"]
        assert old["work_content_text_id"] != new["work_content_text_id"]
        assert old["task_name_snapshot"] == new["task_name_snapshot"]
