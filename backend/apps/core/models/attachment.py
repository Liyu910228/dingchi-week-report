"""通用附件模型。

附件不属于任何单一业务模块，使用业务类型和逻辑关联 ID 绑定业务主记录。
"""

from django.db import models

from .base import SnowflakeIdModel


class Attachment(SnowflakeIdModel):
    """系统通用附件；不建立业务外键。"""

    attachment_type = models.CharField(max_length=64)
    relation_id = models.BigIntegerField()
    relation_sub_id = models.BigIntegerField(null=True, blank=True)
    storage_key = models.CharField(max_length=512, blank=True, default="")
    file_url = models.TextField(blank=True, default="")
    file_name = models.CharField(max_length=255)
    mime_type = models.CharField(max_length=128, blank=True, default="")
    file_size = models.BigIntegerField(default=0)
    description = models.CharField(max_length=500, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "system_attachment"
        ordering = ["created_at", "id"]
        indexes = [
            models.Index(
                fields=["attachment_type", "relation_id", "relation_sub_id"],
                name="idx_system_attachment_relation",
            ),
            models.Index(fields=["attachment_type"], name="idx_system_attachment_type"),
        ]
