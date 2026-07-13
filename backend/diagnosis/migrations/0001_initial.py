from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = []
    operations = [
        migrations.CreateModel(
            name="Project",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=160, verbose_name="项目名称")),
                ("brand", models.CharField(blank=True, max_length=100, verbose_name="品牌")),
                ("category", models.CharField(blank=True, max_length=100, verbose_name="品类")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="更新时间")),
            ],
            options={"ordering": ["-updated_at"]},
        ),
    ]
