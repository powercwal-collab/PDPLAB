from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("diagnosis", "0010_split_ai_and_skill_settings")]

    operations = [
        migrations.AddField(
            model_name="aimodelsettings",
            name="ai_protocol",
            field=models.CharField(
                choices=[("responses", "Responses API"), ("chat_completions", "Chat Completions")],
                default="responses",
                max_length=32,
                verbose_name="API 协议",
            ),
        ),
    ]
