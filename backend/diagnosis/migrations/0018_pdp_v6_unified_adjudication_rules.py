from django.db import migrations


def install_and_activate_pdp_v6_rules(apps, schema_editor):
    from diagnosis.scoring_standards.pdp_v6 import PDP_V6_RULES

    ScoringStandard = apps.get_model("diagnosis", "ScoringStandard")
    standard, _ = ScoringStandard.objects.update_or_create(
        version="pdp-v6",
        defaults={
            "name": "PDP 11 模块统一裁决评分标准",
            "rules": PDP_V6_RULES,
            "is_active": False,
        },
    )
    ScoringStandard.objects.filter(is_active=True).exclude(pk=standard.pk).update(is_active=False)
    standard.is_active = True
    standard.save(update_fields=["is_active"])


def reverse_pdp_v6_rules(apps, schema_editor):
    ScoringStandard = apps.get_model("diagnosis", "ScoringStandard")
    ScoringStandard.objects.filter(version="pdp-v6").update(is_active=False)
    previous = (
        ScoringStandard.objects.filter(version="pdp-v5").first()
        or ScoringStandard.objects.filter(version="pdp-v4").first()
        or ScoringStandard.objects.filter(version="pdp-v3").first()
    )
    if previous:
        previous.is_active = True
        previous.save(update_fields=["is_active"])


class Migration(migrations.Migration):
    dependencies = [("diagnosis", "0017_pdp_v5_latest_skill_rules")]

    operations = [
        migrations.RunPython(install_and_activate_pdp_v6_rules, reverse_pdp_v6_rules),
    ]
