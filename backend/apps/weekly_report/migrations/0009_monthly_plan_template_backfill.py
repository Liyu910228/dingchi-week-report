from django.db import migrations


def backfill_templates(apps, schema_editor):
    role_model = apps.get_model("accounts", "Role")
    plan_model = apps.get_model("weekly_report", "MonthlyPlan")
    alias = schema_editor.connection.alias
    for role in role_model.objects.using(alias).all().iterator():
        plan_model.objects.using(alias).filter(role_code=role.role_code, template_code="").update(
            template_code=role.report_template_code or ""
        )


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0004_usermanager"),
        ("weekly_report", "0008_monthlyplanrevision_monthlyplan_rejection_reason_and_more"),
    ]
    operations = [migrations.RunPython(backfill_templates, migrations.RunPython.noop)]
