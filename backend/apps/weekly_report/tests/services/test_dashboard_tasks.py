from copy import deepcopy
from datetime import date
from types import SimpleNamespace

import pytest

from apps.weekly_report.services import reports
from apps.weekly_report.services.dashboard_tasks import (
    group_work_tasks,
    output_distribution,
    task_trend,
)


def row(index, reference="shared", **values):
    return {
        "id": str(index),
        "report_id": "1",
        "employee_id": "1",
        "employee_name": "员工",
        "group_id": "10",
        "group_name": "交付组",
        "role_code": "delivery",
        "task_text_id": reference,
        "task_name_snapshot": "同名任务",
        "customer_name_snapshot": "客户",
        "task_code": f"task-{index}",
        "section_code": "weekly_tasks",
        "progress_percent": 0,
        "completion_rate": 0,
        "on_time_status": "in_progress",
        "output_description": "重复成果标题",
        "planned_completion_date": date(2026, 10, 16),
        "created_at": date(2026, 10, 12),
        **values,
    }


def test_ten_details_average_progress_and_count_completion_without_changing_outputs():
    rows = [
        row(i, progress_percent=100 if i < 4 else 50, completion_rate=80 if i < 4 else 20)
        for i in range(10)
    ]
    before = deepcopy(rows)
    (task,) = group_work_tasks(rows)
    assert task["detail_count"] == 10
    assert task["progress_percent"] == 70
    assert task["completion_rate"] == 44
    assert task["completed_detail_count"] == 4
    assert task["detail_completion_rate"] == 40
    assert task["output_detail_count"] == 10
    assert task["on_time_status"] == "in_progress"
    assert output_distribution(rows) == [{"section_code": "weekly_tasks", "value": 10}]
    assert rows == before


@pytest.mark.parametrize("separation", ["reference", "report", "customer", "legacy"])
def test_independent_identical_names_are_not_merged(separation):
    first, second = row(1), row(2)
    if separation == "reference":
        second["task_text_id"] = "another"
    elif separation == "report":
        second["report_id"] = "2"
    elif separation == "customer":
        second["customer_name_snapshot"] = "另一客户"
    else:
        first["task_text_id"] = second["task_text_id"] = None
    assert len(group_work_tasks([first, second])) == 2


def test_member_and_group_stats_weight_work_tasks_equally_and_count_raw_outputs():
    rows = [row(i) for i in range(10)] + [
        row(20, "independent", progress_percent=100, completion_rate=100)
    ]
    members, groups = reports._build_dashboard_task_stats([], rows)
    for result in [members[0], groups[0]]:
        assert result["task_count"] == 2
        assert result["completed_task_count"] == 1
        assert result["in_progress_task_count"] == 1
        assert result["completion_rate"] == 50
        assert result["progress_percent"] == 50
        assert result["output_task_count"] == 11
    assert members[0]["tasks"][0]["detail_count"] == 10


def test_empty_values_count_as_zero_and_late_completed_details_are_counted():
    rows = [
        row(1, progress_percent=100, completion_rate=None, on_time_status="late"),
        row(2, progress_percent=None, completion_rate=None, on_time_status="overdue"),
    ]
    (task,) = group_work_tasks(rows)
    assert task["progress_percent"] == 50
    assert task["completed_detail_count"] == 1
    assert task["on_time_status"] == "overdue"
    rows[1].update(progress_percent=100, on_time_status="completed")
    members, _ = reports._build_dashboard_task_stats([], rows)
    assert members[0]["completed_task_count"] == 1
    assert members[0]["risk_task_count"] == 0
    assert members[0]["in_progress_task_count"] == 0


def test_trend_uses_each_days_details_then_averages_work_tasks():
    start = date(2026, 10, 12)
    rows = [
        row(1, progress_percent=100, completion_rate=100),
        row(2),
        row(3, "other", progress_percent=100, completion_rate=100),
    ]
    history = [
        {
            "id": "1",
            "report_id": "1",
            "task_code_snapshot": "task-2",
            "record_date": start,
            "progress_percent": 0,
            "completion_rate": 0,
        },
        {
            "id": "2",
            "report_id": "1",
            "task_code_snapshot": "task-2",
            "record_date": date(2026, 10, 13),
            "progress_percent": 100,
            "completion_rate": 100,
        },
    ]
    points = task_trend(rows, history, start)
    assert points[0]["progress"] == 75
    assert points[0]["completion"] == 75
    assert points[1]["progress"] == 100
    assert len(points) == 7


@pytest.mark.parametrize("count", [10, 240])
def test_summary_keeps_raw_output_values_and_reports_complete_logical_counts(monkeypatch, count):
    start = date(2026, 10, 12)
    rows = [
        row(i, progress_percent=100 if i < 4 else 50, completion_rate=80 if i < 4 else 20)
        for i in range(count)
    ]
    header = {
        "id": "1",
        "employee_id": "1",
        "employee_name": "员工",
        "group_id": "10",
        "group_name": "交付组",
        "period_start": start,
        "period_end": date(2026, 10, 18),
        "status": "in_progress",
        "updated_at": start,
        "role_code": "delivery",
    }
    monkeypatch.setattr(reports, "visible_employee_ids", lambda *args: [1])
    monkeypatch.setattr(reports, "_role_scope", lambda *args: "self")
    monkeypatch.setattr(reports.dao, "list_reports", lambda **kwargs: [header])
    monkeypatch.setattr(reports.dao, "get_report_items", lambda *args: deepcopy(rows))
    monkeypatch.setattr(reports.dao, "list_dashboard_members", lambda *args: [header])
    monkeypatch.setattr(reports.dao, "get_report_item_progress_history", lambda *args: [])
    data = reports.dashboard_summary(
        user=SimpleNamespace(id=1), role_code="delivery", period_start=start
    )
    assert data["kpis"]["planned_tasks"] == 1
    assert data["kpis"]["completed_tasks"] == 0
    assert data["kpis"]["completion_rate"] == round((4 * 80 + (count - 4) * 20) / count, 1)
    assert len(data["my_work_tasks"]) == 1
    assert data["my_work_tasks"][0]["completed_detail_count"] == 4
    assert data["team_work_tasks"][0]["progress_percent"] == round(
        (4 * 100 + (count - 4) * 50) / count, 1
    )
    assert len(data["team_output_items"]) == min(200, count)
    assert data["team_output_items"][0]["progress_percent"] == 100
    assert data["team_output_items"][4]["progress_percent"] == 50
    assert data["output_count"] == count
    assert data["team_work_tasks"][0]["detail_count"] == count
    assert data["member_stats"][0]["task_count"] == 1
    assert data["member_stats"][0]["output_task_count"] == count
    assert data["status_distribution"][0]["value"] == 1
