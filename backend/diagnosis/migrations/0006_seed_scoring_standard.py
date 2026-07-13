from django.db import migrations


RULES = {
    "version": "pdp-v1",
    "coefficients": {"弱": 0, "中": 0.5, "强": 1},
    "modules": [
        {"code": "product_kv", "name": "产品KV/封面故事", "weight": 10},
        {"code": "scenario", "name": "沉浸式购物/场景化", "weight": 18},
        {"code": "selling_point_proof", "name": "卖点与功能证明", "weight": 14},
        {"code": "interactive_content", "name": "产品互动/动态内容", "weight": 8},
        {"code": "detail_review", "name": "细节查阅", "weight": 12},
        {"code": "fit_comparison", "name": "尺码/适配与对比选购", "weight": 10},
        {"code": "basic_information", "name": "基础信息", "weight": 8},
        {"code": "service", "name": "使用说明/服务事项", "weight": 5},
        {"code": "recommendation", "name": "关联推荐/延展购买", "weight": 5},
        {"code": "endorsement", "name": "品牌/产品背书", "weight": 5},
        {"code": "page_rhythm", "name": "页面结构与节奏", "weight": 5},
    ],
    "star_bands": [
        {"lt": 10, "rating": 1}, {"lt": 20, "rating": 1.5},
        {"lt": 27.5, "rating": 2}, {"lt": 35, "rating": 2.5},
        {"lt": 42.5, "rating": 3}, {"lt": 50, "rating": 3.5},
        {"lt": 57.5, "rating": 4}, {"lt": 65, "rating": 4.5},
        {"lt": 72.5, "rating": 5}, {"lt": 80, "rating": 5.5},
        {"lt": 85, "rating": 6}, {"lt": 90, "rating": 6.5},
        {"lt": 101, "rating": 7},
    ],
}


def create_standard(apps, schema_editor):
    ScoringStandard = apps.get_model("diagnosis", "ScoringStandard")
    ScoringStandard.objects.update_or_create(
        version="pdp-v1",
        defaults={"name": "PDP 11 模块评分标准", "rules": RULES, "is_active": True},
    )


def remove_standard(apps, schema_editor):
    ScoringStandard = apps.get_model("diagnosis", "ScoringStandard")
    ScoringStandard.objects.filter(version="pdp-v1").delete()


class Migration(migrations.Migration):
    dependencies = [("diagnosis", "0005_scoringstandard_diagnosisversion_confirmation_mode_and_more")]
    operations = [migrations.RunPython(create_standard, remove_standard)]
