import base64
import json
from pathlib import Path
from typing import Literal

from django.conf import settings
from openai import OpenAI
from pydantic import BaseModel, Field

from .base import DiagnosisModelAdapter


class ModuleSuggestion(BaseModel):
    module_code: str
    coefficient: Literal[0, 0.5, 1]
    judgment: str = Field(min_length=4, max_length=800)
    confidence: float = Field(ge=0, le=1)


class EvidenceSuggestion(BaseModel):
    module_code: str
    page_index: int = Field(ge=0)
    bbox: dict[str, float] = Field(default_factory=dict)
    evidence_type: str = "page_region"
    ocr_text: str = ""
    reason: str = Field(min_length=4, max_length=800)
    confidence: float = Field(ge=0, le=1)


class PdpDiagnosisOutput(BaseModel):
    modules: list[ModuleSuggestion]
    evidence: list[EvidenceSuggestion]


class OpenAIDiagnosisAdapter(DiagnosisModelAdapter):
    provider = "openai"
    prompt_version = "pdp-score-openai-v2"

    def __init__(self, client=None, runtime_config=None):
        config = runtime_config or {
            "model_name": settings.PDP_MODEL_NAME,
            "protocol": settings.PDP_AI_PROTOCOL,
            "api_key": settings.OPENAI_API_KEY,
            "base_url": settings.OPENAI_BASE_URL,
            "timeout_seconds": settings.OPENAI_TIMEOUT_SECONDS,
        }
        self.model_name = config["model_name"]
        self.protocol = config.get("protocol", "responses")
        if client is not None:
            self.client = client
            return
        if not config["api_key"]:
            raise RuntimeError("OPENAI_API_KEY 未配置，无法使用 OpenAI 诊断适配器")
        kwargs = {
            "api_key": config["api_key"],
            "timeout": config["timeout_seconds"],
            "max_retries": 2,
        }
        if config["base_url"]:
            kwargs["base_url"] = config["base_url"]
        self.client = OpenAI(**kwargs)

    def _instructions(self, scoring_rules):
        modules = [{
            "module_code": item["code"],
            "name": item["name"],
            "weight": item["weight"],
            "strong_standard": item.get("strong_standard", ""),
        } for item in scoring_rules["modules"]]
        return (
            "你是电商 PDP 详情页诊断引擎。仅根据上传文件中可见的内容和用户上下文评估。"
            "对每个模块必须返回且只返回一条结果：0=弱，0.5=中，1=强。"
            "不要计算总分或星级，服务端将用版本化评分规则计算。"
            "每个模块至少返回一条证据；若未观察到对应内容，仍返回一条 missing_content 证据并说明缺口。"
            "bbox 使用 0~1 归一化坐标，包含 x/y/width/height；无法定位时可为空对象。"
            "输出必须是单个 JSON 对象，顶层只允许 modules 与 evidence 两个数组，禁止用模块编码作为顶层键。"
            "modules 每项必须包含 module_code、coefficient、judgment、confidence；"
            "evidence 每项必须包含 module_code、page_index、bbox、evidence_type、ocr_text、reason、confidence。"
            "特别注意：weight 是服务端权重，只供你理解重要性，绝对不能填入 coefficient。"
            "coefficient 只能是数字 0、0.5、1；judgment 必须是解释判断的中文字符串，不能是数字。"
            "格式示例：{\"modules\":[{\"module_code\":\"product_kv\",\"coefficient\":0.5,"
            "\"judgment\":\"有主视觉但利益点证明一般\",\"confidence\":0.82}],"
            "\"evidence\":[{\"module_code\":\"product_kv\",\"page_index\":0,"
            "\"bbox\":{\"x\":0.1,\"y\":0.1,\"width\":0.8,\"height\":0.2},"
            "\"evidence_type\":\"page_region\",\"ocr_text\":\"可见文字\","
            "\"reason\":\"该区域支持当前判断\",\"confidence\":0.82}]}。"
            f"\n成熟度定义：{json.dumps(scoring_rules.get('maturity_definitions', {}), ensure_ascii=False)}"
            f"\n判断顺序：{json.dumps(scoring_rules.get('judgment_order', []), ensure_ascii=False)}"
            f"\n评分模块：{json.dumps(modules, ensure_ascii=False)}"
        )

    def _input_content(self, source, context, file_id):
        suffix = Path(source.original_name).suffix.lower()
        content = [{
            "type": "input_text",
            "text": "请诊断这份 PDP 文件。业务上下文：" + json.dumps(context or {}, ensure_ascii=False),
        }]
        if suffix == ".pdf":
            content.append({"type": "input_file", "file_id": file_id})
        else:
            content.append({"type": "input_image", "file_id": file_id, "detail": "high"})
        return [{"role": "user", "content": content}]

    def _chat_input_content(self, source, context):
        suffix = Path(source.original_name).suffix.lower()
        if suffix == ".pdf":
            raise ValueError("当前 Chat Completions 模型暂不支持 PDF 诊断，请上传 PNG 或 JPG。")
        mime_type = "image/png" if suffix == ".png" else "image/jpeg"
        with source.file.open("rb") as source_file:
            encoded = base64.b64encode(source_file.read()).decode("ascii")
        return [{
            "role": "system",
            "content": self._instructions(context["scoring_rules"]),
        }, {
            "role": "user",
            "content": [{
                "type": "text",
                "text": "请诊断这份 PDP 图片。业务上下文：" + json.dumps(context.get("business_context") or {}, ensure_ascii=False),
            }, {
                "type": "image_url",
                "image_url": {"url": f"data:{mime_type};base64,{encoded}", "detail": "high"},
            }],
        }]

    def _validate_output(self, parsed, scoring_rules):
        expected = [item["code"] for item in scoring_rules["modules"]]
        module_codes = [item.module_code for item in parsed.modules]
        if len(module_codes) != len(expected) or set(module_codes) != set(expected):
            raise ValueError("OpenAI 结果必须包含且仅包含 11 个规定评分模块")
        evidence_codes = {item.module_code for item in parsed.evidence}
        missing_evidence = set(expected) - evidence_codes
        if missing_evidence:
            raise ValueError(f"OpenAI 结果缺少模块证据：{', '.join(sorted(missing_evidence))}")
        for evidence in parsed.evidence:
            if evidence.module_code not in expected:
                raise ValueError(f"OpenAI 结果含未知证据模块：{evidence.module_code}")
            for key, value in evidence.bbox.items():
                if key not in {"x", "y", "width", "height"} or not 0 <= float(value) <= 1:
                    raise ValueError("证据 bbox 必须使用 0~1 归一化 x/y/width/height")

    def analyze(self, *, source, context, scoring_rules):
        if self.protocol == "chat_completions":
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=self._chat_input_content(source, {
                    "business_context": context,
                    "scoring_rules": scoring_rules,
                }),
                response_format={"type": "json_object"},
                max_completion_tokens=12000,
                temperature=0,
                extra_body={"thinking": {"type": "disabled"}},
            )
            raw_content = (response.choices[0].message.content or "").strip()
            if raw_content.startswith("```"):
                raw_content = raw_content.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
            if not raw_content:
                raise ValueError("兼容模型未返回可解析的 PDP 诊断结果")
            parsed = PdpDiagnosisOutput.model_validate_json(raw_content)
            self._validate_output(parsed, scoring_rules)
            usage = response.usage.model_dump() if response.usage else {}
            return {
                "modules": [item.model_dump() for item in parsed.modules],
                "evidence": [item.model_dump() for item in parsed.evidence],
                "usage": {**usage, "mode": "chat_completions", "external_api": True},
                "request_id": response.id,
            }

        suffix = Path(source.original_name).suffix.lower()
        purpose = "user_data" if suffix == ".pdf" else "vision"
        remote_file = None
        try:
            with source.file.open("rb") as source_file:
                remote_file = self.client.files.create(file=source_file, purpose=purpose)
            response = self.client.responses.parse(
                model=self.model_name,
                instructions=self._instructions(scoring_rules),
                input=self._input_content(source, context, remote_file.id),
                text_format=PdpDiagnosisOutput,
                store=False,
            )
            parsed = response.output_parsed
            if parsed is None:
                raise ValueError("OpenAI 未返回可解析的 PDP 诊断结果")
            self._validate_output(parsed, scoring_rules)
            usage = response.usage.model_dump() if response.usage else {}
            return {
                "modules": [item.model_dump() for item in parsed.modules],
                "evidence": [item.model_dump() for item in parsed.evidence],
                "usage": {**usage, "mode": "openai", "external_api": True},
                "request_id": response.id,
            }
        finally:
            if remote_file is not None:
                try:
                    self.client.files.delete(remote_file.id)
                except Exception:
                    pass
