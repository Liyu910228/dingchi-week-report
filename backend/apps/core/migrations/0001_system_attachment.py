from django.db import migrations, models

import apps.core.services.id_generator


class Migration(migrations.Migration):
    """新增系统级通用附件表；项目启动不会自动执行本迁移。"""

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Attachment",
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
                ("attachment_type", models.CharField(max_length=64)),
                ("relation_id", models.BigIntegerField()),
                ("relation_sub_id", models.BigIntegerField(blank=True, null=True)),
                ("storage_key", models.CharField(blank=True, default="", max_length=512)),
                ("file_url", models.TextField(blank=True, default="")),
                ("file_name", models.CharField(max_length=255)),
                ("mime_type", models.CharField(blank=True, default="", max_length=128)),
                ("file_size", models.BigIntegerField(default=0)),
                ("description", models.CharField(blank=True, default="", max_length=500)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "db_table": "system_attachment",
                "ordering": ["created_at", "id"],
                "indexes": [
                    models.Index(
                        fields=["attachment_type", "relation_id", "relation_sub_id"],
                        name="idx_system_attachment_relation",
                    ),
                    models.Index(
                        fields=["attachment_type"],
                        name="idx_system_attachment_type",
                    ),
                ],
            },
        ),
    ]
