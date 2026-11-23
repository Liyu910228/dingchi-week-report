"""周报深拷贝的数据读写；调用方提供事务边界。"""

from apps.core.models import Attachment

from .models import (
    WeeklyReport,
    WeeklyReportItem,
    WeeklyReportMetric,
    WeeklyTaskText,
)


def find_report(report_id):
    return WeeklyReport.objects.select_for_update().filter(id=report_id).first()


def target_exists(source, start):
    return WeeklyReport.objects.filter(
        employee_id=source.employee_id,
        role_code=source.role_code,
        period_start=start,
    ).exists()


def rows(model, report_id):
    return list(model.objects.filter(report_id=report_id))


def attachments(report_id):
    return list(Attachment.objects.filter(attachment_type="weekly_report", relation_id=report_id))


def duplicate(row, **overrides):
    values = {
        field.attname: getattr(row, field.attname)
        for field in row._meta.concrete_fields
        if not field.primary_key and field.name not in {"created_at", "updated_at"}
    }
    values.update(overrides)
    return type(row).objects.create(**values)


def copy_details(source, target):
    text_map = {
        row.id: duplicate(row, report_id=target.id).id for row in rows(WeeklyTaskText, source.id)
    }
    item_map = {}
    for row in rows(WeeklyReportItem, source.id):
        copied = duplicate(
            row,
            report_id=target.id,
            customer_text_id=text_map.get(row.customer_text_id),
            dimension_text_id=text_map.get(row.dimension_text_id),
            task_text_id=text_map.get(row.task_text_id),
            work_content_text_id=text_map.get(row.work_content_text_id),
        )
        item_map[row.id] = copied.id
    for row in rows(WeeklyReportMetric, source.id):
        duplicate(row, report_id=target.id, item_id=item_map.get(row.item_id))
    return item_map
