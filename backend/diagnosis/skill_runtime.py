import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from django.db import transaction

from .models import ScoringStandard
from .runtime_config import get_runtime_integration_config
from .scoring import DEFAULT_SCORING_RULES


def _validate_remote_rules(rules):
    expected_codes = {item["code"] for item in DEFAULT_SCORING_RULES["modules"]}
    modules = rules.get("modules") if isinstance(rules, dict) else None
    if not isinstance(modules, list) or {item.get("code") for item in modules} != expected_codes:
        raise RuntimeError("远程 PDP Skill 必须返回完整的 11 模块规则")
    if round(sum(float(item.get("weight", 0)) for item in modules), 3) != 100:
        raise RuntimeError("远程 PDP Skill 模块权重合计必须为 100")
    if rules.get("coefficients") != {"弱": 0, "中": 0.5, "强": 1}:
        raise RuntimeError("远程 PDP Skill 必须使用弱/中/强三档系数")
    if not rules.get("star_bands"):
        raise RuntimeError("远程 PDP Skill 缺少整体星级分段")


def _fetch_remote_standard(config):
    headers = {"Accept": "application/json"}
    if config["skill_token"]:
        headers["Authorization"] = f"Bearer {config['skill_token']}"
    request = Request(config["skill_endpoint_url"], headers=headers, method="GET")
    try:
        with urlopen(request, timeout=config["skill_timeout_seconds"]) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as error:
        raise RuntimeError(f"无法连接远程 PDP Skill：{error}") from error
    rules = payload.get("rules", payload)
    _validate_remote_rules(rules)
    rules = dict(rules)
    rules["source_skill"] = config["skill_name"]
    rules["source_mode"] = "remote_http"
    version = str(payload.get("version") or rules.get("version") or "pdp-remote-v1")[:32]
    rules["version"] = version
    return {
        "version": version,
        "name": str(payload.get("name") or f"{config['skill_name']} 远程评分标准")[:100],
        "rules": rules,
    }


def resolve_scoring_standard():
    config = get_runtime_integration_config()
    if config["skill_mode"] == "remote_http":
        remote = _fetch_remote_standard(config)
        with transaction.atomic():
            ScoringStandard.objects.filter(is_active=True).exclude(version=remote["version"]).update(is_active=False)
            standard, _ = ScoringStandard.objects.update_or_create(
                version=remote["version"],
                defaults={"name": remote["name"], "rules": remote["rules"], "is_active": True},
            )
            return standard
    standard = ScoringStandard.objects.filter(version=DEFAULT_SCORING_RULES["version"]).first()
    if standard is None:
        standard = ScoringStandard.objects.create(
            version=DEFAULT_SCORING_RULES["version"],
            name="PDP 11 模块评分标准",
            rules=DEFAULT_SCORING_RULES,
            is_active=True,
        )
    elif not standard.is_active:
        with transaction.atomic():
            ScoringStandard.objects.filter(is_active=True).exclude(pk=standard.pk).update(is_active=False)
            standard.is_active = True
            standard.save(update_fields=["is_active"])
    return standard
