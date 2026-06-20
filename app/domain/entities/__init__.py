"""
domain/entities — Entidades puras do domínio QA.
Sem dependência de frameworks externos.

Estrutura conforme Clean Architecture:
- requirement.py  → Requirement (entrada: User Story com RN e CA)
- test_case.py    → TestCase + enums (saída: caso de teste individual)
- rtm.py          → RTMEntry + QAArtefact (saída: RTM + artefato de pipeline)
"""
from app.domain.entities.requirement import Requirement, UserStory
from app.domain.entities.test_case import (
    TestCase, Prioridade, TipoTeste,
    CategoriaTest, ClassificacaoTeste, TipoExecucao,
)
from app.domain.entities.rtm import RTMEntry, QAArtefact

__all__ = [
    "Requirement", "UserStory",
    "TestCase", "Prioridade", "TipoTeste",
    "CategoriaTest", "ClassificacaoTeste", "TipoExecucao",
    "RTMEntry", "QAArtefact",
]
