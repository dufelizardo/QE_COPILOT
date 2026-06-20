from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Callable, TypeVar

from app.domain.ports.llm_port import LLMError
from app.observability.logger import StructuredLogger

T = TypeVar("T")


@dataclass
class RetryConfig:
    max_attempts: int = 3
    backoff_seconds: float = 1.5   # multiplicado a cada tentativa
    retry_on_validation_fail: bool = True


@dataclass
class FailureRecord:
    """Registro de falha para auditoria — equivalente ao Dead Letter."""
    us_nome: str
    use_case: str
    attempt: int
    error_type: str         # "llm_error" | "validation_fail" | "timeout"
    error_message: str
    timestamp: str


class FailureHandler:
    """
    Gerencia retry, fallback e registro de falhas do pipeline.

    Responsabilidades:
    - Tentar novamente em caso de LLMError ou validation fail (configurável)
    - Registrar cada falha com contexto suficiente para debug
    - Expor dead_letter para inspeção (base para persistência futura)

    Não tem lógica de domínio — decide QUANDO tentar novamente, não O QUE gerar.

    Uso:
        handler = FailureHandler(config=RetryConfig(max_attempts=2))
        result = handler.with_retry(
            fn=lambda: use_case.execute(request),
            us_nome="Login MFA",
            use_case_name="analise_us",
        )
    """

    def __init__(
        self,
        config: RetryConfig | None = None,
        logger: StructuredLogger | None = None,
    ):
        self._config = config or RetryConfig()
        self._logger = logger or StructuredLogger("qe_copilot.failure_handler")
        self.dead_letter: list[FailureRecord] = []

    def with_retry(
        self,
        fn: Callable[[], T],
        us_nome: str = "",
        use_case_name: str = "",
        should_retry: Callable[[T], bool] | None = None,
    ) -> T:
        """
        Executa fn() com retry automático.

        Args:
            fn: callable sem argumentos que executa o use case
            us_nome: nome da US (para logging)
            use_case_name: nome do use case (para logging)
            should_retry: função opcional que recebe o resultado e retorna True
                          se deve tentar novamente (ex: quando validation falhou)
        """
        last_error: Exception | None = None
        last_result = None

        for attempt in range(1, self._config.max_attempts + 1):
            try:
                result = fn()
                last_result = result

                # Verifica se o resultado merece retry (ex: validation fail)
                if should_retry and should_retry(result):
                    if not self._config.retry_on_validation_fail:
                        return result
                    self._record(
                        us_nome=us_nome,
                        use_case=use_case_name,
                        attempt=attempt,
                        error_type="validation_fail",
                        error_message="ValidatorChain rejeitou a resposta.",
                    )
                    if attempt < self._config.max_attempts:
                        self._wait(attempt)
                    continue

                return result

            except LLMError as e:
                last_error = e
                self._record(
                    us_nome=us_nome,
                    use_case=use_case_name,
                    attempt=attempt,
                    error_type="llm_error",
                    error_message=str(e),
                )
                if attempt < self._config.max_attempts:
                    self._wait(attempt)

            except Exception as e:
                # Erros inesperados: registra mas não retenta
                self._record(
                    us_nome=us_nome,
                    use_case=use_case_name,
                    attempt=attempt,
                    error_type="unexpected",
                    error_message=str(e),
                )
                raise

        # Esgotou tentativas — retorna último resultado disponível (pode ser falho)
        if last_result is not None:
            return last_result
        if last_error:
            raise last_error
        raise RuntimeError(f"FailureHandler: todas as {self._config.max_attempts} tentativas falharam.")

    def _wait(self, attempt: int) -> None:
        sleep_time = self._config.backoff_seconds * attempt
        self._logger.warning(
            "retry_backoff",
            attempt=attempt,
            sleep_seconds=sleep_time,
        )
        time.sleep(sleep_time)

    def _record(
        self,
        us_nome: str,
        use_case: str,
        attempt: int,
        error_type: str,
        error_message: str,
    ) -> None:
        from datetime import datetime
        record = FailureRecord(
            us_nome=us_nome,
            use_case=use_case,
            attempt=attempt,
            error_type=error_type,
            error_message=error_message,
            timestamp=datetime.utcnow().isoformat() + "Z",
        )
        self.dead_letter.append(record)
        self._logger.error(
            "pipeline_failure",
            us_nome=us_nome,
            use_case=use_case,
            attempt=attempt,
            error_type=error_type,
            error_message=error_message[:300],
        )
