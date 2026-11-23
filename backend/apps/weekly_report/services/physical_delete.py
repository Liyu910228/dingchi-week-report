"""草稿删除的逻辑关联清理；调用方负责权限和事务。"""

from ..submission_models import ReportSubmission, ReportSubmissionChange


def delete_legacy_parent(submission_id):
    parent = ReportSubmission.objects.filter(id=submission_id, legacy=True).first()
    if parent:
        ReportSubmissionChange.objects.filter(submission_id=parent.id).delete()
        parent.delete()

