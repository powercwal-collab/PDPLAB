from .base import DiagnosisModelAdapter


class MockDiagnosisAdapter(DiagnosisModelAdapter):
    provider = "mock"
    model_name = "pdp-methodology-mock-v1"

    def analyze(self, *, source, context, scoring_rules):
        coefficients = {
            "product_kv": 0.5,
            "scenario": 0.5,
            "selling_point_proof": 0.5,
            "interactive_content": 0,
            "detail_review": 0.75,
            "fit_comparison": 0.5,
            "basic_information": 0.75,
            "service": 0.5,
            "recommendation": 0.5,
            "endorsement": 0.5,
            "page_rhythm": 0.75,
        }
        judgments = {
            "product_kv": "有产品封面与基础主张，但首屏缺少更清晰的系列定位与利益点排序。",
            "scenario": "存在商品展示，但真实使用场景与消费者利益的绑定不足。",
            "selling_point_proof": "有功能描述，但缺少结构、测试、材料或对比证据。",
            "interactive_content": "未识别到能够解释功能或试穿效果的视频、3D 或动态内容。",
            "detail_review": "多角度与局部细节较完整，能够支持材质和结构查阅。",
            "fit_comparison": "存在尺码信息，但脚型、临界码与对比选择建议仍不完整。",
            "basic_information": "材质、颜色、规格与商品基础信息较完整。",
            "service": "有基础服务说明，但护理、退换和售后信息仍可结构化。",
            "recommendation": "存在关联商品，但推荐逻辑与场景、穿搭或用户意图关联较弱。",
            "endorsement": "有品牌信息，但认证、口碑或专业背书证据仍不足。",
            "page_rhythm": "页面结构完整，主要模块顺序能够形成基础购买叙事。",
        }
        modules = []
        evidence = []
        evidence_types = {
            "product_kv": "product_hero_visual",
            "scenario": "real_use_scene",
            "selling_point_proof": "product_proof",
            "interactive_content": "missing_content",
            "detail_review": "detail_view",
            "fit_comparison": "fit_advice",
            "basic_information": "basic_information",
            "service": "service_policy",
            "recommendation": "related_product_recommendation",
            "endorsement": "brand_asset_proof",
            "page_rhythm": "page_structure",
        }
        for index, definition in enumerate(scoring_rules["modules"]):
            code = definition["code"]
            modules.append({
                "module_code": code,
                "coefficient": coefficients[code],
                "information_level": "none" if coefficients[code] == 0 else "complete",
                "visual_tier": "none" if coefficients[code] == 0 else ("t1" if coefficients[code] == 0.75 else "t2"),
                "integration": "isolated" if coefficients[code] == 0 else "matched",
                "judgment": judgments[code],
                "confidence": 0.82 if coefficients[code] != 0 else 0.94,
            })
            evidence.append({
                "module_code": code,
                "page_index": index,
                "bbox": {"x": 0.08, "y": min(0.82, 0.06 + index * 0.07), "width": 0.84, "height": 0.12},
                "evidence_type": evidence_types[code],
                "ocr_text": f"{definition['name']}：示例识别证据",
                "reason": judgments[code],
                "confidence": 0.82,
            })
        return {"modules": modules, "evidence": evidence, "usage": {"mode": "mock", "external_api": False}}
