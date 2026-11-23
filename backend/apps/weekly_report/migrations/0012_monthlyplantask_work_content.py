from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("weekly_report", "0011_restore_effective_monthly_plans")]

    operations = [
        migrations.AddField(
            model_name="monthlyplantask",
            name="work_content",
            field=models.TextField(blank=True, default=""),
        ),
    ]
