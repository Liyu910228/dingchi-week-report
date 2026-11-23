from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [("accounts", "0002_useraccount_phone")]
    operations = [migrations.RenameField(model_name="useraccount", old_name="is_demo", new_name="is_super")]
