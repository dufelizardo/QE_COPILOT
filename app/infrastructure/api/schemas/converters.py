from __future__ import annotations

from fastapi import Request
from app.adapters.orchestration.orchestrator import OrchestratorResult
from app.adapters.response.schemas.requirement_response import RequirementAnalysisResponse
from app.adapters.response.schemas.rtm_response import RTMResponse
from app.adapters.response.schemas.test_case_response import TestCaseResponse
from app.adapters.response.schemas.design_tests_response import DesignTestsResponse
from app.adapters.response.channel_formatter import OutputChannel
from app.infrastructure.api.schemas.api_schemas import (
    ValidationDetail, AnalyzeUSResponse, GenerateRTMAPIResponse,
    CreateUSAPIResponse, DesignTestsAPIResponse,
)


def _channel(channel_str: str) -> OutputChannel:
    mapping = {"json": OutputChannel.JSON, "markdown": OutputChannel.MARKDOWN, "csv": OutputChannel.CSV}
    return mapping.get(channel_str.lower(), OutputChannel.JSON)


def _validacoes(result: OrchestratorResult) -> list[ValidationDetail]:
    raw = result.response.validacoes if result.response else []
    return [ValidationDetail(**v) for v in raw]


def result_to_analyze_response(result: OrchestratorResult) -> AnalyzeUSResponse:
    r = result.response
    if not isinstance(r, RequirementAnalysisResponse):
        return AnalyzeUSResponse(
            success=False, tipo="analise_us", confidence_score=0,
            modelo_usado=None, tokens_consumidos=None, latencia_ms=None,
            request_id=result.request_id, timestamp=None, validacoes=[],
            error_message=result.error_message, conteudo_markdown="",
            user_story_nome="", secoes_presentes=[], secoes_ausentes=[], completo=False,
        )
    return AnalyzeUSResponse(
        success=r.success, tipo="analise_us",
        confidence_score=r.confidence_score,
        modelo_usado=r.modelo_usado, tokens_consumidos=r.tokens_consumidos,
        latencia_ms=r.latencia_ms, request_id=r.request_id, timestamp=r.timestamp,
        validacoes=_validacoes(result), error_message=r.error_message,
        conteudo_markdown=r.conteudo_markdown,
        user_story_nome=r.user_story_nome,
        secoes_presentes=r.secoes_presentes, secoes_ausentes=r.secoes_ausentes,
        completo=r.completo,
    )


def result_to_design_tests_response(result: OrchestratorResult) -> DesignTestsAPIResponse:
    r = result.response
    if not isinstance(r, DesignTestsResponse):
        return DesignTestsAPIResponse(
            success=False, tipo="design_tests", confidence_score=0,
            modelo_usado=None, tokens_consumidos=None, latencia_ms=None,
            request_id=result.request_id, timestamp=None, validacoes=[],
            error_message=result.error_message, conteudo_markdown="",
            user_story_nome="", total_casos=None, casos_positivos=0, casos_negativos=0,
        )
    return DesignTestsAPIResponse(
        success=r.success, tipo="design_tests",
        confidence_score=r.confidence_score,
        modelo_usado=r.modelo_usado, tokens_consumidos=r.tokens_consumidos,
        latencia_ms=r.latencia_ms, request_id=r.request_id, timestamp=r.timestamp,
        validacoes=_validacoes(result), error_message=r.error_message,
        conteudo_markdown=r.conteudo_markdown,
        user_story_nome=r.user_story_nome,
        total_casos=r.total_casos, casos_positivos=r.casos_positivos,
        casos_negativos=r.casos_negativos,
    )


def result_to_rtm_response(result: OrchestratorResult) -> GenerateRTMAPIResponse:
    r = result.response
    if not isinstance(r, RTMResponse):
        return GenerateRTMAPIResponse(
            success=False, tipo="rtm", confidence_score=0,
            modelo_usado=None, tokens_consumidos=None, latencia_ms=None,
            request_id=result.request_id, timestamp=None, validacoes=[],
            error_message=result.error_message, conteudo_markdown="",
            user_story_nome="", total_tcs=None, rns_cobertas=[], cas_cobertos=[],
        )
    return GenerateRTMAPIResponse(
        success=r.success, tipo="rtm",
        confidence_score=r.confidence_score,
        modelo_usado=r.modelo_usado, tokens_consumidos=r.tokens_consumidos,
        latencia_ms=r.latencia_ms, request_id=r.request_id, timestamp=r.timestamp,
        validacoes=_validacoes(result), error_message=r.error_message,
        conteudo_markdown=r.conteudo_markdown,
        user_story_nome=r.user_story_nome,
        total_tcs=r.total_tcs, rns_cobertas=r.rns_cobertas, cas_cobertos=r.cas_cobertos,
    )


def result_to_create_us_response(result: OrchestratorResult) -> CreateUSAPIResponse:
    r = result.response
    if not isinstance(r, TestCaseResponse):
        return CreateUSAPIResponse(
            success=False, tipo="us_nova", confidence_score=0,
            modelo_usado=None, tokens_consumidos=None, latencia_ms=None,
            request_id=result.request_id, timestamp=None, validacoes=[],
            error_message=result.error_message, conteudo_markdown="",
            feature_titulo="", parte_a_user_story="", parte_b_analise="", completo=False,
        )
    return CreateUSAPIResponse(
        success=r.success, tipo="us_nova",
        confidence_score=r.confidence_score,
        modelo_usado=r.modelo_usado, tokens_consumidos=r.tokens_consumidos,
        latencia_ms=r.latencia_ms, request_id=r.request_id, timestamp=r.timestamp,
        validacoes=_validacoes(result), error_message=r.error_message,
        conteudo_markdown=r.conteudo_markdown,
        feature_titulo=r.feature_titulo,
        parte_a_user_story=r.parte_a_user_story, parte_b_analise=r.parte_b_analise,
        completo=r.completo,
    )
