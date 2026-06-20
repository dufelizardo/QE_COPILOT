import logging
import json
import time
from datetime import datetime
from typing import Any


class StructuredLogger:
    """
    Logger estruturado em JSON para o QE Copilot.
    Registra latência, tokens, modelo e resultado de cada chamada.
    Alimenta o sistema de observabilidade sem que os use cases precisem saber disso.
    """

    def __init__(self, name: str, level: str = "INFO"):
        self._logger = logging.getLogger(name)
        self._logger.setLevel(getattr(logging, level.upper(), logging.INFO))

        if not self._logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter("%(message)s"))
            self._logger.addHandler(handler)

    def _emit(self, level: str, event: str, **kwargs: Any) -> None:
        record = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": level,
            "event": event,
            **kwargs,
        }
        msg = json.dumps(record, ensure_ascii=False)
        getattr(self._logger, level.lower(), self._logger.info)(msg)

    def info(self, event: str, **kwargs: Any) -> None:
        self._emit("INFO", event, **kwargs)

    def warning(self, event: str, **kwargs: Any) -> None:
        self._emit("WARNING", event, **kwargs)

    def error(self, event: str, **kwargs: Any) -> None:
        self._emit("ERROR", event, **kwargs)

    def llm_call(
        self,
        use_case: str,
        model: str,
        tokens: int | None,
        latencia_ms: float | None,
        success: bool,
        us_nome: str = "",
    ) -> None:
        self._emit(
            "INFO" if success else "ERROR",
            "llm_call",
            use_case=use_case,
            model=model,
            tokens=tokens,
            latencia_ms=round(latencia_ms, 1) if latencia_ms else None,
            success=success,
            us_nome=us_nome,
        )

    def validation(
        self,
        us_nome: str,
        passed: bool,
        confidence_score: float,
        failed_validators: list[str],
    ) -> None:
        self._emit(
            "INFO" if passed else "WARNING",
            "validation",
            us_nome=us_nome,
            passed=passed,
            confidence_score=confidence_score,
            failed_validators=failed_validators,
        )


# Instância padrão — importar diretamente quando necessário
logger = StructuredLogger("qe_copilot")
