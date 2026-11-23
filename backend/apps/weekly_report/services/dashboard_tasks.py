"""首页工作任务按共享文本归组；输出成果始终保留明细口径。"""

from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation


def percent(value):
    try:
        number = Decimal(str(value or 0))
        return max(Decimal(0), min(Decimal(100), number)) if number.is_finite() else Decimal(0)
    except (InvalidOperation, ValueError, TypeError):
        return Decimal(0)


def detail_completed(row):
    return (
        row.get("on_time_status") in {"completed", "on_time", "late"}
        or percent(row.get("progress_percent")) >= 100
    )


def detail_risk(row):
    return row.get("on_time_status") in {"overdue", "late"} or bool(
        str(row.get("delay_reason") or "").strip()
    )


def task_key(row, index):
    # 独立同名任务不能合并；旧数据缺少引用时每条明细仍独立统计。
    reference = (
        ("shared", str(row["task_text_id"]))
        if row.get("task_text_id")
        else ("row", str(row.get("id") or index))
    )
    return (
        str(row.get("report_id") or ""),
        str(row.get("employee_id") or ""),
        str(row.get("customer_id") or row.get("customer_name_snapshot") or ""),
        reference,
    )


def mean(rows, field, fallback=None):
    values = [
        percent(row.get(field) if row.get(field) is not None else row.get(fallback)) for row in rows
    ]
    return sum(values, Decimal(0)) / len(values)


def aggregate_task(rows):
    result = dict(rows[0])
    completed = sum(detail_completed(row) for row in rows)
    risks = [row for row in rows if not detail_completed(row) and detail_risk(row)]
    dates = [
        str(row["planned_completion_date"])[:10]
        for row in rows
        if row.get("planned_completion_date")
    ]
    result.update(
        detail_count=len(rows),
        completed_detail_count=completed,
        detail_completion_rate=round(Decimal(completed) * 100 / len(rows), 1),
        output_detail_count=sum(
            bool(str(row.get("output_description") or "").strip()) for row in rows
        ),
        risk_detail_count=sum(detail_risk(row) for row in rows),
        progress_percent=round(mean(rows, "progress_percent"), 1),
        completion_rate=round(mean(rows, "completion_rate", "progress_percent"), 1),
        quality_percent=round(mean(rows, "quality_percent"), 1)
        if any(row.get("quality_percent") is not None for row in rows)
        else None,
        on_time_status="completed"
        if completed == len(rows)
        else "overdue"
        if risks
        else "in_progress",
        delay_reason="；".join(
            dict.fromkeys(str(row.get("delay_reason") or "").strip() for row in risks)
        ),
        planned_completion_date=max(dates) if len(dates) == len(rows) else None,
        planned_detail_count=len(dates),
        work_content="\n\n".join(
            dict.fromkeys(
                str(row.get("work_content") or "").strip()
                for row in rows
                if row.get("work_content")
            )
        ),
        output_description="\n\n".join(
            dict.fromkeys(
                str(row.get("output_description") or "").strip()
                for row in rows
                if row.get("output_description")
            )
        ),
        detail_ids=[str(row.get("id") or "") for row in rows],
        collaborator_names="、".join(
            dict.fromkeys(
                str(row.get("collaborator_names") or "").strip()
                for row in rows
                if row.get("collaborator_names")
            )
        ),
    )
    return result


def group_work_tasks(rows):
    groups = {}
    for index, row in enumerate(rows):
        groups.setdefault(task_key(row, index), []).append(row)
    return [aggregate_task(group) for group in groups.values()]


def day_of(value, fallback):
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value)[:10])
    except ValueError:
        return fallback


def task_trend(items, histories, start):
    by_task = {}
    for row in histories:
        by_task.setdefault(
            (str(row.get("report_id") or ""), str(row.get("task_code_snapshot") or "")), []
        ).append(row)
    for rows in by_task.values():
        rows.sort(
            key=lambda row: (
                day_of(row.get("record_date"), start),
                str(row.get("created_at") or ""),
                int(row.get("id") or 0),
            )
        )
    points = []
    for index in range(7):
        day = start + timedelta(days=index)
        visible = []
        for item in items:
            rows = by_task.get(
                (str(item.get("report_id") or ""), str(item.get("task_code") or "")), []
            )
            latest = next(
                (row for row in reversed(rows) if day_of(row.get("record_date"), start) <= day),
                None,
            )
            if latest:
                visible.append(
                    {
                        **item,
                        **{
                            field: latest.get(field)
                            for field in (
                                "progress_percent",
                                "quality_percent",
                                "completion_rate",
                                "on_time_status",
                            )
                        },
                    }
                )
            elif (
                not rows and day_of(item.get("created_at") or item.get("updated_at"), start) <= day
            ):
                visible.append(item)
        grouped = group_work_tasks(visible)
        points.append(
            {
                "date": day.isoformat(),
                "label": f"周{['一', '二', '三', '四', '五', '六', '日'][index]}",
                "progress": float(round(mean(grouped, "progress_percent"), 1)) if grouped else 0,
                "completion": float(round(mean(grouped, "completion_rate", "progress_percent"), 1))
                if grouped
                else 0,
            }
        )
    return points


def output_distribution(rows):
    counts = {}
    for row in rows:
        if str(row.get("output_description") or "").strip():
            key = row.get("section_code") or "other"
            counts[key] = counts.get(key, 0) + 1
    return [{"section_code": key, "value": value} for key, value in counts.items()]
