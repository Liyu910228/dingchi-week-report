"""旧的就地变更迁入子流程，恢复最后通过的生效数据，保留原审批单和节点。"""
import json

from django.db import migrations

from apps.core.services.id_generator import generate_primary_id


def migrate_changes(apps, schema_editor):
    alias = schema_editor.connection.alias
    plans = apps.get_model("weekly_report", "MonthlyPlan")
    tasks = apps.get_model("weekly_report", "MonthlyPlanTask")
    changes = apps.get_model("weekly_report", "MonthlyPlanChange")
    requests = apps.get_model("approvals", "ApprovalRequest")
    for plan in plans.objects.using(alias).exclude(status__in=["approved", "deleted"]).iterator():
        passed = requests.objects.using(alias).filter(
            business_type="monthly_plan", business_id=plan.id, status="approved"
        ).order_by("-completed_at", "-created_at", "-id").first()
        if not passed:
            continue
        base = json.loads(passed.snapshot_json)
        base_ids = {str(task.get("id")) for task in base["tasks"]}
        existing = list(tasks.objects.using(alias).filter(
            employee_id=plan.employee_id, role_code=plan.role_code, month_key=plan.month_key
        ).order_by("sort_order"))
        proposal = {"summary": plan.summary, "template_code": plan.template_code,
                    "month_key": plan.month_key, "tasks": [
                        {"id": str(task.id) if str(task.id) in base_ids else f"draft-legacy-{task.id}", "scope_name": task.scope_name or "",
                         "work_task": task.work_task, "sort_order": task.sort_order} for task in existing]}
        change = changes.objects.using(alias).create(
            monthly_plan_id=plan.id, base_revision=passed.revision,
            base_snapshot_json=json.dumps(base, ensure_ascii=False),
            proposed_snapshot_json=json.dumps(proposal, ensure_ascii=False),
            revision=plan.revision, status=plan.status, rejection_reason=plan.rejection_reason,
            created_by=plan.employee_id,
        )
        cutoff = passed.completed_at or passed.created_at
        requests.objects.using(alias).filter(business_type="monthly_plan", business_id=plan.id,
                                            created_at__gt=cutoff).exclude(status="approved").update(
            business_type="monthly_plan_change", business_id=change.id)
        tasks.objects.using(alias).filter(id__in=[task.id for task in existing]).delete()
        for index, item in enumerate(base["tasks"]):
            key = str(item.get("id") or "")
            task_id = int(key) if key.isdigit() else generate_primary_id()
            if tasks.objects.using(alias).filter(id=task_id).exists():
                task_id = generate_primary_id()
            tasks.objects.using(alias).create(
                id=task_id, employee_id=plan.employee_id, role_code=plan.role_code,
                month_key=plan.month_key, scope_name=item.get("scope_name") or item.get("customer_name") or item.get("dimension") or None,
                work_task=item["work_task"], sort_order=index,
            )
        plan.summary, plan.status, plan.revision = base["summary"], "approved", passed.revision
        plan.rejection_reason = ""
        plan.save(using=alias, update_fields=["summary", "status", "revision", "rejection_reason"])


class Migration(migrations.Migration):
    dependencies = [("weekly_report", "0010_monthlyplanchange"), ("approvals", "0001_initial")]
    operations = [migrations.RunPython(migrate_changes, migrations.RunPython.noop)]
