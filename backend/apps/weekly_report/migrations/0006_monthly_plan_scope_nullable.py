from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("weekly_report", "0005_monthly_plan_task_dimension")]
    operations = [
        migrations.AlterField(
            model_name="monthlyplantask", name=field,
            field=models.CharField(max_length=255, blank=True, null=True, default=""),
        )
        for field in ["customer_name", "dimension"]
    ]
