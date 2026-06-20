from __future__ import annotations
from dataclasses import dataclass

from app.adapters.validators.validator_chain import ChainResult, ValidationResult


# Pesos por validator — soma deve ser 1.0
_DEFAULT_WEIGHTS: dict[str, float] = {
    "completeness": 0.45,
    "traceability": 0.35,
    "content_length": 0.20,
}


@dataclass
class AggregatedScore:
    """Score composto com decomposição por validator para auditabilidade."""
    composite: float                          # Score final ponderado (0.0–1.0)
    by_validator: dict[str, float]            # Score de cada validator
    weights_used: dict[str, float]            # Pesos aplicados
    passed: bool

    @property
    def grade(self) -> str:
        """Classificação qualitativa para exibição."""
        if self.composite >= 0.90:
            return "A"
        if self.composite >= 0.75:
            return "B"
        if self.composite >= 0.60:
            return "C"
        return "D"


class ConfidenceAggregator:
    """
    Consolida os scores individuais dos validators em um score composto ponderado.

    Separado do ValidatorChain (que decide pass/fail) e do ResponseBuilder
    (que formata) — responsabilidade única: agregar e ponderar.

    Os pesos podem ser ajustados por tipo de artefato:
    - Para RTM: traceability tem peso maior (cobertura de RN/CA é crítica)
    - Para análise: completeness tem peso maior (todas as seções são obrigatórias)
    """

    def __init__(self, weights: dict[str, float] | None = None):
        self._weights = weights or _DEFAULT_WEIGHTS

    def aggregate(self, chain_result: ChainResult) -> AggregatedScore:
        by_validator: dict[str, float] = {}
        weighted_sum = 0.0
        total_weight = 0.0

        for result in chain_result.results:
            weight = self._weights.get(result.validator_name, 0.1)
            by_validator[result.validator_name] = result.score
            weighted_sum += result.score * weight
            total_weight += weight

        composite = round(weighted_sum / total_weight, 3) if total_weight > 0 else 0.0

        return AggregatedScore(
            composite=composite,
            by_validator=by_validator,
            weights_used=dict(self._weights),
            passed=chain_result.passed,
        )

    @classmethod
    def for_rtm(cls) -> "ConfidenceAggregator":
        """Pesos ajustados para artefatos RTM — traceability é mais crítica."""
        return cls(weights={
            "completeness": 0.25,
            "traceability": 0.55,
            "content_length": 0.20,
        })

    @classmethod
    def for_analysis(cls) -> "ConfidenceAggregator":
        """Pesos ajustados para análise de US — completeness é mais crítica."""
        return cls(weights={
            "completeness": 0.50,
            "traceability": 0.30,
            "content_length": 0.20,
        })
