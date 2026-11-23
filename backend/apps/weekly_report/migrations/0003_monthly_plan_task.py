import apps.core.services.id_generator
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("weekly_report", "0002_weekly_report_daily_task")]

    operations = [
        migrations.CreateModel(
            name="MonthlyPlanTask",
            fields=[
                ("id", models.BigIntegerField(
                    default=apps.core.services.id_generator.generate_primary_id,
                    editable=False, primary_key=True, serialize=False,
                )),
                ("employee_id", models.BigIntegerField()),
                ("role_code", models.CharField(max_length=64)),
                ("month_key", models.CharField(max_length=7)),
                ("work_task", models.TextField()),
                ("sort_order", models.PositiveIntegerField(default=0)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "db_table": "monthly_plan_task",
                "ordering": ["sort_order", "id"],
                "constraints": [models.UniqueConstraint(
                    fields=("employee_id", "role_code", "month_key", "sort_order"),
                    name="uq_monthly_plan_task_order",
                )],
            },
        ),
    ]
