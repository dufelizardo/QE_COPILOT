from __future__ import annotations
import json
from dataclasses import dataclass, field
from typing import Any


@dataclass
class RequirementAnalysisResponse:
    """
    DTO tipado para saída de análise de User Story existente.
    Contrato estável com o caller — independente de qual LLM ou prompt foi usado.

    Cada campo é rastreável até uma decisão anterior no pipeline:
    - conteudo_markdown  ← gerado pelo LLM via AnalyzeUserStory use case
    - secoes_presentes   ← detectadas pelo use case após geração
    - confidence_score   ← agregado pelo ConfidenceAggregator
    - validacoes         ← produzidas pelo ValidatorChain
    - modelo_usado       ← reportado pelo LLMProvider
    - request_id         ← gerado pelo Orchestrator para rastreabilidade fim-a-fim
    """
    # Conteúdo principal
    conteudo_markdown: str
    user_story_nome: str

    # Rastreabilidade de pipeline
    secoes_presentes: list[str] = field(default_factory=list)
    secoes_ausentes: list[str] = field(default_factory=list)

    # Qualidade
    confidence_score: float = 0.0
    completo: bool = True
    validacoes: list[dict] = field(default_factory=list)

    # Auditoria
    modelo_usado: str | None = None
    tokens_consumidos: int | None = None
    latencia_ms: float | None = None
    request_id: str | None = None
    timestamp: str | None = None

    # Status
    success: bool = True
    error_message: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "tipo": "analise_us",
            "success": self.success,
            "user_story_nome": self.user_story_nome,
            "confidence_score": self.confidence_score,
            "completo": self.completo,
            "secoes_presentes": self.secoes_presentes,
            "secoes_ausentes": self.secoes_ausentes,
            "validacoes": self.validacoes,
            "modelo_usado": self.modelo_usado,
            "tokens_consumidos": self.tokens_consumidos,
            "latencia_ms": round(self.latencia_ms, 1) if self.latencia_ms else None,
            "request_id": self.request_id,
            "timestamp": self.timestamp,
            "error_message": self.error_message,
            "conteudo_markdown": self.conteudo_markdown,
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)
