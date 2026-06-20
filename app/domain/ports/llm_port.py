from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class LLMMessage:
    role: str    # "system" | "user" | "assistant"
    content: str


@dataclass
class LLMResponse:
    content: str
    model: str
    tokens_prompt: Optional[int] = None
    tokens_completion: Optional[int] = None
    latencia_ms: Optional[float] = None

    @property
    def tokens_total(self) -> Optional[int]:
        if self.tokens_prompt is not None and self.tokens_completion is not None:
            return self.tokens_prompt + self.tokens_completion
        return None


class LLMPort(ABC):
    """
    Porta de saída para qualquer provider LLM.
    Implementações concretas ficam em infrastructure/llm/.
    Os use cases dependem APENAS desta interface — nunca de OpenAI, Gemini, etc.
    """

    @abstractmethod
    def complete(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.2,
        max_tokens: int = 2000,
    ) -> LLMResponse:
        """
        Envia uma lista de mensagens e retorna a resposta do modelo.
        Exceções devem ser normalizadas para LLMError antes de subir.
        """
        ...

    @abstractmethod
    def health_check(self) -> bool:
        """Verifica se o provider está acessível. Retorna True se OK."""
        ...


class LLMError(Exception):
    """
    Exceção normalizada de todos os providers.
    Nenhum caller precisa conhecer HTTPError, RequestException, etc.
    """
    def __init__(self, message: str, status_code: Optional[int] = None, provider: str = "unknown"):
        super().__init__(message)
        self.status_code = status_code
        self.provider = provider
