from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("weekly_report", "0003_monthly_plan_task")]
    operations = [
        migrations.AddField(
            model_name="monthlyplantask",
            name="customer_name",
            field=models.CharField(max_length=255, blank=True, default=""),
        ),
    ]
