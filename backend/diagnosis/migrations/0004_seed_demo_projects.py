from django.db import migrations


def seed_projects(apps, schema_editor):
    Project = apps.get_model("diagnosis", "Project")
    projects = [
        ("Nike Kids｜毛毛虫幼童学步鞋", "Nike Kids", "幼童学步鞋"),
        ("Nike Kids｜儿童足球球衣", "Nike Kids", "儿童足球服"),
        ("Nike Running｜城市轻跑鞋", "Nike Running", "跑步鞋"),
    ]
    for name, brand, category in projects:
        Project.objects.get_or_create(name=name, defaults={"brand": brand, "category": category})


def remove_seed_projects(apps, schema_editor):
    Project = apps.get_model("diagnosis", "Project")
    Project.objects.filter(name__in=[
        "Nike Kids｜毛毛虫幼童学步鞋",
        "Nike Kids｜儿童足球球衣",
        "Nike Running｜城市轻跑鞋",
    ]).delete()


class Migration(migrations.Migration):
    dependencies = [("diagnosis", "0003_diagnosisversion")]
    operations = [migrations.RunPython(seed_projects, remove_seed_projects)]
