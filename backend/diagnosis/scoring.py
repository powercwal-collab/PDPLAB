DEFAULT_SCORING_RULES = {
    "version": "pdp-v3",
    "source_skill": "pdp-detail-page-methodology",
    "source_mode": "versioned_runtime_rules",
    "source_revision": "sha256:5608bdd07b424761fca91cc30ad9abf38366a7ed21c9dd3742641d2f8d8dda2e",
    "skill_manifest_revision": "sha256:5608bdd07b424761fca91cc30ad9abf38366a7ed21c9dd3742641d2f8d8dda2e",
    "coefficients": {"弱": 0, "较弱": 0.25, "中": 0.5, "较强": 0.75, "强": 1},
    "maturity_definitions": {
        "弱": "无有效模块；标题、占位、通用模板、装饰素材或空壳不计入模块存在",
        "较弱": "有产品相关内容，但只有文案、单一信息、T2 视觉或棚拍/模特图，信息与视觉尚未形成有效结合",
        "中": "产品信息与 T2 级视觉形成基本结合，能够回答基础购买问题，但证据、吸引力或叙事仍不完整",
        "较强": "完整匹配的信息内容与 T1 级视觉有效结合，层级清楚并能辅助购买决策",
        "强": "完整可信的信息、证据与 T0 级视觉高度结合，形成品牌记忆、专业说服与标杆增长表达",
    },
    "judgment_order": ["有效存在性", "信息完整度", "T2/T1/T0 视觉层级", "信息与视觉匹配度", "消费者购买决策价值"],
    "modules": [
        {"code": "product_kv", "name": "产品KV/封面故事", "weight": 10, "strong_standard": "0.5-1屏内讲清产品主张、系列定位、核心卖点和主视觉"},
        {"code": "scenario", "name": "沉浸式购物/场景化", "weight": 18, "strong_standard": "场景覆盖真实使用、穿搭、运动状态和情绪代入"},
        {"code": "selling_point_proof", "name": "卖点与功能证明", "weight": 14, "strong_standard": "核心卖点排序清楚，有技术、材料、对比或使用证据"},
        {"code": "interactive_content", "name": "产品互动/动态内容", "weight": 8, "strong_standard": "视频、AR、3D或动效直接解释功能、结构或试穿效果"},
        {"code": "detail_review", "name": "细节查阅", "weight": 12, "strong_standard": "多角度、颜色、材质、结构、局部细节完整"},
        {"code": "fit_comparison", "name": "尺码/适配与对比选购", "weight": 10, "strong_standard": "测量方式、脚型/身型、版型建议、消费者荐言、系列对比完整"},
        {"code": "basic_information", "name": "基础信息", "weight": 8, "strong_standard": "面料、材质、成分、颜色、货号、规格结构化呈现"},
        {"code": "service", "name": "使用说明/服务事项", "weight": 5, "strong_standard": "服务、护理、退换、售后能降低购买顾虑"},
        {"code": "recommendation", "name": "关联推荐/延展购买", "weight": 5, "strong_standard": "推荐基于系列、场景、穿搭、用户意图"},
        {"code": "endorsement", "name": "品牌/产品背书", "weight": 5, "strong_standard": "有认证、奖项、机构、科技来源、用户口碑或品牌资产"},
        {"code": "page_rhythm", "name": "页面结构与节奏", "weight": 5, "strong_standard": "封面-沉浸-卖点-细节-信息-服务-推荐-背书形成购买叙事"},
    ],
    "star_bands": [
        {"lt": 10, "rating": 1, "page_type": "严重信息缺失页", "business_meaning": "几乎无法转化"},
        {"lt": 20, "rating": 1.5, "page_type": "信息缺失页", "business_meaning": "很难转化"},
        {"lt": 27.5, "rating": 2, "page_type": "基础陈列页", "business_meaning": "只能展示商品"},
        {"lt": 35, "rating": 2.5, "page_type": "基础陈列增强页", "business_meaning": "商品展示更完整，但决策支持弱"},
        {"lt": 42.5, "rating": 3, "page_type": "基础说明页", "business_meaning": "能看懂，但说服弱"},
        {"lt": 50, "rating": 3.5, "page_type": "基础说明增强页", "business_meaning": "信息更完整，但证据和视觉吸引不足"},
        {"lt": 57.5, "rating": 4, "page_type": "完整说明页", "business_meaning": "基本完整，但转化阻力多"},
        {"lt": 65, "rating": 4.5, "page_type": "完整说明增强页", "business_meaning": "接近成熟转化，但关键模块仍偏中"},
        {"lt": 72.5, "rating": 5, "page_type": "成熟转化页", "business_meaning": "能支撑大多数用户决策"},
        {"lt": 80, "rating": 5.5, "page_type": "成熟转化增强页", "business_meaning": "转化链路成熟，少数专业证据仍待补强"},
        {"lt": 85, "rating": 6, "page_type": "专业决策页", "business_meaning": "有强证据、强场景、强信任"},
        {"lt": 90, "rating": 6.5, "page_type": "专业决策增强页", "business_meaning": "专业证据充分，接近标杆增长"},
        {"lt": 101, "rating": 7, "page_type": "标杆增长页", "business_meaning": "形成品牌级内容资产"},
    ],
}


