"""当前周期成员周报摘要：每人一条，按最近更新时间降序。"""


def member_report_summaries(rows, member_ids):
    latest, completed = {}, {}
    for row in rows:
        employee = str(row["employee_id"])
        if employee not in member_ids:
            continue
        completed[employee] = completed.get(employee, True) and row.get("status") == "completed"
        previous = latest.get(employee)
        key = (row["updated_at"], int(row["id"]))
        if previous is None or key > (previous["updated_at"], int(previous["id"])):
            latest[employee] = row
    return [
        {**row, "status": "completed" if completed[str(row["employee_id"])] else "in_progress"}
        for row in sorted(
            latest.values(), key=lambda row: (row["updated_at"], int(row["id"])), reverse=True
        )
    ]
