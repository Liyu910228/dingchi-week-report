import json
from django.db import migrations


def backfill(apps, schema_editor):
    alias = schema_editor.connection.alias
    todos = apps.get_model("todos", "TodoItem")
    steps = apps.get_model("approvals", "ApprovalStep")
    for item in todos.objects.using(alias).filter(role_code="").iterator():
        target = json.loads(item.target_json)
        role_code = target.get("role_code", "")
        if item.source == "approval":
            approval_id = target.get("approval_id")
            step = (
                steps.objects.using(alias)
                .filter(approval_id=approval_id, approver_id=item.recipient_id)
                .first()
            )
            role_code = step.approver_role_code if step else ""
        if role_code:
            item.role_code = role_code
            target["role_code"] = role_code
            item.target_json = json.dumps(target, ensure_ascii=False)
            item.save(using=alias, update_fields=["role_code", "target_json"])


class Migration(migrations.Migration):
    dependencies = [
        ("todos", "0002_remove_todoitem_uq_todo_recipient_key_and_more"),
        ("approvals", "0003_backfill_step_roles"),
    ]
    operations = [migrations.RunPython(backfill, migrations.RunPython.noop)]
