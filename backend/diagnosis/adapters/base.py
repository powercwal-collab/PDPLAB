from abc import ABC, abstractmethod


class DiagnosisModelAdapter(ABC):
    provider = "unknown"
    model_name = "unknown"
    prompt_version = "pdp-score-v1"

    @abstractmethod
    def analyze(self, *, source, context, scoring_rules):
        """Return structured module suggestions and evidence; never return a trusted total score."""
        raise NotImplementedError
