from django.db import models

from apps.core.models.base import SnowflakeIdModel


class TodoItem(SnowflakeIdModel):
    recipient_id = models.BigIntegerField()
    role_code = models.CharField(max_length=64, default="", blank=True)
    source = models.CharField(max_length=64)
    dedupe_key = models.CharField(max_length=192)
    title = models.CharField(max_length=255)
    target_json = models.TextField()
    status = models.CharField(max_length=16, default="pending")
    read_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "todo_item"
        ordering = ["-created_at", "-id"]
        constraints = [
            models.UniqueConstraint(
                fields=["recipient_id", "role_code", "dedupe_key"], name="uq_todo_recipient_key"
            )
        ]
        indexes = [
            models.Index(
                fields=["recipient_id", "role_code", "status", "created_at"],
                name="idx_todo_recipient_status",
            )
        ]
