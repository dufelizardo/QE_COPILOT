from __future__ import annotations
from dataclasses import dataclass
from typing import Optional


@dataclass
class Requirement:
    """
    Entidade central de entrada do domínio QA.
    Representa os insumos de uma User Story antes de qualquer processamento LLM.
    Sem dependência de nenhum framework ou biblioteca externa.

    Anteriormente: UserStory — renomeada para Requirement seguindo Clean Architecture,
    pois o domínio trata de requisitos, não de User Stories especificamente.
    """
    nome: str
    descricao: str
    regras_negocio: str
    criterios_aceite: str

    # Campos para criação de nova US do zero
    feature_titulo: Optional[str] = None
    persona: Optional[str] = None
    objetivo_usuario: Optional[str] = None
    beneficio: Optional[str] = None
    contexto: Optional[str] = ""
    restricoes: Optional[str] = ""
    nfr: Optional[str] = ""
    integracoes: Optional[str] = ""
    dados_exemplo: Optional[str] = ""
    dependencias: Optional[str] = ""
    riscos: Optional[str] = ""
    perguntas_abertas: Optional[str] = ""

    def is_nova(self) -> bool:
        """True quando é um requisito a ser criado do zero."""
        return bool(self.feature_titulo and self.persona and self.objetivo_usuario)

    def has_rns(self) -> bool:
        return bool(self.regras_negocio and self.regras_negocio.strip())

    def has_cas(self) -> bool:
        return bool(self.criterios_aceite and self.criterios_aceite.strip())


# Alias para compatibilidade com código existente — remover na próxima versão
UserStory = Requirement
