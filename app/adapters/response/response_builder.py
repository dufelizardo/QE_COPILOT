from __future__ import annotations

import re
import unicodedata
from datetime import datetime
from pathlib import Path
from typing import Union

from app.domain.entities.rtm import QAArtefact
from app.adapters.validators.validator_chain import ChainResult
from app.adapters.response.confidence_aggregator import ConfidenceAggregator
from app.adapters.response.schemas.requirement_response import RequirementAnalysisResponse
from app.adapters.response.schemas.rtm_response import RTMResponse
from app.adapters.response.schemas.test_case_response import TestCaseResponse
from app.adapters.response.schemas.design_tests_response import DesignTestsResponse

AnyResponse = Union[
    RequirementAnalysisResponse,
    RTMResponse,
    TestCaseResponse,
    DesignTestsResponse,
]

_REQUIRED_SECTIONS = [
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


class ResponseBuilder:
    """
    Monta o DTO tipado final a partir do artefato validado + ChainResult.
    Seleciona o schema correto pelo tipo de artefato.
    Delega agregação de score ao ConfidenceAggregator.
    Extrai metadados estruturados do Markdown.
    """

    def __init__(self):
        self._agg_analysis = ConfidenceAggregator.for_analysis()
        self._agg_rtm = ConfidenceAggregator.for_rtm()
        self._agg_default = ConfidenceAggregator()

    def build(
        self,
        chain_result: ChainResult,
        request_id: str | None = None,
        success: bool = True,
    ) -> AnyResponse:
        artefact = chain_result.artefact
        tipo = artefact.tipo
        timestamp = datetime.utcnow().isoformat() + "Z"

        validacoes = [
            {
                "validator": r.validator_name,
                "passed": r.passed,
                "score": r.score,
                "message": r.message,
            }
            for r in chain_result.results
        ]

        if tipo == "analise_us":
            return self._build_requirement(artefact, chain_result, validacoes, request_id, timestamp, success)
        elif tipo == "rtm":
            return self._build_rtm(artefact, chain_result, validacoes, request_id, timestamp, success)
        elif tipo == "design_tests":
            return self._build_design_tests(artefact, chain_result, validacoes, request_id, timestamp, success)
        else:  # us_nova
            return self._build_test_case(artefact, chain_result, validacoes, request_id, timestamp, success)

    def _build_requirement(self, artefact, chain_result, validacoes, request_id, timestamp, success):
        score = self._agg_analysis.aggregate(chain_result)
        secoes_ausentes = [s for s in _REQUIRED_SECTIONS if s not in artefact.secoes_presentes]
        return RequirementAnalysisResponse(
            conteudo_markdown=artefact.conteudo_markdown,
            user_story_nome=artefact.user_story_nome,
            secoes_presentes=artefact.secoes_presentes,
            secoes_ausentes=secoes_ausentes,
            confidence_score=score.composite,
            completo=artefact.completo,
            validacoes=validacoes,
            modelo_usado=artefact.modelo_usado,
            tokens_consumidos=artefact.tokens_consumidos,
            latencia_ms=artefact.latencia_ms,
            request_id=request_id,
            timestamp=timestamp,
            success=success and chain_result.passed,
        )

    def _build_rtm(self, artefact, chain_result, validacoes, request_id, timestamp, success):
        score = self._agg_rtm.aggregate(chain_result)
        total_tcs, rns, cas = self._extract_rtm_metadata(artefact.conteudo_markdown)
        return RTMResponse(
            conteudo_markdown=artefact.conteudo_markdown,
            user_story_nome=artefact.user_story_nome,
            total_tcs=total_tcs,
            rns_cobertas=rns,
            cas_cobertos=cas,
            confidence_score=score.composite,
            validacoes=validacoes,
            modelo_usado=artefact.modelo_usado,
            tokens_consumidos=artefact.tokens_consumidos,
            latencia_ms=artefact.latencia_ms,
            request_id=request_id,
            timestamp=timestamp,
            success=success and chain_result.passed,
        )

    def _build_design_tests(self, artefact, chain_result, validacoes, request_id, timestamp, success):
        score = self._agg_rtm.aggregate(chain_result)
        total, pos, neg = self._extract_design_tests_metadata(artefact.conteudo_markdown)
        return DesignTestsResponse(
            conteudo_markdown=artefact.conteudo_markdown,
            user_story_nome=artefact.user_story_nome,
            total_casos=total,
            casos_positivos=pos,
            casos_negativos=neg,
            confidence_score=score.composite,
            validacoes=validacoes,
            modelo_usado=artefact.modelo_usado,
            tokens_consumidos=artefact.tokens_consumidos,
            latencia_ms=artefact.latencia_ms,
            request_id=request_id,
            timestamp=timestamp,
            success=success and chain_result.passed,
        )

    def _build_test_case(self, artefact, chain_result, validacoes, request_id, timestamp, success):
        score = self._agg_default.aggregate(chain_result)
        parte_a, parte_b = self._split_partes(artefact.conteudo_markdown)
        return TestCaseResponse(
            conteudo_markdown=artefact.conteudo_markdown,
            feature_titulo=artefact.user_story_nome,
            parte_a_user_story=parte_a,
            parte_b_analise=parte_b,
            confidence_score=score.composite,
            completo=artefact.completo,
            validacoes=validacoes,
            modelo_usado=artefact.modelo_usado,
            tokens_consumidos=artefact.tokens_consumidos,
            latencia_ms=artefact.latencia_ms,
            request_id=request_id,
            timestamp=timestamp,
            success=success and chain_result.passed,
        )

    # ── Extratores ──────────────────────────────────────────────────────────

    @staticmethod
    def _extract_rtm_metadata(markdown: str) -> tuple[int | None, list[str], list[str]]:
        total_tcs: int | None = None
        m = re.search(r"total de casos[:\s]+(\d+)", markdown, re.IGNORECASE)
        if m:
            total_tcs = int(m.group(1))
        rns = sorted(set(re.findall(r"RN-\d+(?:\.\d+)?", markdown, re.IGNORECASE)))
        cas = sorted(set(re.findall(r"CA-\d+(?:[.\w]+)?", markdown, re.IGNORECASE)))
        return total_tcs, rns, cas

    @staticmethod
    def _extract_design_tests_metadata(markdown: str) -> tuple[int | None, int, int]:
        tcs = re.findall(r"###\s+CT-\d+", markdown, re.IGNORECASE)
        total = len(tcs) if tcs else None
        pos = len(re.findall(r"\*\*Tipo\*\*:\s*Positivo", markdown, re.IGNORECASE))
        neg = len(re.findall(r"\*\*Tipo\*\*:\s*Negativo", markdown, re.IGNORECASE))
        return total, pos, neg

    @staticmethod
    def _split_partes(markdown: str) -> tuple[str, str]:
        marker = re.search(
            r"(##\s*Parte\s*B|##\s*\d+️⃣\s*Análise de Negócio)",
            markdown, re.IGNORECASE,
        )
        if marker:
            return markdown[: marker.start()].strip(), markdown[marker.start():].strip()
        return markdown, ""

    def save_markdown(self, response: AnyResponse, path: str | None = None, base_dir: str = ".") -> str:
        nome = getattr(response, "user_story_nome", None) or getattr(response, "feature_titulo", "artefato")
        if path:
            file_path = Path(path)
        else:
            slug = self._slugify(nome)
            ts = datetime.now().strftime("%Y%m%d-%H%M")
            file_path = Path(base_dir) / "log" / "analise" / f"analise-{slug}-{ts}.md"
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(response.conteudo_markdown)
        return str(file_path)

    @staticmethod
    def _slugify(text: str) -> str:
        normalized = unicodedata.normalize("NFD", text.lower())
        no_accents = "".join(c for c in normalized if unicodedata.category(c) != "Mn")
        return re.sub(r"[^a-z0-9\-]+", "-", no_accents).strip("-")
