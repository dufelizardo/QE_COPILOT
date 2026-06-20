import time
from dataclasses import dataclass

from app.domain.entities.requirement import Requirement
from app.domain.entities.rtm import QAArtefact
from app.domain.ports.llm_port import LLMPort, LLMError
from app.domain.ports.knowledge_port import RetrievalPort


@dataclass
class GenerateRTMRequest:
    requirement: Requirement
    temperature: float = 0.3
    max_tokens: int = 5000


@dataclass
class GenerateRTMResponse:
    artefact: QAArtefact
    success: bool
    error_message: str | None = None


class GenerateRTM:
    """
    Use case: Geração de Casos de Teste + Tabela de Cenários + RTM Bidirecional.
    Equivale ao gerar_rtm_e_cenarios_de_testes do código legado.

    Responsabilidade única: orquestrar a geração do RTM.
    Não formata, não valida saída, não conhece HTTP.
    """

    def __init__(
        self,
        llm: LLMPort,
        prompt_builder,
        retrieval: RetrievalPort | None = None,
        logger=None,
    ):
        self._llm = llm
        self._prompt_builder = prompt_builder
        self._retrieval = retrieval
        self._logger = logger

    def execute(self, request: GenerateRTMRequest) -> GenerateRTMResponse:
        start = time.monotonic()
        us = request.requirement

        try:
            context_chunks = []
            if self._retrieval:
                context_chunks = self._retrieval.search(
                    query=f"RTM casos de teste {us.nome}",
                    top_k=3,
                )

            messages = self._prompt_builder.build_rtm_e_cenarios(
                requirement=us,
                context_chunks=context_chunks,
            )

            llm_response = self._llm.complete(
                messages=messages,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
            )

            latencia_ms = (time.monotonic() - start) * 1000

            artefact = QAArtefact(
                conteudo_markdown=llm_response.content,
                tipo="rtm",
                user_story_nome=us.nome,
                completo=True,
                modelo_usado=llm_response.model,
                tokens_consumidos=llm_response.tokens_total,
                latencia_ms=latencia_ms,
            )

            return GenerateRTMResponse(artefact=artefact, success=True)

        except LLMError as e:
            return GenerateRTMResponse(
                artefact=QAArtefact(
                    conteudo_markdown="",
                    tipo="rtm",
                    user_story_nome=us.nome,
                    completo=False,
                ),
                success=False,
                error_message=str(e),
            )
