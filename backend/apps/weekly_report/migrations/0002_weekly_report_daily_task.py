import apps.core.services.id_generator
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("weekly_report", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="WeeklyReportDailyTask",
            fields=[
                (
                    "id",
                    models.BigIntegerField(
                        default=apps.core.services.id_generator.generate_primary_id,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("report_id", models.BigIntegerField()),
                ("work_date", models.DateField()),
                ("work_content", models.TextField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "db_table": "weekly_report_daily_task",
                "ordering": ["work_date", "id"],
            },
        ),
        migrations.AddConstraint(
            model_name="weeklyreportdailytask",
            constraint=models.UniqueConstraint(
                fields=("report_id", "work_date"),
                name="uq_weekly_report_daily_task_date",
            ),
        ),
    ]
