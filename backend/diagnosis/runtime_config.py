from django.conf import settings
from django.db.utils import OperationalError, ProgrammingError


def get_runtime_integration_config():
    config = {
        "adapter": settings.PDP_DIAGNOSIS_ADAPTER,
        "protocol": settings.PDP_AI_PROTOCOL,
        "model_name": settings.PDP_MODEL_NAME,
        "api_key": settings.OPENAI_API_KEY,
        "base_url": settings.OPENAI_BASE_URL,
        "timeout_seconds": settings.OPENAI_TIMEOUT_SECONDS,
        "skill_name": "pdp-detail-page-methodology",
        "skill_mode": "built_in",
        "skill_endpoint_url": "",
        "skill_timeout_seconds": 30,
        "skill_token": "",
        "source": "environment",
        "ai_config_source": "environment",
        "skill_config_source": "default",
    }
    try:
        from .models import AiModelSettings, PdpSkillSettings

        ai_saved = AiModelSettings.objects.filter(is_active=True).order_by("-updated_at").first()
        skill_saved = PdpSkillSettings.objects.filter(is_active=True).order_by("-updated_at").first()
    except (OperationalError, ProgrammingError):
        ai_saved = None
        skill_saved = None
    if ai_saved is not None:
        stored_key = ai_saved.get_api_key()
        config.update({
            "adapter": ai_saved.ai_adapter,
            "protocol": ai_saved.ai_protocol,
            "model_name": ai_saved.ai_model_name,
            "api_key": stored_key or config["api_key"],
            "base_url": ai_saved.ai_base_url or config["base_url"],
            "timeout_seconds": ai_saved.ai_timeout_seconds,
            "ai_config_source": "admin",
        })
    if skill_saved is not None:
        config.update({
            "skill_name": skill_saved.skill_name,
            "skill_mode": skill_saved.skill_mode,
            "skill_endpoint_url": skill_saved.skill_endpoint_url,
            "skill_timeout_seconds": skill_saved.skill_timeout_seconds,
            "skill_token": skill_saved.get_skill_token(),
            "skill_config_source": "admin",
        })
    if ai_saved is not None or skill_saved is not None:
        config["source"] = "admin"
    return config
