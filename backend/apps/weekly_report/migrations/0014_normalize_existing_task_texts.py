from django.db import migrations


def forwards(apps, schema_editor):
    Item = apps.get_model("weekly_report", "WeeklyReportItem")
    Text = apps.get_model("weekly_report", "WeeklyTaskText")
    for item in Item.objects.all().iterator(chunk_size=500):
        changes = {}
        for kind, field, ref in (
            ("task", "task_name_snapshot", "task_text_id"),
            ("work", "work_content", "work_content_text_id"),
        ):
            if getattr(item, ref) is not None:
                continue
            text = Text.objects.create(
                report_id=item.report_id,
                content_type=kind,
                content=getattr(item, field),
                source="custom",
            )
            changes[ref] = text.id
            changes[field] = ""
        if changes:
            Item.objects.filter(id=item.id).update(**changes)


def backwards(apps, schema_editor):
    Item = apps.get_model("weekly_report", "WeeklyReportItem")
    Text = apps.get_model("weekly_report", "WeeklyTaskText")
    for item in Item.objects.all().iterator(chunk_size=500):
        changes = {}
        for field, ref in (
            ("task_name_snapshot", "task_text_id"),
            ("work_content", "work_content_text_id"),
        ):
            text = Text.objects.filter(id=getattr(item, ref)).first()
            if text:
                changes[field] = text.content
                changes[ref] = None
        Item.objects.filter(id=item.id).update(**changes)


class Migration(migrations.Migration):
    dependencies = [("weekly_report", "0013_weeklytasktext_weeklyreportitem_task_text_id_and_more")]
    operations = [migrations.RunPython(forwards, backwards)]
