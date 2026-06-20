import time
from dataclasses import dataclass

from app.domain.entities.requirement import Requirement
from app.domain.entities.rtm import QAArtefact
from app.domain.ports.llm_port import LLMPort, LLMMessage, LLMError
from app.domain.ports.knowledge_port import RetrievalPort


@dataclass
class AnalyzeUserStoryRequest:
    requirement: Requirement
    include_gherkin: bool = False
    temperature: float = 0.2
    max_tokens: int = 2800


@dataclass
class AnalyzeUserStoryResponse:
    artefact: QAArtefact
    success: bool
    error_message: str | None = None


class AnalyzeUserStory:
    """
    Use case: Análise completa de uma User Story existente.
    Equivale ao que era gerar_analise_completa_e_salvar no código legado,
    mas agora desacoplado de provider, prompt e HTTP.

    Depende apenas de abstrações (Ports) — nunca de implementações concretas.
    O DI Container injeta as implementações em runtime.
    """

    # Seções obrigatórias na resposta — retiradas de _REQUIRED_SECTIONS do código legado
    REQUIRED_SECTIONS = [
        "Análise de Negócio",
        "Análise de Requisitos",
        "Análise de Critérios de Aceite",
        "Análise de Testabilidade",
        "Análise Técnica",
        "Análise de Riscos",
        "Análise de Dependências",
        "Análise de Rastreabilidade",
        "Recomendações Finais",
    ]

    def __init__(
        self,
        llm: LLMPort,
        prompt_builder,       # PromptBuilderPort — injetado pelo DI
        retrieval: RetrievalPort | None = None,
        logger=None,
    ):
        self._llm = llm
        self._prompt_builder = prompt_builder
        self._retrieval = retrieval
        self._logger = logger

    def execute(self, request: AnalyzeUserStoryRequest) -> AnalyzeUserStoryResponse:
        start = time.monotonic()
        us = request.requirement

        try:
            # 1. Recupera contexto relevante do RAG (se disponível)
            context_chunks = []
            if self._retrieval:
                context_chunks = self._retrieval.search(
                    query=f"{us.nome} {us.descricao}",
                    top_k=5,
                )

            # 2. Constrói as mensagens via PromptBuilder (adapter)
            messages = self._prompt_builder.build_analise_completa(
                requirement=us,
                include_gherkin=request.include_gherkin,
                context_chunks=context_chunks,
            )

            # 3. Chama o LLM via Port (sem saber qual provider é)
            llm_response = self._llm.complete(
                messages=messages,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
            )

            latencia_ms = (time.monotonic() - start) * 1000

            # 4. Verifica completude (lógica de domínio — fica aqui, não no adapter)
            secoes_presentes = self._detect_sections(llm_response.content)
            completo = len(secoes_presentes) >= len(self.REQUIRED_SECTIONS)

            artefact = QAArtefact(
                conteudo_markdown=llm_response.content,
                tipo="analise_us",
                user_story_nome=us.nome,
                secoes_presentes=secoes_presentes,
                completo=completo,
                modelo_usado=llm_response.model,
                tokens_consumidos=llm_response.tokens_total,
                latencia_ms=latencia_ms,
            )

            return AnalyzeUserStoryResponse(artefact=artefact, success=True)

        except LLMError as e:
            return AnalyzeUserStoryResponse(
                artefact=QAArtefact(
                    conteudo_markdown="",
                    tipo="analise_us",
                    user_story_nome=us.nome,
                    completo=False,
                ),
                success=False,
                error_message=str(e),
            )

    def _detect_sections(self, markdown: str) -> list[str]:
        """Detecta quais seções obrigatórias estão presentes no Markdown gerado."""
        import unicodedata

        def strip_accents(s: str) -> str:
            return "".join(
                c for c in unicodedata.normalize("NFD", s)
                if unicodedata.category(c) != "Mn"
            )

        base = strip_accents(markdown).lower()
        return [
            sec for sec in self.REQUIRED_SECTIONS
            if strip_accents(sec).lower() in base
        ]
