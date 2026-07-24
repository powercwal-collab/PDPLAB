from .scoring_standards.pdp_v6 import PDP_V6_RULES


DEFAULT_SCORING_RULES = PDP_V6_RULES


# Evidence categories are a server contract, rather than a cosmetic prompt hint.  They
# allow the scoring engine to reject a model coefficient that is supported only by a
# title, logo, blank shell, or studio image.  Historic versions keep their saved score;
# these guards apply only while a new job is being calculated.
NON_QUALIFYING_EVIDENCE = {
    "missing_content", "generic_or_decorative", "empty_shell", "template_block",
    "generic_icon_row", "logo_only",
}

DESIGNED_SINGLE_SUBJECT_EVIDENCE = {"designed_model_only", "designed_product_only"}

MODULE_EVIDENCE_GATES = {
    "product_kv": {"product_hero_visual", "campaign_cover"},
    "scenario": {"real_use_scene", "lifestyle_scene", "sport_scene", "movement_scene", "styling_scene"},
    "recommendation": {"related_product_recommendation", "series_recommendation", "outfit_recommendation"},
    "endorsement": {"certification", "award", "institutional_endorsement", "technology_source", "attributable_review", "brand_asset_proof"},
}

FIT_STRONG_EVIDENCE = {
    "measurement_method", "fit_advice", "model_body_profile", "tryon_feedback", "series_comparison",
}

SCENARIO_CONTEXT_EVIDENCE = {
    "real_use_scene", "lifestyle_scene", "sport_scene", "movement_scene", "styling_scene",
}

FIT_SUPPORTING_EVIDENCE = {
    "model_body_profile", "fit_advice", "measurement_method", "series_comparison",
    "body_type_guidance", "wearing_preference",
}

SERVICE_GENERIC_EVIDENCE = {
    "generic_platform_service", "generic_icon_row", "service_policy",
}

SERVICE_PRODUCT_EVIDENCE = {
    "product_specific_care", "product_specific_return_boundary", "tryon_policy",
    "customization_policy", "product_warranty", "installation_guidance",
}


MATURITY_BY_COEFFICIENT = {0: "弱", 0.25: "较弱", 0.5: "中", 0.75: "强", 1: "极强"}
VALID_COEFFICIENTS = set(MATURITY_BY_COEFFICIENT)


