from __future__ import annotations

from fastapi import APIRouter, Request, HTTPException
from app.adapters.agents.qa_agent import QAIntent
from app.adapters.orchestration.orchestrator import OrchestratorRequest
from app.adapters.response.channel_formatter import OutputChannel
from app.domain.entities.requirement import Requirement
from app.infrastructure.api.schemas.api_schemas import (
    AnalyzeUSRequest, AnalyzeUSResponse,
    DesignTestsRequest, DesignTestsAPIResponse,
    GenerateRTMRequest, GenerateRTMAPIResponse,
    CreateUSRequest, CreateUSAPIResponse,
)
from app.infrastructure.api.schemas.converters import (
    result_to_analyze_response, result_to_design_tests_response,
    result_to_rtm_response, result_to_create_us_response, _channel,
)

router = APIRouter(prefix="/qa", tags=["QA"])


def _get_orchestrator(request: Request):
    return request.app.state.container.orchestrator


def _get_request_id(request: Request) -> str:
    return getattr(request.state, "request_id", None)


@router.post("/analyze", response_model=AnalyzeUSResponse, summary="Análise completa de User Story")
async def analyze_user_story(body: AnalyzeUSRequest, request: Request):
    """
    Gera análise completa (seções 1–8 + Recomendações) de uma User Story existente.
    """
    req_input = body.user_story
    req = Requirement(
        nome=req_input.nome,
        descricao=req_input.descricao,
        regras_negocio=req_input.regras_negocio,
        criterios_aceite=req_input.criterios_aceite,
    )
    result = _get_orchestrator(request).run(OrchestratorRequest(
        intent=QAIntent.ANALYZE_US,
        requirement=req,
        channel=_channel(body.channel),
        include_gherkin=body.include_gherkin,
        temperature=body.temperature,
        max_tokens=body.max_tokens,
        request_id=_get_request_id(request),
    ))
    return result_to_analyze_response(result)


@router.post("/design-tests", response_model=DesignTestsAPIResponse, summary="Design detalhado de casos de teste")
async def design_tests(body: DesignTestsRequest, request: Request):
    """
    Gera casos de teste detalhados com passos, dados de teste e sugestões de automação.
    """
    req_input = body.user_story
    req = Requirement(
        nome=req_input.nome,
        descricao=req_input.descricao,
        regras_negocio=req_input.regras_negocio,
        criterios_aceite=req_input.criterios_aceite,
    )
    result = _get_orchestrator(request).run(OrchestratorRequest(
        intent=QAIntent.DESIGN_TESTS,
        requirement=req,
        channel=_channel(body.channel),
        temperature=body.temperature,
        max_tokens=body.max_tokens,
        request_id=_get_request_id(request),
    ))
    return result_to_design_tests_response(result)


@router.post("/generate-rtm", response_model=GenerateRTMAPIResponse, summary="RTM bidirecional + cenários")
async def generate_rtm(body: GenerateRTMRequest, request: Request):
    """
    Gera Tabela de Cenários de Teste + RTM Bidirecional (RN → CA → CT).
    """
    req_input = body.user_story
    req = Requirement(
        nome=req_input.nome,
        descricao=req_input.descricao,
        regras_negocio=req_input.regras_negocio,
        criterios_aceite=req_input.criterios_aceite,
    )
    result = _get_orchestrator(request).run(OrchestratorRequest(
        intent=QAIntent.GENERATE_RTM,
        requirement=req,
        channel=_channel(body.channel),
        temperature=body.temperature,
        max_tokens=body.max_tokens,
        request_id=_get_request_id(request),
    ))
    return result_to_rtm_response(result)


@router.post("/create-user-story", response_model=CreateUSAPIResponse, summary="Cria nova US + análise completa")
async def create_user_story(body: CreateUSRequest, request: Request):
    """
    Cria uma nova User Story do zero (Parte A) e gera análise completa (Parte B).
    """
    req = Requirement(
        nome=body.feature_titulo,
        descricao=body.objetivo_usuario,
        regras_negocio=body.regras_negocio,
        criterios_aceite=body.criterios_aceite,
        feature_titulo=body.feature_titulo,
        persona=body.persona,
        objetivo_usuario=body.objetivo_usuario,
        beneficio=body.beneficio,
        contexto=body.contexto,
        restricoes=body.restricoes,
        nfr=body.nfr,
        integracoes=body.integracoes,
        dados_exemplo=body.dados_exemplo,
        dependencias=body.dependencias,
        riscos=body.riscos,
        perguntas_abertas=body.perguntas_abertas,
    )
    result = _get_orchestrator(request).run(OrchestratorRequest(
        intent=QAIntent.CREATE_US,
        requirement=req,
        channel=_channel(body.channel),
        include_gherkin=body.include_gherkin,
        temperature=body.temperature,
        max_tokens=body.max_tokens,
        arquivo_md=body.arquivo_md,
        request_id=_get_request_id(request),
    ))
    return result_to_create_us_response(result)
