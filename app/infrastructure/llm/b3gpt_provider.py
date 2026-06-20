import time
import json
import requests

from app.domain.ports.llm_port import LLMPort, LLMMessage, LLMResponse, LLMError


class B3GPTProvider(LLMPort):
    """
    Implementação concreta do LLMPort para o endpoint B3GPT.
    Encapsula toda a lógica HTTP — nenhuma outra camada conhece requests, headers ou URLs.

    Normaliza todas as exceções para LLMError antes de subir,
    garantindo que o use case nunca precise tratar HTTPError diretamente.
    """

    DEFAULT_BASE_URL = "https://api-b3gpt.b3.com.br/internal-api/b3gpt-llms/v1/openai"

    def __init__(
        self,
        token: str,
        model_name: str,
        base_url: str | None = None,
        timeout: int = 60,
    ):
        if not token:
            raise ValueError("B3GPTProvider: token (api-key) é obrigatório.")
        if not model_name:
            raise ValueError("B3GPTProvider: model_name é obrigatório.")

        self._token = token
        self._model_name = model_name
        self._base_url = base_url or self.DEFAULT_BASE_URL
        self._timeout = timeout

    @property
    def model_name(self) -> str:
        return self._model_name

    def complete(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.2,
        max_tokens: int = 2000,
    ) -> LLMResponse:
        """
        Envia mensagens ao endpoint B3GPT e retorna LLMResponse normalizado.
        Exceções de rede e HTTP são capturadas e relançadas como LLMError.
        """
        url = f"{self._base_url}/deployments/{self._model_name}/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "api-key": self._token,
        }
        body = {
            "messages": [
                {"role": msg.role, "content": msg.content}
                for msg in messages
            ],
            "temperature": float(temperature),
            "max_tokens": int(max_tokens),
        }

        start = time.monotonic()

        try:
            resp = requests.post(
                url,
                headers=headers,
                json=body,
                timeout=float(self._timeout),
            )
            resp.raise_for_status()

        except requests.HTTPError as e:
            status = getattr(resp, "status_code", None)
            text = getattr(resp, "text", "")
            raise LLMError(
                message=f"HTTP {status}: {text[:500]}",
                status_code=status,
                provider="b3gpt",
            ) from e

        except requests.Timeout:
            raise LLMError(
                message=f"Timeout após {self._timeout}s chamando B3GPT.",
                provider="b3gpt",
            )

        except requests.RequestException as e:
            raise LLMError(
                message=f"Erro de rede B3GPT: {e}",
                provider="b3gpt",
            ) from e

        latencia_ms = (time.monotonic() - start) * 1000

        try:
            data = resp.json()
        except ValueError:
            raise LLMError(
                message=f"Resposta não é JSON válida: {resp.text[:500]}",
                provider="b3gpt",
            )

        try:
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError) as e:
            raise LLMError(
                message=f"Estrutura de resposta inesperada: {json.dumps(data)[:500]}",
                provider="b3gpt",
            ) from e

        usage = data.get("usage", {})

        return LLMResponse(
            content=content,
            model=data.get("model", self._model_name),
            tokens_prompt=usage.get("prompt_tokens"),
            tokens_completion=usage.get("completion_tokens"),
            latencia_ms=latencia_ms,
        )

    def health_check(self) -> bool:
        """Faz uma chamada mínima para verificar conectividade."""
        try:
            resp = self.complete(
                messages=[
                    LLMMessage(role="user", content="ping"),
                ],
                max_tokens=5,
                temperature=0.0,
            )
            return bool(resp.content)
        except LLMError:
            return False
