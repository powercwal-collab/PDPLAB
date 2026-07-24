from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("diagnosis", "0018_pdp_v6_unified_adjudication_rules")]

    operations = [
        migrations.AlterField(
            model_name="pageevidence",
            name="evidence_type",
            field=models.CharField(default="page_region", max_length=64, verbose_name="证据类型"),
        ),
    ]
