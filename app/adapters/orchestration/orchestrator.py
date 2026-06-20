from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Union

from app.adapters.agents.qa_agent import QAAgent, AgentRequest, QAIntent
from app.adapters.orchestration.failure_handler import FailureHandler, RetryConfig
from app.adapters.response.response_builder import ResponseBuilder
from app.adapters.response.channel_formatter import ChannelFormatter, OutputChannel
from app.adapters.response.schemas.requirement_response import RequirementAnalysisResponse
from app.adapters.response.schemas.rtm_response import RTMResponse
from app.adapters.response.schemas.test_case_response import TestCaseResponse
from app.adapters.validators.validator_chain import ValidatorChain
from app.domain.entities.requirement import Requirement
from app.observability.logger import StructuredLogger

AnyResponse = Union[RequirementAnalysisResponse, RTMResponse, TestCaseResponse]


@dataclass
class SessionContext:
    """
    Contexto de sessão mantido pelo Orchestrator.
    Armazena histórico de requests para suportar continuação (análise truncada).
    """
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    requests_count: int = 0
    last_us_nome: str = ""
    last_intent: QAIntent | None = None


@dataclass
class OrchestratorRequest:
    """Request de entrada para o Orchestrator — vindo do facade público."""
    intent: QAIntent
    requirement: Requirement
    channel: OutputChannel = OutputChannel.ROBOT
    include_gherkin: bool = False
    temperature: float = 0.2
    max_tokens: int = 2800
    arquivo_md: str | None = None
    request_id: str | None = None


@dataclass
class OrchestratorResult:
    """
    Resultado final do pipeline completo.
    Contém o DTO tipado + o conteúdo formatado para o canal solicitado.
    """
    response: AnyResponse
    formatted_output: str        # Pronto para entregar ao caller
    request_id: str
    success: bool
    error_message: str | None = None


class Orchestrator:
    """
    Coordena o pipeline completo de geração QA.

    Fluxo:
        OrchestratorRequest
            → detecta intent (já vem resolvida no MVP)
            → cria request_id de rastreabilidade
            → chama QAAgent com retry via FailureHandler
            → passa artefato pelo ValidatorChain
            → entrega ao ResponseBuilder → DTO tipado
            → formata pelo ChannelFormatter
            → persiste se arquivo_md informado
            → retorna OrchestratorResult

    Distinção com QAAgent:
    - Orchestrator: QUAL WORKFLOW e COMO entregar (canal, retry, persistência, rastreabilidade)
    - Agent: QUAL USE CASE chamar dentro do workflow
    """

    def __init__(
        self,
        agent: QAAgent,
        validator_chain: ValidatorChain,
        response_builder: ResponseBuilder,
        channel_formatter: ChannelFormatter,
        failure_handler: FailureHandler,
        logger: StructuredLogger,
    ):
        self._agent = agent
        self._validator_chain = validator_chain
        self._response_builder = response_builder
        self._channel_formatter = channel_formatter
        self._failure_handler = failure_handler
        self._logger = logger
        self._session = SessionContext()

    def run(self, request: OrchestratorRequest) -> OrchestratorResult:
        """
        Executa o pipeline completo. Nunca lança exceção para o caller —
        erros são encapsulados no OrchestratorResult.
        """
        request_id = request.request_id or str(uuid.uuid4())
        self._session.requests_count += 1
        self._session.last_us_nome = request.requirement.nome
        self._session.last_intent = request.intent

        self._logger.info(
            "orchestrator_start",
            request_id=request_id,
            intent=request.intent.value,
            us_nome=request.requirement.nome,
            channel=request.channel.value,
        )

        try:
            # 1. Chama Agent com retry via FailureHandler
            agent_request = AgentRequest(
                intent=request.intent,
                requirement=request.requirement,
                include_gherkin=request.include_gherkin,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
            )

            agent_result = self._failure_handler.with_retry(
                fn=lambda: self._agent.execute(agent_request),
                us_nome=request.requirement.nome,
                use_case_name=request.intent.value,
                should_retry=lambda r: not r.success,
            )

            if not agent_result.success:
                return self._error_result(
                    request_id=request_id,
                    message=agent_result.error_message or "Agent retornou falha.",
                    intent=request.intent,
                    us_nome=request.requirement.nome,
                )

            # 2. Valida o artefato gerado
            artefact = agent_result.use_case_response.artefact
            chain_result = self._validator_chain.run(artefact)

            self._logger.validation(
                us_nome=request.requirement.nome,
                passed=chain_result.passed,
                confidence_score=chain_result.confidence_score,
                failed_validators=chain_result.failed_validators,
            )

            # 3. Constrói o DTO tipado pelo tipo de artefato
            typed_response = self._response_builder.build(
                chain_result=chain_result,
                request_id=request_id,
                success=True,
            )

            # 4. Formata para o canal solicitado
            formatted = self._channel_formatter.format(typed_response, request.channel)

            # 5. Persiste se arquivo_md informado
            if request.arquivo_md:
                saved_path = self._response_builder.save_markdown(
                    typed_response, path=request.arquivo_md
                )
                self._logger.info("markdown_saved", path=saved_path, request_id=request_id)

            self._logger.llm_call(
                use_case=request.intent.value,
                model=artefact.modelo_usado or "unknown",
                tokens=artefact.tokens_consumidos,
                latencia_ms=artefact.latencia_ms,
                success=True,
                us_nome=request.requirement.nome,
            )

            return OrchestratorResult(
                response=typed_response,
                formatted_output=formatted,
                request_id=request_id,
                success=True,
            )

        except Exception as e:
            self._logger.error(
                "orchestrator_unhandled_error",
                request_id=request_id,
                error=str(e),
                us_nome=request.requirement.nome,
            )
            return self._error_result(
                request_id=request_id,
                message=str(e),
                intent=request.intent,
                us_nome=request.requirement.nome,
            )

    def _error_result(
        self,
        request_id: str,
        message: str,
        intent: QAIntent,
        us_nome: str,
    ) -> OrchestratorResult:
        """Cria resultado de erro compatível com o tipo de intent."""
        from app.domain.entities.rtm import QAArtefact
        from app.adapters.validators.validator_chain import ChainResult

        empty_artefact = QAArtefact(
            conteudo_markdown="",
            tipo=intent.value,
            user_story_nome=us_nome,
            completo=False,
        )
        empty_chain = ChainResult(
            passed=False,
            confidence_score=0.0,
            results=[],
            artefact=empty_artefact,
        )
        error_response = self._response_builder.build(
            chain_result=empty_chain,
            request_id=request_id,
            success=False,
        )
        error_response.success = False
        error_response.error_message = message

        return OrchestratorResult(
            response=error_response,
            formatted_output="",
            request_id=request_id,
            success=False,
            error_message=message,
        )