def apply_evidence_guards(adapter_modules, evidence, rules=None):
    """Apply the PDP Skill's deterministic existence and hard-gate rules.

    The AI can identify evidence and propose a discrete coefficient, but it cannot
    override a zero-score gate.  This deliberately works on typed evidence only;
    untyped legacy ``page_region`` evidence remains compatible but cannot prove a
    module-specific gate on its own.
    """
    active_rules = rules or DEFAULT_SCORING_RULES
    boundary_locks = active_rules.get("boundary_locks", {})
    suggestions = {item["module_code"]: dict(item) for item in adapter_modules}
    evidence_by_module = {}
    for item in evidence or []:
        evidence_by_module.setdefault(item.get("module_code"), []).append(item.get("evidence_type", "page_region"))

    def force_zero(code, reason):
        suggestion = suggestions[code]
        if float(suggestion.get("coefficient", 0)) != 0:
            suggestion["coefficient"] = 0
            suggestion["judgment"] = f"{reason} 原模型判断：{suggestion.get('judgment', '')}"[:800]

    def cap(code, maximum, reason):
        suggestion = suggestions[code]
        if float(suggestion.get("coefficient", 0)) > maximum:
            suggestion["coefficient"] = maximum
            suggestion["judgment"] = f"{reason} 原模型判断：{suggestion.get('judgment', '')}"[:800]

    for code, suggestion in suggestions.items():
        types = set(evidence_by_module.get(code, []))
        if types and types.issubset(NON_QUALIFYING_EVIDENCE):
            force_zero(code, "未发现能回答具体购买问题的有效产品证据，形式性区块不计入模块存在。")

    for code, qualifying_types in MODULE_EVIDENCE_GATES.items():
        if code not in suggestions:
            continue
        types = set(evidence_by_module.get(code, []))
        if not (types & qualifying_types):
            labels = {
                "product_kv": "未发现产品主导的英雄视觉；仅文案、标题或卖点文字不能作为 KV。",
                "scenario": "未发现真实使用、运动、生活或穿搭场景；白/灰底模特与正背面展示不计作场景。",
                "recommendation": "未发现基于系列、场景、穿搭或用户意图的真实关联推荐；仅颜色/SKU 选项不计入推荐。",
                "endorsement": "未发现可归因的认证、机构、科技来源、口碑或品牌资产证据；单独 Logo 不计入背书。",
            }
            types = set(evidence_by_module.get(code, []))
            if code == "product_kv" and "hero_copy_only" in types:
                cap(code, 0.25, "存在产品相关文案但缺少产品主导英雄视觉，最高计为“较弱”。")
            elif code == "scenario" and "studio_model_view" in types:
                cap(code, 0.25, "存在棚拍/模特展示但缺少真实使用场景与利益绑定，最高计为“较弱”。")
            else:
                force_zero(code, labels[code])

    # Visual polish alone cannot produce a mature score.  The adapter reports
    # these axes, while the backend enforces deterministic ceilings.
    for code, suggestion in suggestions.items():
        information_level = suggestion.get("information_level", "")
        visual_tier = suggestion.get("visual_tier", "")
        integration = suggestion.get("integration", "")
        types = set(evidence_by_module.get(code, []))
        if information_level in {"none", "shallow"} or integration == "isolated":
            cap(code, 0.25, "信息或视觉仍是单一证据，尚未形成图文结合，最高计为“较弱”。")
        elif visual_tier == "t2":
            cap(code, 0.5, "当前为 T2 基础表达，最高计为“中”。")
        elif visual_tier == "t1":
            cap(code, 0.75, "当前为 T1 标准转化表达，最高计为“强”；“极强”需要 T0 标杆表达。")
        elif visual_tier != "t0" and float(suggestion.get("coefficient", 0)) == 1:
            cap(code, 0.75, "缺少可验证的 T0 视觉层级，不能计为“极强”。")
        if (
            visual_tier == "t0"
            and types & DESIGNED_SINGLE_SUBJECT_EVIDENCE
            and not types & {"designed_model_product_composite", "pagewide_designed_model_product_sequence"}
        ):
            cap(code, 0.75, "特殊非白底/灰底设计中仅有模特或仅有单产品，视觉最高按 T1 计为“强”；模特与产品需在同模块形成联合构图才可作为 T0 依据。")

    fit = suggestions.get("fit_comparison")
    if fit and float(fit.get("coefficient", 0)) >= 0.75 and "fit_comparison" not in boundary_locks:
        fit_types = set(evidence_by_module.get("fit_comparison", []))
        if len(fit_types & FIT_STRONG_EVIDENCE) < 2:
            fit["coefficient"] = 0.5
            fit["judgment"] = (
                "仅有尺码表或单一适配信息，不足以达到“强”；需同时提供测量方式、版型建议、模特/试穿或系列对比等至少两类依据。 原模型判断："
                + fit.get("judgment", "")
            )[:800]

    if "scenario" in boundary_locks:
        scenario = suggestions.get("scenario")
        scenario_types = set(evidence_by_module.get("scenario", []))
        if scenario and float(scenario.get("coefficient", 0)) == 1:
            context_count = len(scenario_types & SCENARIO_CONTEXT_EVIDENCE)
            if context_count < 2 or "scene_benefit_link" not in scenario_types:
                cap(
                    "scenario",
                    0.75,
                    "场景大片缺少多场景覆盖或明确的场景—产品利益证明，按统一边界最高计为“强”。",
                )

    if "fit_comparison" in boundary_locks and fit:
        fit_types = set(evidence_by_module.get("fit_comparison", []))
        if float(fit.get("coefficient", 0)) >= 0.75:
            supporting_count = len(fit_types & FIT_SUPPORTING_EVIDENCE)
            if "size_chart" not in fit_types or supporting_count < 2:
                cap(
                    "fit_comparison",
                    0.5,
                    "达到“强”必须同时有尺码表和至少两类模特、版型、测量、版本或偏好依据。",
                )
        if float(fit.get("coefficient", 0)) == 1:
            personalized = bool(fit_types & {"personalized_fit_guidance", "body_type_guidance"})
            visualization = bool(fit_types & {"fit_visualization", "tryon_feedback"})
            if not (personalized and visualization and "series_comparison" in fit_types):
                cap(
                    "fit_comparison",
                    0.75,
                    "“极强”还需个性化/身型指导、适配可视化或消费者证据，以及完整版本对比。",
                )

    if "service" in boundary_locks:
        service = suggestions.get("service")
        if service:
            service_types = set(evidence_by_module.get("service", []))
            product_types = service_types & SERVICE_PRODUCT_EVIDENCE
            generic_types = service_types & SERVICE_GENERIC_EVIDENCE
            if not product_types:
                force_zero("service", "仅有平台通用服务或模板通知，未降低该产品的具体购买风险。")
            elif len(product_types) == 1:
                cap("service", 0.25, "仅有一项产品专属护理或服务边界，最高计为“较弱”。")
            elif generic_types and len(product_types) <= 2:
                cap("service", 0.5, "通用平台通知与有限产品专属服务混合，最高计为“中”。")
            if float(service.get("coefficient", 0)) == 1:
                if len(product_types) < 3 or "premium_service_proof" not in service_types:
                    cap("service", 0.75, "“极强”需要完整产品专属覆盖、可信高端服务证明与 T0 系统表达。")

    rhythm = suggestions.get("page_rhythm")
    if rhythm and float(rhythm.get("coefficient", 0)) >= 0.75:
        if float(suggestions.get("product_kv", {}).get("coefficient", 0)) <= 0.25 or float(suggestions.get("scenario", {}).get("coefficient", 0)) <= 0.25:
            rhythm["coefficient"] = 0.5
            rhythm["judgment"] = (
                "缺少有效 KV 或真实场景，页面尚未形成完整的“封面—沉浸—证明—决策—信任”叙事，结构节奏最高计为中。 原模型判断："
                + rhythm.get("judgment", "")
            )[:800]

    return [suggestions[item["module_code"]] for item in adapter_modules]


