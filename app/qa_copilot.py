"""
QACopilot — Facade pública do Quality Engineering Copilot.
Compatível com Robot Framework. Usa o Container para DI.

Pipeline completo:
    Caller → QACopilot → Container → Orchestrator → QAAgent
          → Use Cases → LLMPort → B3GPTProvider
          → ValidatorChain → ResponseBuilder → DTO tipado
          → ChannelFormatter → output formatado
"""
from __future__ import annotations

from app.config.settings import Settings, get_settings
from app.container.container import Container
from app.adapters.agents.qa_agent import QAIntent
from app.adapters.orchestration.orchestrator import OrchestratorRequest
from app.adapters.response.channel_formatter import OutputChannel
from app.adapters.response.schemas.requirement_response import RequirementAnalysisResponse
from app.adapters.response.schemas.rtm_response import RTMResponse
from app.adapters.response.schemas.design_tests_response import DesignTestsResponse
from app.adapters.response.schemas.test_case_response import TestCaseResponse
from app.domain.entities.requirement import Requirement


class QACopilot:
    """
    Facade do QE Copilot — Robot Framework compatible.
    Constrói o Container e delega tudo ao Orchestrator.
    """

    def __init__(
        self,
        token: str,
        model_name: str,
        base_url: str | None = None,
        timeout: int = 60,
        log_level: str = "INFO",
        max_retries: int = 2,
        rag_enabled: bool = False,
        vector_store_type: str = "chroma",
        vector_store_path: str = "./data/vectorstore",
    ):
        settings = Settings(
            b3gpt_token=token,
            b3gpt_model_name=model_name,
            b3gpt_base_url=base_url or "https://api-b3gpt.b3.com.br/internal-api/b3gpt-llms/v1/openai",
            b3gpt_timeout=timeout,
            log_level=log_level,
            max_retries=max_retries,
            rag_enabled=rag_enabled,
            vector_store_type=vector_store_type,
            vector_store_path=vector_store_path,
        )
        self._container = Container(settings)

    @classmethod
    def from_settings(cls) -> "QACopilot":
        """Cria instância a partir de variáveis de ambiente / .env."""
        s = get_settings()
        return cls(
            token=s.b3gpt_token,
            model_name=s.b3gpt_model_name,
            base_url=s.b3gpt_base_url,
            timeout=s.b3gpt_timeout,
            log_level=s.log_level,
            max_retries=s.max_retries,
            rag_enabled=s.rag_enabled,
            vector_store_type=s.vector_store_type,
            vector_store_path=s.vector_store_path,
        )

    def _run(
        self,
        intent: QAIntent,
        user_story: UserStory,
        channel: OutputChannel = OutputChannel.ROBOT,
        include_gherkin: bool = False,
        include_automation_hints: bool = True,
        temperature: float = 0.2,
        max_tokens: int = 2800,
        arquivo_md: str | None = None,
    ) -> str:
        result = self._container.orchestrator.run(OrchestratorRequest(
            intent=intent,
            user_story=user_story,
            channel=channel,
            include_gherkin=include_gherkin,
            temperature=temperature,
            max_tokens=max_tokens,
            arquivo_md=arquivo_md,
        ))
        if not result.success:
            raise AssertionError(f"[QE Copilot] {result.error_message}")
        return result.formatted_output

    # ── Keywords públicas ─────────────────────────────────────────────────

    def gerar_analise_user_story(
        self, nome: str, descricao: str, rns: str, cas: str,
        include_gherkin: bool = False, temperature: float = 0.2, max_tokens: int = 2800,
    ) -> str:
        """Keyword RF: Análise completa de User Story existente. Retorna Markdown."""
        req = Requirement(nome=nome, descricao=descricao, regras_negocio=rns, criterios_aceite=cas)
        return self._run(QAIntent.ANALYZE_US, us, include_gherkin=include_gherkin,
                         temperature=temperature, max_tokens=max_tokens)

    def gerar_design_de_testes(
        self, nome: str, descricao: str, rns: str, cas: str,
        include_automation_hints: bool = True, temperature: float = 0.3, max_tokens: int = 4000,
    ) -> str:
        """Keyword RF: Casos de teste detalhados com passos e automação. Retorna Markdown."""
        req = Requirement(nome=nome, descricao=descricao, regras_negocio=rns, criterios_aceite=cas)
        return self._run(QAIntent.DESIGN_TESTS, us, include_automation_hints=include_automation_hints,
                         temperature=temperature, max_tokens=max_tokens)

    def gerar_rtm_e_cenarios_de_testes(
        self, nome: str, descricao: str, rns: str, cas: str,
        temperature: float = 0.3, max_tokens: int = 5000,
    ) -> str:
        """Keyword RF: RTM bidirecional + tabela de cenários. Retorna Markdown."""
        req = Requirement(nome=nome, descricao=descricao, regras_negocio=rns, criterios_aceite=cas)
        return self._run(QAIntent.GENERATE_RTM, us, temperature=temperature, max_tokens=max_tokens)

    def gerar_user_story_nova_com_analise(
        self, feature_titulo: str, persona: str, objetivo_usuario: str, beneficio: str,
        contexto: str = "", regras_negocio: str = "", criterios_aceite: str = "",
        restricoes: str = "", nfr: str = "", integracoes: str = "", dados_exemplo: str = "",
        dependencias: str = "", riscos: str = "", perguntas_abertas: str = "",
        include_gherkin: bool = False, arquivo_md: str | None = None,
        temperature: float = 0.2, max_tokens: int = 3200,
    ) -> str:
        """Keyword RF: Nova US + análise completa. Salva .md se arquivo_md informado."""
        req = Requirement(
            nome=feature_titulo, descricao=objetivo_usuario,
            regras_negocio=regras_negocio, criterios_aceite=criterios_aceite,
            feature_titulo=feature_titulo, persona=persona,
            objetivo_usuario=objetivo_usuario, beneficio=beneficio,
            contexto=contexto, restricoes=restricoes, nfr=nfr,
            integracoes=integracoes, dados_exemplo=dados_exemplo,
            dependencias=dependencias, riscos=riscos, perguntas_abertas=perguntas_abertas,
        )
        return self._run(QAIntent.CREATE_US, us, include_gherkin=include_gherkin,
                         temperature=temperature, max_tokens=max_tokens, arquivo_md=arquivo_md)

    def perguntar_simples(self, pergunta: str, temperature: float = 0.2, max_tokens: int = 200) -> str:
        """Keyword RF: Teste de conectividade."""
        from app.domain.ports.llm_port import LLMMessage
        try:
            resp = self._container.llm.complete(
                messages=[
                    LLMMessage(role="system", content="Você é um assistente simples e direto."),
                    LLMMessage(role="user", content=pergunta),
                ],
                temperature=temperature, max_tokens=max_tokens,
            )
            return resp.content
        except Exception as e:
            raise AssertionError(f"[QE Copilot] Erro em perguntar_simples: {e}")

    def health_check(self) -> bool:
        """Verifica conectividade com o LLM provider."""
        return self._container.llm.health_check()

    # ── Métodos tipados para uso programático / API ───────────────────────

    def gerar_analise_completa(self, nome: str, descricao: str, rns: str, cas: str,
                                include_gherkin: bool = False) -> RequirementAnalysisResponse:
        req = Requirement(nome=nome, descricao=descricao, regras_negocio=rns, criterios_aceite=cas)
        result = self._container.orchestrator.run(OrchestratorRequest(
            intent=QAIntent.ANALYZE_US, requirement=req, channel=OutputChannel.JSON,
            include_gherkin=include_gherkin,
        ))
        return result.response

    def gerar_rtm_completo(self, nome: str, descricao: str, rns: str, cas: str) -> RTMResponse:
        req = Requirement(nome=nome, descricao=descricao, regras_negocio=rns, criterios_aceite=cas)
        result = self._container.orchestrator.run(OrchestratorRequest(
            intent=QAIntent.GENERATE_RTM, requirement=req, channel=OutputChannel.JSON,
        ))
        return result.response

    def gerar_design_completo(self, nome: str, descricao: str, rns: str, cas: str) -> DesignTestsResponse:
        req = Requirement(nome=nome, descricao=descricao, regras_negocio=rns, criterios_aceite=cas)
        result = self._container.orchestrator.run(OrchestratorRequest(
            intent=QAIntent.DESIGN_TESTS, requirement=req, channel=OutputChannel.JSON,
        ))
        return result.response

    # ── RAG ───────────────────────────────────────────────────────────────

    def indexar_documento(self, conteudo: str, fonte: str, tipo: str = "documento") -> bool:
        """Indexa um documento no RAG. Requer rag_enabled=True."""
        if not self._container.rag_service:
            raise AssertionError("[QE Copilot] RAG não está habilitado. Configure rag_enabled=True.")
        return self._container.rag_service.ingest_document(conteudo=conteudo, fonte=fonte, tipo=tipo)
