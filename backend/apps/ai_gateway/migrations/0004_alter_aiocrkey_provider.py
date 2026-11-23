from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("ai_gateway", "0003_aiocrkey_and_attachment_extraction"),
    ]

    operations = [
        migrations.AlterField(
            model_name="aiocrkey",
            name="provider",
            field=models.CharField(
                choices=[("paddleocr", "PaddleOCR"), ("mineru", "MinerU"), ("baidu", "百度 OCR")],
                max_length=16,
            ),
        ),
    ]
