from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("ai_gateway", "0001_initial")]

    operations = [
        migrations.AlterField(
            model_name="aichatattachment",
            name="storage_name",
            field=models.CharField(max_length=255, unique=True),
        ),
    ]
