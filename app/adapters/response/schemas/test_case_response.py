from __future__ import annotations
import json
from dataclasses import dataclass, field
from typing import Any


@dataclass
class TestCaseResponse:
    """
    DTO tipado para saída de criação de nova User Story com análise completa.
    Contém Parte A (US gerada) + Parte B (análise), separadas para consumo por canal.

    Rastreabilidade:
    - conteudo_markdown  ← gerado pelo CreateUserStory use case
    - parte_a / parte_b  ← split do markdown após geração (best-effort)
    - confidence_score   ← agregado pelo ConfidenceAggregator
    """
    # Conteúdo principal
    conteudo_markdown: str
    feature_titulo: str

    # Split Parte A / Parte B (extraídos do markdown gerado)
    parte_a_user_story: str = ""     # Feature + Como/Quero/Para + RN + CA
    parte_b_analise: str = ""        # Seções 1–9 + Recomendações

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
            "tipo": "us_nova",
            "success": self.success,
            "feature_titulo": self.feature_titulo,
            "confidence_score": self.confidence_score,
            "completo": self.completo,
            "parte_a_user_story": self.parte_a_user_story,
            "parte_b_analise": self.parte_b_analise,
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
