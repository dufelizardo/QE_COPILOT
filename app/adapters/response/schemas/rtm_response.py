from __future__ import annotations
import json
from dataclasses import dataclass, field
from typing import Any


@dataclass
class RTMResponse:
    """
    DTO tipado para saída de RTM bidirecional + cenários de teste.
    Contrato estável com o caller — independente de LLM ou prompt.

    Rastreabilidade:
    - conteudo_markdown  ← gerado pelo GenerateRTM use case
    - total_tcs          ← extraído do checklist final do prompt
    - confidence_score   ← agregado pelo ConfidenceAggregator
    - validacoes         ← produzidas pelo ValidatorChain
    """
    # Conteúdo principal
    conteudo_markdown: str
    user_story_nome: str

    # Metadados extraídos do conteúdo (best-effort via parsing leve)
    total_tcs: int | None = None
    rns_cobertas: list[str] = field(default_factory=list)
    cas_cobertos: list[str] = field(default_factory=list)

    # Qualidade
    confidence_score: float = 0.0
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
            "tipo": "rtm",
            "success": self.success,
            "user_story_nome": self.user_story_nome,
            "total_tcs": self.total_tcs,
            "rns_cobertas": self.rns_cobertas,
            "cas_cobertos": self.cas_cobertos,
            "confidence_score": self.confidence_score,
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
