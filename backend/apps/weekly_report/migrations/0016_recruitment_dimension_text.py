from django.db import migrations, models
from django.utils import timezone


def show_all_fields(apps, schema_editor):
    apps.get_model("dictionary", "DictionaryItem").objects.using(
        schema_editor.connection.alias
    ).filter(dict_type="weekly_report_fields_recruitment_v1").update(
        dict_value="1", updated_at=timezone.now()
    )


class Migration(migrations.Migration):
    dependencies = [
        ("weekly_report", "0015_monthly_task_longtext"),
        ("dictionary", "0001_initial"),
    ]
    operations = [
        migrations.AddField(
            model_name="weeklyreportitem", name="dimension_text_id",
            field=models.BigIntegerField(blank=True, null=True),
        ),
        migrations.RunPython(show_all_fields, migrations.RunPython.noop),
    ]
