from __future__ import annotations
import json
import re
from dataclasses import dataclass, field
from typing import Any


@dataclass
class DesignTestsResponse:
    """
    DTO tipado para saída de design detalhado de casos de teste.
    Contrato estável — independente de LLM ou prompt.
    """
    conteudo_markdown: str
    user_story_nome: str
    total_casos: int | None = None
    casos_positivos: int = 0
    casos_negativos: int = 0
    confidence_score: float = 0.0
    validacoes: list[dict] = field(default_factory=list)
    modelo_usado: str | None = None
    tokens_consumidos: int | None = None
    latencia_ms: float | None = None
    request_id: str | None = None
    timestamp: str | None = None
    success: bool = True
    error_message: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "tipo": "design_tests",
            "success": self.success,
            "user_story_nome": self.user_story_nome,
            "total_casos": self.total_casos,
            "casos_positivos": self.casos_positivos,
            "casos_negativos": self.casos_negativos,
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
