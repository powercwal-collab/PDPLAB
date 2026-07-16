from django.db import migrations, models


def install_pdp_v3_rules(apps, schema_editor):
    from diagnosis.scoring import DEFAULT_SCORING_RULES

    ScoringStandard = apps.get_model("diagnosis", "ScoringStandard")
    ScoringStandard.objects.filter(is_active=True).update(is_active=False)
    ScoringStandard.objects.update_or_create(
        version="pdp-v3",
        defaults={
            "name": "PDP 11 模块五级成熟度评分标准",
            "rules": DEFAULT_SCORING_RULES,
            "is_active": True,
        },
    )


def reverse_pdp_v3_rules(apps, schema_editor):
    ScoringStandard = apps.get_model("diagnosis", "ScoringStandard")
    ScoringStandard.objects.filter(version="pdp-v3").update(is_active=False)
    ScoringStandard.objects.filter(version="pdp-v2").update(is_active=True)


class Migration(migrations.Migration):
    dependencies = [("diagnosis", "0015_pdpsource_content_sha256")]

    operations = [
        migrations.AlterField(
            model_name="diagnosisversion",
            name="total_score",
            field=models.DecimalField(decimal_places=2, max_digits=6, verbose_name="总分"),
        ),
        migrations.AlterField(
            model_name="moduleassessment",
            name="coefficient",
            field=models.DecimalField(decimal_places=2, max_digits=3, verbose_name="评分系数"),
        ),
        migrations.AlterField(
            model_name="moduleassessment",
            name="score",
            field=models.DecimalField(decimal_places=2, max_digits=6, verbose_name="得分"),
        ),
        migrations.RunPython(install_pdp_v3_rules, reverse_pdp_v3_rules),
    ]
