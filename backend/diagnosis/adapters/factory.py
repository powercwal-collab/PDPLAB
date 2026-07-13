from .mock import MockDiagnosisAdapter
from .openai import OpenAIDiagnosisAdapter
from ..runtime_config import get_runtime_integration_config


def get_diagnosis_adapter(name=None):
    config = get_runtime_integration_config()
    adapter_name = name or config["adapter"]
    if adapter_name == "auto":
        adapter_name = "openai" if config["api_key"] else "mock"
    if adapter_name == "mock":
        return MockDiagnosisAdapter()
    if adapter_name == "openai":
        return OpenAIDiagnosisAdapter(runtime_config=config)
    raise RuntimeError(f"未配置诊断模型适配器：{adapter_name}")
