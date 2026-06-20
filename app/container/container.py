from __future__ import annotations

from functools import cached_property
from typing import Literal

from app.config.settings import Settings
from app.domain.ports.knowledge_port import RetrievalPort, IngestionPort
from app.domain.ports.llm_port import LLMPort
from app.infrastructure.llm.b3gpt_provider import B3GPTProvider
from app.infrastructure.rag.rag_service import RAGService
from app.adapters.context.prompt_builder import PromptBuilder
from app.adapters.validators.validator_chain import (
    ValidatorChain, CompletenessValidator,
    ContentLengthValidator, TraceabilityValidator,
)
from app.adapters.response.response_builder import ResponseBuilder
from app.adapters.response.channel_formatter import ChannelFormatter
from app.adapters.agents.qa_agent import QAAgent
from app.adapters.orchestration.orchestrator import Orchestrator
from app.adapters.orchestration.failure_handler import FailureHandler, RetryConfig
from app.domain.use_cases.analyze_user_story import AnalyzeUserStory
from app.domain.use_cases.design_tests import DesignTests
from app.domain.use_cases.generate_rtm import GenerateRTM
from app.domain.use_cases.create_user_story import CreateUserStory
from app.observability.logger import StructuredLogger


class Container:
    """
    DI Container manual — monta o grafo de dependências completo.
    Usa cached_property: cada dependência é instanciada uma única vez (singleton por container).

    Substitui a injeção manual espalhada pela facade.
    Para trocar um componente (ex: FAISS → Qdrant), muda-se apenas aqui.

    Uso:
        container = Container(settings)
        orchestrator = container.orchestrator   # tudo já injetado
    """

    def __init__(self, settings: Settings):
        self._settings = settings

    # ── Observability ──────────────────────────────────────────────────────

    @cached_property
    def logger(self) -> StructuredLogger:
        return StructuredLogger("qe_copilot", level=self._settings.log_level)

    # ── Infrastructure — LLM ──────────────────────────────────────────────

    @cached_property
    def llm(self) -> LLMPort:
        return B3GPTProvider(
            token=self._settings.b3gpt_token,
            model_name=self._settings.b3gpt_model_name,
            base_url=self._settings.b3gpt_base_url,
            timeout=self._settings.b3gpt_timeout,
        )

    # ── Infrastructure — Vector Store ─────────────────────────────────────

    @cached_property
    def vector_store(self) -> RetrievalPort:
        """
        Seleciona o vector store pelo settings.vector_store_type.
        Lazy import — a lib só é carregada se o store for realmente usado.
        """
        store_type: Literal["chroma", "faiss", "qdrant"] = self._settings.vector_store_type
        path = self._settings.vector_store_path

        if store_type == "chroma":
            from app.infrastructure.vectorstores.chroma_store import ChromaStore
            return ChromaStore(persist_path=path)

        if store_type == "faiss":
            from app.infrastructure.vectorstores.faiss_store import FAISSStore
            return FAISSStore(persist_path=path)

        if store_type == "qdrant":
            from app.infrastructure.vectorstores.qdrant_store import QdrantStore
            return QdrantStore(
                host=getattr(self._settings, "qdrant_host", "localhost"),
                port=getattr(self._settings, "qdrant_port", 6333),
            )

        raise ValueError(f"vector_store_type desconhecido: {store_type!r}")

    # ── Infrastructure — RAG ──────────────────────────────────────────────

    @cached_property
    def rag_service(self) -> RAGService | None:
        """
        Retorna None se RAG estiver desabilitado (rag_enabled=False no settings).
        Use cases recebem None e simplesmente não fazem retrieval.
        """
        if not getattr(self._settings, "rag_enabled", False):
            return None
        store = self.vector_store
        return RAGService(retrieval=store, ingestion=store)

    # ── Adapters — Context ────────────────────────────────────────────────

    @cached_property
    def prompt_builder(self) -> PromptBuilder:
        return PromptBuilder()

    # ── Domain — Use Cases ────────────────────────────────────────────────

    @cached_property
    def analyze_us_uc(self) -> AnalyzeUserStory:
        return AnalyzeUserStory(
            llm=self.llm,
            prompt_builder=self.prompt_builder,
            retrieval=self.rag_service,
            logger=self.logger,
        )

    @cached_property
    def design_tests_uc(self) -> DesignTests:
        return DesignTests(
            llm=self.llm,
            prompt_builder=self.prompt_builder,
            retrieval=self.rag_service,
            logger=self.logger,
        )

    @cached_property
    def generate_rtm_uc(self) -> GenerateRTM:
        return GenerateRTM(
            llm=self.llm,
            prompt_builder=self.prompt_builder,
            retrieval=self.rag_service,
            logger=self.logger,
        )

    @cached_property
    def create_us_uc(self) -> CreateUserStory:
        return CreateUserStory(
            llm=self.llm,
            prompt_builder=self.prompt_builder,
            retrieval=self.rag_service,
            logger=self.logger,
        )

    # ── Adapters — Agent ──────────────────────────────────────────────────

    @cached_property
    def agent(self) -> QAAgent:
        return QAAgent(
            analyze_us=self.analyze_us_uc,
            design_tests=self.design_tests_uc,
            generate_rtm=self.generate_rtm_uc,
            create_us=self.create_us_uc,
        )

    # ── Adapters — Validation + Response ─────────────────────────────────

    @cached_property
    def validator_chain(self) -> ValidatorChain:
        return ValidatorChain([
            CompletenessValidator(),
            ContentLengthValidator(),
            TraceabilityValidator(),
        ])

    @cached_property
    def response_builder(self) -> ResponseBuilder:
        return ResponseBuilder()

    @cached_property
    def channel_formatter(self) -> ChannelFormatter:
        return ChannelFormatter()

    @cached_property
    def failure_handler(self) -> FailureHandler:
        return FailureHandler(
            config=RetryConfig(max_attempts=self._settings.max_retries),
            logger=self.logger,
        )

    # ── Orchestrator ──────────────────────────────────────────────────────

    @cached_property
    def orchestrator(self) -> Orchestrator:
        return Orchestrator(
            agent=self.agent,
            validator_chain=self.validator_chain,
            response_builder=self.response_builder,
            channel_formatter=self.channel_formatter,
            failure_handler=self.failure_handler,
            logger=self.logger,
        )
