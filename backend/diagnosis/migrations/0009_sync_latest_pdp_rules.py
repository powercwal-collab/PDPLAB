from django.db import migrations


def sync_latest_pdp_rules(apps, schema_editor):
    from diagnosis.scoring import DEFAULT_SCORING_RULES

    ScoringStandard = apps.get_model("diagnosis", "ScoringStandard")
    IntegrationSettings = apps.get_model("diagnosis", "IntegrationSettings")
    ScoringStandard.objects.update_or_create(
        version=DEFAULT_SCORING_RULES["version"],
        defaults={
            "name": "PDP 11 模块评分标准",
            "rules": DEFAULT_SCORING_RULES,
            "is_active": True,
        },
    )
    IntegrationSettings.objects.get_or_create(
        name="PDP Lab 默认集成",
        defaults={
            "is_active": True,
            "ai_adapter": "auto",
            "ai_model_name": "gpt-5.4-mini",
            "skill_name": "pdp-detail-page-methodology",
            "skill_mode": "built_in",
        },
    )


class Migration(migrations.Migration):
    dependencies = [("diagnosis", "0008_integration_settings")]
    operations = [migrations.RunPython(sync_latest_pdp_rules, migrations.RunPython.noop)]
