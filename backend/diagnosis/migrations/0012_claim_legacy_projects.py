from django.conf import settings
from django.db import migrations


def claim_legacy_projects(apps, schema_editor):
    Project = apps.get_model("diagnosis", "Project")
    User = apps.get_model(*settings.AUTH_USER_MODEL.split("."))
    owner = User.objects.filter(username="powercwal").first()
    if owner is None:
        owner = User.objects.filter(is_superuser=True).order_by("id").first()
    if owner is not None:
        Project.objects.filter(owner__isnull=True).update(owner=owner)


class Migration(migrations.Migration):
    dependencies = [("diagnosis", "0011_aimodelsettings_ai_protocol")]
    operations = [migrations.RunPython(claim_legacy_projects, migrations.RunPython.noop)]
