from django.db import migrations, models

import apps.core.security.fields
import apps.core.services.id_generator


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="AIModelConfig",
            fields=[
                ("id", models.BigIntegerField(default=apps.core.services.id_generator.generate_primary_id, editable=False, primary_key=True, serialize=False)),
                ("model", models.CharField(max_length=128)),
                ("vision_model", models.CharField(blank=True, default="", max_length=128)),
                ("base_url", models.CharField(blank=True, default="", max_length=500)),
                ("api_key", apps.core.security.fields.EncryptedPasswordField(blank=True, default="")),
                ("is_enabled", models.BooleanField(default=True)),
                ("last_test_status", models.CharField(blank=True, default="", max_length=16)),
                ("last_test_message", models.CharField(blank=True, default="", max_length=500)),
                ("last_tested_at", models.DateTimeField(blank=True, null=True)),
                ("updated_by_id", models.BigIntegerField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"db_table": "ai_model_config", "ordering": ["-updated_at", "-id"]},
        ),
        migrations.CreateModel(
            name="AIChatAttachment",
            fields=[
                ("id", models.BigIntegerField(default=apps.core.services.id_generator.generate_primary_id, editable=False, primary_key=True, serialize=False)),
                ("uploader_id", models.BigIntegerField(db_index=True)),
                ("original_name", models.CharField(max_length=255)),
                ("storage_name", models.CharField(max_length=512, unique=True)),
                ("mime_type", models.CharField(blank=True, default="", max_length=128)),
                ("file_size", models.BigIntegerField(default=0)),
                ("kind", models.CharField(max_length=16)),
                ("extracted_text", models.TextField(blank=True, default="")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "db_table": "ai_chat_attachment",
                "ordering": ["created_at", "id"],
                "indexes": [models.Index(fields=["uploader_id", "id"], name="idx_ai_attachment_owner")],
            },
        ),
    ]
