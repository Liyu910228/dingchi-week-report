from django.db import migrations


def merge_scope(apps, schema_editor):
    model = apps.get_model("weekly_report", "MonthlyPlanTask")
    for task in model.objects.using(schema_editor.connection.alias).exclude(
        dimension__isnull=True
    ).exclude(dimension="").iterator():
        if task.dimension.strip():
            task.scope_name = task.dimension
            task.save(update_fields=["scope_name"], using=schema_editor.connection.alias)


class Migration(migrations.Migration):
    dependencies = [("weekly_report", "0006_monthly_plan_scope_nullable")]
    operations = [
        migrations.RenameField(
            model_name="monthlyplantask", old_name="customer_name", new_name="scope_name",
        ),
        migrations.RunPython(merge_scope, migrations.RunPython.noop),
        migrations.RemoveField(model_name="monthlyplantask", name="dimension"),
    ]
