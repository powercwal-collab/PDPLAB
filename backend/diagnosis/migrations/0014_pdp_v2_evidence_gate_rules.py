from django.db import migrations


def install_pdp_v2_rules(apps, schema_editor):
    # Import at migration runtime so the deployed source remains the single rule
    # definition.  Do not mutate pdp-v1: locked historical diagnoses must retain
    # the rules that produced them.
    from diagnosis.scoring import DEFAULT_SCORING_RULES

    ScoringStandard = apps.get_model("diagnosis", "ScoringStandard")
    ScoringStandard.objects.filter(is_active=True).update(is_active=False)
    ScoringStandard.objects.update_or_create(
        version=DEFAULT_SCORING_RULES["version"],
        defaults={
            "name": "PDP 11 模块评分标准（证据强制校验）",
            "rules": DEFAULT_SCORING_RULES,
            "is_active": True,
        },
    )


def reverse_pdp_v2_rules(apps, schema_editor):
    ScoringStandard = apps.get_model("diagnosis", "ScoringStandard")
    ScoringStandard.objects.filter(version="pdp-v2").update(is_active=False)
    ScoringStandard.objects.filter(version="pdp-v1").update(is_active=True)


class Migration(migrations.Migration):
    dependencies = [("diagnosis", "0013_userprofile")]

    operations = [migrations.RunPython(install_pdp_v2_rules, reverse_pdp_v2_rules)]
