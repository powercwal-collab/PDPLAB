from django.db import migrations


def link_scoring_standard(apps, schema_editor):
    ScoringStandard = apps.get_model("diagnosis", "ScoringStandard")
    standard = ScoringStandard.objects.filter(version="pdp-v1").first()
    if standard is None:
        return
    rules = dict(standard.rules or {})
    rules["source_skill"] = "pdp-detail-page-methodology"
    rules["source_mode"] = "versioned_runtime_rules"
    standard.rules = rules
    standard.save(update_fields=["rules"])


def unlink_scoring_standard(apps, schema_editor):
    ScoringStandard = apps.get_model("diagnosis", "ScoringStandard")
    standard = ScoringStandard.objects.filter(version="pdp-v1").first()
    if standard is None:
        return
    rules = dict(standard.rules or {})
    rules.pop("source_skill", None)
    rules.pop("source_mode", None)
    standard.rules = rules
    standard.save(update_fields=["rules"])


class Migration(migrations.Migration):
    dependencies = [("diagnosis", "0006_seed_scoring_standard")]
    operations = [migrations.RunPython(link_scoring_standard, unlink_scoring_standard)]
