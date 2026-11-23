from django.db import migrations


def widen_task_text(apps, schema_editor):
    if schema_editor.connection.vendor == "mysql":
        schema_editor.execute(
            "ALTER TABLE monthly_plan_task MODIFY COLUMN work_task LONGTEXT NOT NULL"
        )


class Migration(migrations.Migration):
    dependencies = [("weekly_report", "0014_normalize_existing_task_texts")]
    operations = [migrations.RunPython(widen_task_text, migrations.RunPython.noop)]
