from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Union

from app.domain.entities.requirement import Requirement
from app.domain.use_cases.analyze_user_story import AnalyzeUserStory, AnalyzeUserStoryRequest, AnalyzeUserStoryResponse
from app.domain.use_cases.design_tests import DesignTests, DesignTestsRequest, DesignTestsResponse
from app.domain.use_cases.generate_rtm import GenerateRTM, GenerateRTMRequest, GenerateRTMResponse
from app.domain.use_cases.create_user_story import CreateUserStory, CreateUserStoryRequest, CreateUserStoryResponse

UseCaseResponse = Union[
    AnalyzeUserStoryResponse,
    DesignTestsResponse,
    GenerateRTMResponse,
    CreateUserStoryResponse,
]


class QAIntent(str, Enum):
    ANALYZE_US = "analise_us"
    DESIGN_TESTS = "design_tests"
    GENERATE_RTM = "rtm"
    CREATE_US = "us_nova"


@dataclass
class AgentRequest:
    intent: QAIntent
    requirement: Requirement
    include_gherkin: bool = False
    include_automation_hints: bool = True
    temperature: float = 0.2
    max_tokens: int = 2800


@dataclass
class AgentResult:
    intent: QAIntent
    use_case_response: UseCaseResponse
    success: bool
    error_message: str | None = None


class QAAgent:
    """
    Decide qual use case chamar com base na intenção detectada pelo Orchestrator.
    Responsabilidade única: roteamento intent → use case.
    NÃO executa lógica de domínio. NÃO formata respostas.
    """

    def __init__(
        self,
        analyze_us: AnalyzeUserStory,
        design_tests: DesignTests,
        generate_rtm: GenerateRTM,
        create_us: CreateUserStory,
    ):
        self._analyze_us = analyze_us
        self._design_tests = design_tests
        self._generate_rtm = generate_rtm
        self._create_us = create_us

    def execute(self, request: AgentRequest) -> AgentResult:
        try:
            response = self._dispatch(request)
            return AgentResult(
                intent=request.intent,
                use_case_response=response,
                success=response.success,
                error_message=response.error_message if not response.success else None,
            )
        except Exception as e:
            return AgentResult(
                intent=request.intent,
                use_case_response=self._empty_response(request),
                success=False,
                error_message=f"Agent dispatch error: {e}",
            )

    def _dispatch(self, request: AgentRequest) -> UseCaseResponse:
        us = request.requirement

        if request.intent == QAIntent.ANALYZE_US:
            return self._analyze_us.execute(AnalyzeUserStoryRequest(
                requirement=us,
                include_gherkin=request.include_gherkin,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
            ))

        if request.intent == QAIntent.DESIGN_TESTS:
            return self._design_tests.execute(DesignTestsRequest(
                requirement=us,
                include_automation_hints=request.include_automation_hints,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
            ))

        if request.intent == QAIntent.GENERATE_RTM:
            return self._generate_rtm.execute(GenerateRTMRequest(
                requirement=us,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
            ))

        if request.intent == QAIntent.CREATE_US:
            return self._create_us.execute(CreateUserStoryRequest(
                requirement=us,
                include_gherkin=request.include_gherkin,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
            ))

        raise ValueError(f"QAAgent: intent não reconhecida: {request.intent}")

    @staticmethod
    def _empty_response(request: AgentRequest) -> AnalyzeUserStoryResponse:
        from app.domain.entities.rtm import QAArtefact
        return AnalyzeUserStoryResponse(
            artefact=QAArtefact(
                conteudo_markdown="",
                tipo=request.intent.value,
                user_story_nome=request.requirement.nome,
                completo=False,
            ),
            success=False,
            error_message="Agent dispatch error",
        )
