import time
from dataclasses import dataclass

from app.domain.entities.requirement import Requirement
from app.domain.entities.rtm import QAArtefact
from app.domain.ports.llm_port import LLMPort, LLMError
from app.domain.ports.knowledge_port import RetrievalPort


@dataclass
class DesignTestsRequest:
    requirement: Requirement
    include_automation_hints: bool = True
    temperature: float = 0.3
    max_tokens: int = 4000


@dataclass
class DesignTestsResponse:
    artefact: QAArtefact
    success: bool
    error_message: str | None = None


class DesignTests:
    """
    Use case: Geração detalhada de casos de teste com passos, dados e automação.
    Distinto do GenerateRTM — foca nos TCs individualmente (passos, pré-condições,
    dados de teste, resultado esperado, prioridade, automação sugerida).
    GenerateRTM foca na tabela bidirecional RN→CA→CT.
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

    def execute(self, request: DesignTestsRequest) -> DesignTestsResponse:
        start = time.monotonic()
        us = request.requirement

        try:
            context_chunks = []
            if self._retrieval:
                context_chunks = self._retrieval.search(
                    query=f"casos de teste design {us.nome}",
                    top_k=3,
                )

            messages = self._prompt_builder.build_design_tests(
                requirement=us,
                include_automation_hints=request.include_automation_hints,
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
                tipo="design_tests",
                user_story_nome=us.nome,
                completo=True,
                modelo_usado=llm_response.model,
                tokens_consumidos=llm_response.tokens_total,
                latencia_ms=latencia_ms,
            )

            return DesignTestsResponse(artefact=artefact, success=True)

        except LLMError as e:
            return DesignTestsResponse(
                artefact=QAArtefact(
                    conteudo_markdown="",
                    tipo="design_tests",
                    user_story_nome=us.nome,
                    completo=False,
                ),
                success=False,
                error_message=str(e),
            )
