from django.db import migrations, models

import apps.core.security.fields
import apps.core.services.id_generator


class Migration(migrations.Migration):
    dependencies = [
        ("ai_gateway", "0002_alter_aichatattachment_storage_name"),
    ]

    operations = [
        migrations.CreateModel(
            name="AIOCRKey",
            fields=[
                (
                    "id",
                    models.BigIntegerField(
                        default=apps.core.services.id_generator.generate_primary_id,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "provider",
                    models.CharField(
                        choices=[("paddleocr", "PaddleOCR"), ("mineru", "MinerU")],
                        max_length=16,
                    ),
                ),
                ("label", models.CharField(blank=True, default="", max_length=80)),
                ("api_key", apps.core.security.fields.EncryptedPasswordField()),
                ("is_enabled", models.BooleanField(db_index=True, default=True)),
                ("last_used_at", models.DateTimeField(blank=True, null=True)),
                ("last_status", models.CharField(blank=True, default="", max_length=16)),
                ("last_error", models.CharField(blank=True, default="", max_length=300)),
                ("use_count", models.PositiveBigIntegerField(default=0)),
                ("created_by_id", models.BigIntegerField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "db_table": "ai_ocr_key",
                "ordering": ["provider", "created_at", "id"],
            },
        ),
        migrations.AddField(
            model_name="aichatattachment",
            name="extraction_provider",
            field=models.CharField(blank=True, default="", max_length=16),
        ),
        migrations.AddField(
            model_name="aichatattachment",
            name="extraction_key_id",
            field=models.BigIntegerField(blank=True, null=True),
        ),
        migrations.AddIndex(
            model_name="aiocrkey",
            index=models.Index(
                fields=["provider", "is_enabled"], name="idx_ai_ocr_key_enabled"
            ),
        ),
    ]
