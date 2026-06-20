from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional

from app.domain.entities.test_case import (
    TipoTeste, Prioridade, CategoriaTest,
    ClassificacaoTeste, TipoExecucao,
)


@dataclass
class RTMEntry:
    """
    Uma linha da RTM bidirecional: CA → RN → CT(s).
    Entidade pura de domínio — sem dependência de frameworks.
    """
    ca_id: str
    criterio_aceite: str
    rn_id: str
    regra_negocio: str
    cenarios_relacionados: list[str] = field(default_factory=list)
    tipo: TipoTeste = TipoTeste.POSITIVO
    prioridade: Prioridade = Prioridade.MEDIA
    classificacao: ClassificacaoTeste = ClassificacaoTeste.FUNCIONAL
    tipo_execucao: TipoExecucao = TipoExecucao.PENDENTE_AUTOMACAO
    ambiente: str = "QA"
    categoria: CategoriaTest = CategoriaTest.REGRESSIVO
    status: str = "Pendente"


@dataclass
class QAArtefact:
    """
    Artefato de saída do pipeline QA.
    DTO de transporte entre camadas — sem lógica, sem dependências externas.
    Contém o Markdown gerado pelo LLM + metadados de rastreabilidade.
    """
    conteudo_markdown: str
    tipo: str                  # "analise_us" | "rtm" | "design_tests" | "us_nova"
    user_story_nome: str
    secoes_presentes: list[str] = field(default_factory=list)
    test_cases: list = field(default_factory=list)      # list[TestCase]
    rtm_entries: list[RTMEntry] = field(default_factory=list)
    completo: bool = True
    modelo_usado: Optional[str] = None
    tokens_consumidos: Optional[int] = None
    latencia_ms: Optional[float] = None
