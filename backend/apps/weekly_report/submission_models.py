"""多职位统一主单；原职位记录和任务ID继续保留。"""

from django.db import models

from apps.core.models.base import SnowflakeIdModel


class ReportSubmission(SnowflakeIdModel):
    merged_into_id = models.BigIntegerField(null=True, blank=True)
    kind = models.CharField(max_length=16)
    employee_id = models.BigIntegerField()
    group_id = models.BigIntegerField(null=True, blank=True)
    month_key = models.CharField(max_length=7)
    period_start = models.DateField(null=True, blank=True)
    period_end = models.DateField(null=True, blank=True)
    active_key = models.CharField(max_length=128, null=True, blank=True, unique=True)
    status = models.CharField(max_length=24, default="draft")
    revision = models.PositiveIntegerField(default=0)
    legacy = models.BooleanField(default=False)
    submitted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "report_submission"
        ordering = ["-month_key", "-updated_at", "-id"]
        indexes = [
            models.Index(fields=["merged_into_id"], name="idx_submission_merged_into"),
            models.Index(
                fields=["employee_id", "kind", "month_key"], name="idx_submission_owner_period"
            )
        ]


class ReportSubmissionChange(SnowflakeIdModel):
    submission_id = models.BigIntegerField(db_index=True)
    base_revision = models.PositiveIntegerField()
    revision = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=24, default="draft")
    base_snapshot_json = models.TextField()
    proposed_snapshot_json = models.TextField()
    rejection_reason = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "report_submission_change"
        ordering = ["-created_at", "-id"]
