from django.db import migrations


def forwards(apps, schema_editor):
    Submission = apps.get_model("weekly_report", "ReportSubmission")
    alias = schema_editor.connection.alias
    for model_name, kind in [("MonthlyPlan", "monthly"), ("WeeklyReport", "weekly")]:
        Model = apps.get_model("weekly_report", model_name)
        for row in (
            Model.objects.using(alias).filter(submission_id__isnull=True).iterator(chunk_size=500)
        ):
            parent = Submission.objects.using(alias).create(
                kind=kind,
                employee_id=row.employee_id,
                group_id=row.group_id,
                month_key=row.month_key,
                period_start=getattr(row, "period_start", None),
                period_end=getattr(row, "period_end", None),
                status=row.status,
                revision=getattr(row, "revision", 0),
                legacy=True,
            )
            Submission.objects.using(alias).filter(id=parent.id).update(
                created_at=row.created_at, updated_at=row.updated_at
            )
            Model.objects.using(alias).filter(id=row.id).update(submission_id=parent.id)


def backwards(apps, schema_editor):
    # 不删除历史正文或审批；撤回时仅解除新增主单关联。
    alias = schema_editor.connection.alias
    legacy_ids = list(
        apps.get_model("weekly_report", "ReportSubmission")
        .objects.using(alias)
        .filter(legacy=True)
        .values_list("id", flat=True)
    )
    for name in ["MonthlyPlan", "WeeklyReport"]:
        apps.get_model("weekly_report", name).objects.using(alias).filter(
            submission_id__in=legacy_ids
        ).update(submission_id=None)
    apps.get_model("weekly_report", "ReportSubmission").objects.using(alias).filter(
        legacy=True
    ).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("weekly_report", "0020_reportsubmissionchange_monthlyplan_submission_id_and_more")
    ]
    operations = [migrations.RunPython(forwards, backwards)]
