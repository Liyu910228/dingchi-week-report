"""AI provider settings and private chat attachments."""

from __future__ import annotations

from django.db import models

from apps.core.models.base import SnowflakeIdModel
from apps.core.security.fields import EncryptedPasswordField


class AIModelConfig(SnowflakeIdModel):
    """Singleton-style provider configuration maintained by system administrators."""

    model = models.CharField(max_length=128)
    vision_model = models.CharField(max_length=128, blank=True, default="")
    base_url = models.CharField(max_length=500, blank=True, default="")
    api_key = EncryptedPasswordField(blank=True, default="")
    is_enabled = models.BooleanField(default=True)
    last_test_status = models.CharField(max_length=16, blank=True, default="")
    last_test_message = models.CharField(max_length=500, blank=True, default="")
    last_tested_at = models.DateTimeField(null=True, blank=True)
    updated_by_id = models.BigIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "ai_model_config"
        ordering = ["-updated_at", "-id"]


class AIOCRKey(SnowflakeIdModel):
    """An encrypted OCR provider credential that can be independently enabled."""

    PROVIDER_PADDLEOCR = "paddleocr"
    PROVIDER_MINERU = "mineru"
    PROVIDER_CHOICES = (
        (PROVIDER_PADDLEOCR, "PaddleOCR"),
        (PROVIDER_MINERU, "MinerU"),
    )

    provider = models.CharField(max_length=16, choices=PROVIDER_CHOICES)
    label = models.CharField(max_length=80, blank=True, default="")
    api_key = EncryptedPasswordField()
    is_enabled = models.BooleanField(default=True, db_index=True)
    last_used_at = models.DateTimeField(null=True, blank=True)
    last_status = models.CharField(max_length=16, blank=True, default="")
    last_error = models.CharField(max_length=300, blank=True, default="")
    use_count = models.PositiveBigIntegerField(default=0)
    created_by_id = models.BigIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "ai_ocr_key"
        ordering = ["provider", "created_at", "id"]
        indexes = [
            models.Index(fields=["provider", "is_enabled"], name="idx_ai_ocr_key_enabled"),
        ]


class AIChatAttachment(SnowflakeIdModel):
    """A user-owned, non-public file that may be referenced by chat messages."""

    uploader_id = models.BigIntegerField(db_index=True)
    original_name = models.CharField(max_length=255)
    storage_name = models.CharField(max_length=255, unique=True)
    mime_type = models.CharField(max_length=128, blank=True, default="")
    file_size = models.BigIntegerField(default=0)
    kind = models.CharField(max_length=16)
    extracted_text = models.TextField(blank=True, default="")
    extraction_provider = models.CharField(max_length=16, blank=True, default="")
    extraction_key_id = models.BigIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "ai_chat_attachment"
        ordering = ["created_at", "id"]
        indexes = [
            models.Index(fields=["uploader_id", "id"], name="idx_ai_attachment_owner"),
        ]
