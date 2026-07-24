from django.db import migrations


def update_pdp_v6_runtime_consistency(apps, schema_editor):
    from diagnosis.scoring_standards.pdp_v6 import PDP_V6_RULES

    ScoringStandard = apps.get_model("diagnosis", "ScoringStandard")
    ScoringStandard.objects.filter(version="pdp-v6").update(
        name="PDP 11 模块统一裁决评分标准",
        rules=PDP_V6_RULES,
    )


def restore_previous_pdp_v6_rules(apps, schema_editor):
    # Historical diagnosis snapshots remain immutable. Reversing this data-only
    # synchronization intentionally leaves the last safe v6 rules in place.
    pass


class Migration(migrations.Migration):
    dependencies = [("diagnosis", "0019_expand_page_evidence_type")]

    operations = [
        migrations.RunPython(update_pdp_v6_runtime_consistency, restore_previous_pdp_v6_rules),
    ]
