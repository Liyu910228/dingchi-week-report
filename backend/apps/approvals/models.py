from django.db import models

from apps.core.models.base import SnowflakeIdModel


class ApprovalRequest(SnowflakeIdModel):
    business_type = models.CharField(max_length=64)
    business_id = models.BigIntegerField()
    applicant_id = models.BigIntegerField()
    revision = models.PositiveIntegerField()
    status = models.CharField(max_length=16, default="pending")
    current_step = models.PositiveIntegerField(default=0)
    snapshot_json = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "business_approval"
        indexes = [
            models.Index(fields=["business_type", "business_id"], name="idx_approval_business")
        ]


class ApprovalStep(SnowflakeIdModel):
    approval_id = models.BigIntegerField()
    approver_id = models.BigIntegerField()
    approver_name = models.CharField(max_length=128)
    approver_role_code = models.CharField(max_length=64, default="", blank=True)
    sort_order = models.PositiveIntegerField()
    status = models.CharField(max_length=16, default="waiting")
    reason = models.TextField(blank=True, default="")
    acted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "business_approval_step"
        constraints = [
            models.UniqueConstraint(
                fields=["approval_id", "sort_order"], name="uq_approval_step_order"
            )
        ]