# Evidence categories are a server contract, rather than a cosmetic prompt hint.  They
# allow the scoring engine to reject a model coefficient that is supported only by a
# title, logo, blank shell, or studio image.  Historic versions keep their saved score;
# these guards apply only while a new job is being calculated.
NON_QUALIFYING_EVIDENCE = {
    "missing_content", "generic_or_decorative", "empty_shell", "template_block",
    "generic_icon_row", "logo_only",
}

MODULE_EVIDENCE_GATES = {
    "product_kv": {"product_hero_visual", "campaign_cover"},
    "scenario": {"real_use_scene", "lifestyle_scene", "sport_scene", "movement_scene", "styling_scene"},
    "recommendation": {"related_product_recommendation", "series_recommendation", "outfit_recommendation"},
    "endorsement": {"certification", "award", "institutional_endorsement", "technology_source", "attributable_review", "brand_asset_proof"},
}

FIT_STRONG_EVIDENCE = {
    "measurement_method", "fit_advice", "model_body_profile", "tryon_feedback", "series_comparison",
}


MATURITY_BY_COEFFICIENT = {0: "弱", 0.25: "较弱", 0.5: "中", 0.75: "较强", 1: "强"}
VALID_COEFFICIENTS = set(MATURITY_BY_COEFFICIENT)


def apply_evidence_guards(adapter_modules, evidence, rules=None):
    """Apply the PDP Skill's deterministic existence and hard-gate rules.

    The AI can identify evidence and propose a discrete coefficient, but it cannot
    override a zero-score gate.  This deliberately works on typed evidence only;
    untyped legacy ``page_region`` evidence remains compatible but cannot prove a
    module-specific gate on its own.
    """
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
        if information_level in {"none", "shallow"} or integration == "isolated":
            cap(code, 0.25, "信息或视觉仍是单一证据，尚未形成图文结合，最高计为“较弱”。")
        elif visual_tier == "t2":
            cap(code, 0.5, "当前为 T2 基础表达，最高计为“中”。")
        elif visual_tier == "t1":
            cap(code, 0.75, "当前为 T1 标准转化表达，最高计为“较强”；“强”需要 T0 标杆表达。")
        elif visual_tier != "t0" and float(suggestion.get("coefficient", 0)) == 1:
            cap(code, 0.75, "缺少可验证的 T0 视觉层级，不能计为“强”。")

    fit = suggestions.get("fit_comparison")
    if fit and float(fit.get("coefficient", 0)) >= 0.75:
        fit_types = set(evidence_by_module.get("fit_comparison", []))
        if len(fit_types & FIT_STRONG_EVIDENCE) < 2:
            fit["coefficient"] = 0.5
            fit["judgment"] = (
                "仅有尺码表或单一适配信息，不足以达到“强”；需同时提供测量方式、版型建议、模特/试穿或系列对比等至少两类依据。 原模型判断："
                + fit.get("judgment", "")
            )[:800]

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