def map_overall_rating(total_score, rules=None):
    active_rules = rules or DEFAULT_SCORING_RULES
    for band in active_rules["star_bands"]:
        if float(total_score) < band["lt"]:
            return band["rating"]
    return 7


def calculate_assessments(adapter_modules, rules=None):
    active_rules = rules or DEFAULT_SCORING_RULES
    suggestions = {item["module_code"]: item for item in adapter_modules}
    modules = []
    for definition in active_rules["modules"]:
        suggestion = suggestions.get(definition["code"], {})
        coefficient = float(suggestion.get("coefficient", 0))
        if coefficient not in VALID_COEFFICIENTS:
            raise ValueError(f"模块 {definition['code']} 返回了无效评分系数")
        maturity = MATURITY_BY_COEFFICIENT[coefficient]
        modules.append({
            "code": definition["code"],
            "name": definition["name"],
            "max": definition["weight"],
            "weight": definition["weight"],
            "coefficient": coefficient,
            "score": definition["weight"] * coefficient,
            "maturity": maturity,
            "judgment": suggestion.get("judgment", "模型未返回具体判断"),
            "confidence": float(suggestion.get("confidence", 0)),
            "checked": True,
        })
    total_score = sum(module["score"] for module in modules)
    return modules, total_score, map_overall_rating(total_score, active_rules)
