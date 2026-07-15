from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("diagnosis", "0014_pdp_v2_evidence_gate_rules"),
    ]

    operations = [
        migrations.AddField(
            model_name="pdpsource",
            name="content_sha256",
            field=models.CharField(blank=True, db_index=True, max_length=64, verbose_name="文件内容指纹"),
        ),
    ]
