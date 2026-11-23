from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("weekly_report", "0004_monthly_plan_task_customer")]
    operations = [
        migrations.AddField(
            model_name="monthlyplantask",
            name="dimension",
            field=models.CharField(max_length=255, blank=True, default=""),
        ),
    ]
