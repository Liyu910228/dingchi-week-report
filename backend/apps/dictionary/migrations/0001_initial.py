import apps.core.services.id_generator
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="DictionaryItem",
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
                ("dict_type", models.CharField(max_length=64)),
                ("dict_code", models.CharField(max_length=64)),
                ("dict_name", models.CharField(max_length=128)),
                ("dict_value", models.CharField(blank=True, default="", max_length=255)),
                ("description", models.CharField(blank=True, default="", max_length=255)),
                ("status", models.CharField(default="active", max_length=16)),
                ("sort_order", models.PositiveIntegerField(default=0)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "db_table": "system_dictionary",
                "ordering": ["dict_type", "sort_order", "id"],
            },
        ),
        migrations.AddConstraint(
            model_name="dictionaryitem",
            constraint=models.UniqueConstraint(
                fields=("dict_type", "dict_code"),
                name="uq_system_dictionary_type_code",
            ),
        ),
        migrations.AddIndex(
            model_name="dictionaryitem",
            index=models.Index(
                fields=["dict_type", "status", "sort_order"],
                name="idx_system_dictionary_lookup",
            ),
        ),
    ]
