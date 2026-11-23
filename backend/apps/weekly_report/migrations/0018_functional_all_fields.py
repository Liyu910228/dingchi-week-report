from django.db import migrations
from django.utils import timezone


def show_all_fields(apps, schema_editor):
    apps.get_model("dictionary", "DictionaryItem").objects.using(
        schema_editor.connection.alias
    ).filter(dict_type="weekly_report_fields_functional_group_v1").update(
        dict_value="1", updated_at=timezone.now()
    )


class Migration(migrations.Migration):
    dependencies = [("weekly_report", "0017_sales_customer_text")]
    operations = [migrations.RunPython(show_all_fields, migrations.RunPython.noop)]
