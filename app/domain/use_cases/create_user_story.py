import time
from dataclasses import dataclass

from app.domain.entities.requirement import Requirement
from app.domain.entities.rtm import QAArtefact
from app.domain.ports.llm_port import LLMPort, LLMError
from app.domain.ports.knowledge_port import RetrievalPort


@dataclass
class CreateUserStoryRequest:
    requirement: Requirement           # Preenchida com feature_titulo, persona, objetivo, beneficio
    include_gherkin: bool = False
    temperature: float = 0.2
    max_tokens: int = 3200


@dataclass
class CreateUserStoryResponse:
    artefact: QAArtefact
    success: bool
    error_message: str | None = None


class CreateUserStory:
    """
    Use case: Criação de nova User Story + análise completa (Parte A + Parte B).
    Equivale ao gerar_user_story_nova_com_analise do código legado.

    Valida que os insumos mínimos estão presentes antes de chamar o LLM.
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

    def execute(self, request: CreateUserStoryRequest) -> CreateUserStoryResponse:
        us = request.requirement

        # Validação de domínio — antes de qualquer chamada LLM
        if not us.is_nova():
            return CreateUserStoryResponse(
                artefact=QAArtefact(
                    conteudo_markdown="",
                    tipo="us_nova",
                    user_story_nome=us.feature_titulo or "desconhecida",
                    completo=False,
                ),
                success=False,
                error_message=(
                    "Para criar uma nova US, forneça: feature_titulo, persona e objetivo_usuario."
                ),
            )

        start = time.monotonic()

        try:
            context_chunks = []
            if self._retrieval:
                context_chunks = self._retrieval.search(
                    query=f"{us.feature_titulo} {us.objetivo_usuario}",
                    top_k=3,
                )

            messages = self._prompt_builder.build_us_nova_com_analise(
                requirement=us,
                include_gherkin=request.include_gherkin,
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
                tipo="us_nova",
                user_story_nome=us.feature_titulo or "nova_us",
                completo=True,
                modelo_usado=llm_response.model,
                tokens_consumidos=llm_response.tokens_total,
                latencia_ms=latencia_ms,
            )

            return CreateUserStoryResponse(artefact=artefact, success=True)

        except LLMError as e:
            return CreateUserStoryResponse(
                artefact=QAArtefact(
                    conteudo_markdown="",
                    tipo="us_nova",
                    user_story_nome=us.feature_titulo or "desconhecida",
                    completo=False,
                ),
                success=False,
                error_message=str(e),
            )
