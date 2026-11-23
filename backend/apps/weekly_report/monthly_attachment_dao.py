"""月度计划附件数据访问，保持逻辑关联。"""

from apps.core.models import Attachment


def locked_files(ids):
    return {str(row.id): row for row in Attachment.objects.select_for_update().filter(id__in=ids)}


def bind_pending(ids, plan_id):
    Attachment.objects.filter(id__in=ids, attachment_type="weekly_report_pending").update(
        attachment_type="monthly_plan", relation_id=plan_id, relation_sub_id=None
    )


def create_file(**values):
    return Attachment.objects.create(**values)
