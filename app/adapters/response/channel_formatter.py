from __future__ import annotations
import csv
import io
import json
import re
from enum import Enum
from typing import Any, Union

from app.adapters.response.schemas.requirement_response import RequirementAnalysisResponse
from app.adapters.response.schemas.rtm_response import RTMResponse
from app.adapters.response.schemas.test_case_response import TestCaseResponse

AnyResponse = Union[RequirementAnalysisResponse, RTMResponse, TestCaseResponse]


class OutputChannel(str, Enum):
    MARKDOWN = "markdown"
    JSON = "json"
    CSV = "csv"
    ROBOT = "robot"    # string pura para Robot Framework Keywords


class ChannelFormatter:
    """
    Transforma um DTO de resposta no formato exigido pelo canal de destino.

    Não decide O QUE entregar — apenas COMO formatar.
    A mesma resposta pode ser entregue como Markdown para Streamlit,
    JSON para a API REST, CSV para download, ou string pura para o Robot Framework.
    """

    def format(
        self,
        response: AnyResponse,
        channel: OutputChannel = OutputChannel.MARKDOWN,
    ) -> str:
        dispatch = {
            OutputChannel.MARKDOWN: self._to_markdown,
            OutputChannel.JSON: self._to_json,
            OutputChannel.CSV: self._to_csv,
            OutputChannel.ROBOT: self._to_robot,
        }
        formatter = dispatch.get(channel, self._to_markdown)
        return formatter(response)

    # ── Formatadores por canal ──────────────────────────────────────────────

    def _to_markdown(self, response: AnyResponse) -> str:
        """Retorna o Markdown gerado com cabeçalho de metadados."""
        meta_lines = [
            f"<!-- confidence: {response.confidence_score:.3f} | "
            f"modelo: {response.modelo_usado or 'n/a'} | "
            f"tokens: {response.tokens_consumidos or 'n/a'} | "
            f"request_id: {response.request_id or 'n/a'} -->",
            "",
        ]
        return "\n".join(meta_lines) + response.conteudo_markdown

    def _to_json(self, response: AnyResponse) -> str:
        """Serializa o DTO completo como JSON estruturado."""
        return response.to_json(indent=2)

    def _to_robot(self, response: AnyResponse) -> str:
        """Retorna apenas o conteúdo Markdown — compatível com Robot Framework."""
        return response.conteudo_markdown

    def _to_csv(self, response: AnyResponse) -> str:
        """
        Exporta para CSV. Para RTMResponse tenta extrair linhas da tabela RTM.
        Para outros tipos, exporta metadados.
        """
        if isinstance(response, RTMResponse):
            return self._rtm_to_csv(response)
        return self._metadata_to_csv(response)

    def _rtm_to_csv(self, response: RTMResponse) -> str:
        """
        Tenta extrair a tabela RTM do Markdown e convertê-la para CSV.
        Usa parsing leve de tabelas Markdown — suficiente para RTMs gerados pelo copilot.
        """
        output = io.StringIO()
        writer = csv.writer(output)

        rows = self._extract_markdown_table(response.conteudo_markdown)
        if rows:
            for row in rows:
                writer.writerow(row)
        else:
            # Fallback: exporta metadados se não encontrar tabela
            writer.writerow(["user_story", "confidence_score", "modelo", "tokens", "request_id"])
            writer.writerow([
                response.user_story_nome,
                response.confidence_score,
                response.modelo_usado or "",
                response.tokens_consumidos or "",
                response.request_id or "",
            ])

        return output.getvalue()

    def _metadata_to_csv(self, response: AnyResponse) -> str:
        """CSV de metadados para tipos sem tabela estruturada."""
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["campo", "valor"])
        for k, v in response.to_dict().items():
            if k != "conteudo_markdown":
                writer.writerow([k, v])
        return output.getvalue()

    @staticmethod
    def _extract_markdown_table(markdown: str) -> list[list[str]]:
        """
        Extrai a primeira tabela Markdown encontrada como lista de listas.
        Retorna lista vazia se não encontrar tabela.
        """
        lines = markdown.splitlines()
        table_lines: list[str] = []
        in_table = False

        for line in lines:
            stripped = line.strip()
            if stripped.startswith("|") and stripped.endswith("|"):
                in_table = True
                # Ignora linhas separadoras (|---|---|)
                if not re.match(r"^\|[-\s|:]+\|$", stripped):
                    table_lines.append(stripped)
            elif in_table and table_lines:
                break  # Fim da primeira tabela

        if not table_lines:
            return []

        rows = []
        for line in table_lines:
            cells = [cell.strip() for cell in line.strip("|").split("|")]
            rows.append(cells)
        return rows
