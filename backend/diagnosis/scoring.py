DEFAULT_SCORING_RULES = {
    "version": "pdp-v1",
    "source_skill": "pdp-detail-page-methodology",
    "source_mode": "versioned_runtime_rules",
    "source_revision": "sha256:14b427e36ad81f75706f2e4fa2d76e5f087915a066e72221e59c1cd4c368a670",
    "skill_manifest_revision": "sha256:82ae404654c9ff9c57a2f1fe603abaf31fee7fb00c727471cdbde3c9330ba901",
    "coefficients": {"弱": 0, "中": 0.5, "强": 1},
    "maturity_definitions": {
        "弱": "无对应模块，用户无法在页面中获得该类购买决策信息",
        "中": "有对应模块，但信息浅或视觉弱；设计信息与视觉素材任一维度不达标都会影响消费者继续理解",
        "强": "有对应模块，且设计信息与视觉素材都围绕消费者需求展开，内容、证据、视觉表达与购买决策高度契合",
    },
    "judgment_order": ["模块存在性", "设计信息与视觉素材质量", "T1/T0 视觉层级匹配", "消费者需求匹配"],
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
        if coefficient not in {0, 0.5, 1}:
            raise ValueError(f"模块 {definition['code']} 返回了无效评分系数")
        maturity = {0: "弱", 0.5: "中", 1: "强"}[coefficient]
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
