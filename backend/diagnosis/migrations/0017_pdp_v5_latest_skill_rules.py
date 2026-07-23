from django.db import migrations


def install_pdp_v5_rules(apps, schema_editor):
    from diagnosis.scoring import DEFAULT_SCORING_RULES

    ScoringStandard = apps.get_model("diagnosis", "ScoringStandard")
    ScoringStandard.objects.filter(is_active=True).update(is_active=False)
    ScoringStandard.objects.update_or_create(
        version="pdp-v5",
        defaults={
            "name": "PDP 11 模块最新版 Skill 评分标准",
            "rules": DEFAULT_SCORING_RULES,
            "is_active": True,
        },
    )


def reverse_pdp_v5_rules(apps, schema_editor):
    ScoringStandard = apps.get_model("diagnosis", "ScoringStandard")
    ScoringStandard.objects.filter(version="pdp-v5").update(is_active=False)
    previous = (
        ScoringStandard.objects.filter(version="pdp-v4").first()
        or ScoringStandard.objects.filter(version="pdp-v3").first()
    )
    if previous:
        previous.is_active = True
        previous.save(update_fields=["is_active"])


class Migration(migrations.Migration):
    dependencies = [("diagnosis", "0016_pdp_v3_five_level_scoring")]

    operations = [migrations.RunPython(install_pdp_v5_rules, reverse_pdp_v5_rules)]
