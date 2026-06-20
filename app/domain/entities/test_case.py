from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum


class Prioridade(str, Enum):
    ALTA = "alta"
    MEDIA = "média"
    BAIXA = "baixa"


class TipoTeste(str, Enum):
    POSITIVO = "Positivo"
    NEGATIVO = "Negativo"
    LIMITE = "Limite"
    EXPLORATORIO = "Exploratório"


class CategoriaTest(str, Enum):
    SMOKE = "Smoke"
    REGRESSIVO = "Regressivo"
    EXPLORATORIO = "Exploratório"
    SANIDADE = "Sanidade"


class ClassificacaoTeste(str, Enum):
    FUNCIONAL = "Funcional"
    NAO_FUNCIONAL = "Não Funcional"
    ACESSIBILIDADE = "Acessibilidade"
    PERFORMANCE = "Performance"
    SEGURANCA = "Segurança"


class TipoExecucao(str, Enum):
    PENDENTE_AUTOMACAO = "Pendente de Automação"
    NAO_AUTOMATIZAVEL = "Não Automatizável"
    AUTOMATIZADO = "Automatizado"


@dataclass
class TestCase:
    """
    Entidade de domínio que representa um caso de teste gerado pelo copilot.
    Estrutura mínima para rastreabilidade CA ↔ RN ↔ CT.
    Sem dependência de nenhum framework externo.
    """
    id: str                    # TC-001, TC-002, ...
    nome: str
    descricao: str
    rns_relacionadas: list[str] = field(default_factory=list)
    cas_relacionados: list[str] = field(default_factory=list)
    tipo: TipoTeste = TipoTeste.POSITIVO
    prioridade: Prioridade = Prioridade.MEDIA
    categoria: CategoriaTest = CategoriaTest.REGRESSIVO
    classificacao: ClassificacaoTeste = ClassificacaoTeste.FUNCIONAL
    tipo_execucao: TipoExecucao = TipoExecucao.PENDENTE_AUTOMACAO
    objetivo: str = ""
    preconditions: list[str] = field(default_factory=list)
    passos: list[str] = field(default_factory=list)
    resultado_esperado: str = ""
    dados_teste: str = ""
    automacao_sugerida: str = ""
