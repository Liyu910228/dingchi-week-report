from datetime import datetime, timedelta

from apps.weekly_report.services.dashboard_submissions import member_report_summaries


def test_member_submissions_saved_not_submitted_and_latest_per_person():
    moment = datetime(2026, 10, 14, 12)
    rows = [
        {"id": str(i), "employee_id": str(i), "updated_at": moment, "status": "completed"}
        for i in range(1, 16)
    ]
    rows.extend(
        [
            {
                "id": "20",
                "employee_id": "1",
                "updated_at": moment + timedelta(hours=1),
                "status": "in_progress",
            },
            {
                "id": "21",
                "employee_id": "1",
                "updated_at": moment + timedelta(hours=2),
                "status": "completed",
            },
            {
                "id": "22",
                "employee_id": "99",
                "updated_at": moment + timedelta(hours=3),
                "status": "completed",
            },
        ]
    )
    result = member_report_summaries(rows, {str(i) for i in range(1, 17)})
    assert len(result) == 15
    assert result[0]["id"] == "21"
    assert result[0]["status"] == "in_progress"  # 同一人员尚有保存未提交的周报
    assert all(row["status"] == "completed" for row in result[1:])
    assert len({row["employee_id"] for row in result}) == len(result)
    assert "16" not in {row["employee_id"] for row in result}
