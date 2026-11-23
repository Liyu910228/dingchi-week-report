import json
from django.db import migrations


def backfill(apps, schema_editor):
    alias = schema_editor.connection.alias
    roles = apps.get_model("accounts", "Role")
    assignments = apps.get_model("accounts", "UserRole")
    steps = apps.get_model("approvals", "ApprovalStep")
    requests = apps.get_model("approvals", "ApprovalRequest")
    for step in steps.objects.using(alias).filter(approver_role_code="").iterator():
        ids = list(
            assignments.objects.using(alias)
            .filter(user_id=step.approver_id, status="active")
            .order_by("-is_default", "id")
            .values_list("role_id", flat=True)
        )
        available = {
            role.id: role for role in roles.objects.using(alias).filter(id__in=ids, status="active")
        }
        request = requests.objects.using(alias).filter(id=step.approval_id).first()
        template = json.loads(request.snapshot_json).get("template_code", "") if request else ""
        choices = [
            (index, available[value]) for index, value in enumerate(ids) if value in available
        ]
        choices.sort(
            key=lambda item: (
                item[1].scope not in {"team", "all"},
                item[1].report_template_code != template,
                item[1].scope != "team",
                item[0],
            )
        )
        if choices:
            step.approver_role_code = choices[0][1].role_code
            step.save(using=alias, update_fields=["approver_role_code"])


class Migration(migrations.Migration):
    dependencies = [
        ("approvals", "0002_approvalstep_approver_role_code"),
        ("accounts", "0004_usermanager"),
    ]
    operations = [migrations.RunPython(backfill, migrations.RunPython.noop)]
