from abc import ABC, abstractmethod
from dataclasses import dataclass

from app.domain.entities.rtm import QAArtefact


@dataclass
class ValidationResult:
    passed: bool
    score: float          # 0.0 a 1.0
    validator_name: str
    message: str = ""


class BaseValidator(ABC):
    """
    Interface base para todos os validadores.
    Adicionar um novo validador = criar uma subclasse. Não modifica nada existente.
    """
    @abstractmethod
    def validate(self, artefact: QAArtefact) -> ValidationResult:
        ...


class CompletenessValidator(BaseValidator):
    """Verifica se as seções obrigatórias estão presentes no Markdown."""

    REQUIRED = [
        "análise de negócio",
        "análise de requisitos",
        "análise de critérios de aceite",
        "análise de testabilidade",
        "análise técnica",
        "análise de riscos",
        "análise de dependências",
        "análise de rastreabilidade",
        "recomendações finais",
    ]

    def validate(self, artefact: QAArtefact) -> ValidationResult:
        if artefact.tipo == "rtm":
            return ValidationResult(passed=True, score=1.0, validator_name="completeness")

        content_lower = artefact.conteudo_markdown.lower()
        found = sum(1 for sec in self.REQUIRED if sec in content_lower)
        score = found / len(self.REQUIRED)

        return ValidationResult(
            passed=score >= 0.8,
            score=score,
            validator_name="completeness",
            message=f"{found}/{len(self.REQUIRED)} seções obrigatórias encontradas.",
        )


class ContentLengthValidator(BaseValidator):
    """Valida se o conteúdo tem tamanho mínimo razoável."""

    MIN_CHARS = 500

    def validate(self, artefact: QAArtefact) -> ValidationResult:
        length = len(artefact.conteudo_markdown)
        passed = length >= self.MIN_CHARS
        score = min(1.0, length / (self.MIN_CHARS * 10))

        return ValidationResult(
            passed=passed,
            score=score,
            validator_name="content_length",
            message=f"Conteúdo com {length} caracteres (mínimo: {self.MIN_CHARS}).",
        )


class TraceabilityValidator(BaseValidator):
    """Verifica se há referências a RN e CA no conteúdo gerado."""

    def validate(self, artefact: QAArtefact) -> ValidationResult:
        content = artefact.conteudo_markdown
        has_rn = "rn-" in content.lower()
        has_ca = "ca-" in content.lower()

        if has_rn and has_ca:
            return ValidationResult(
                passed=True, score=1.0,
                validator_name="traceability",
                message="Rastreabilidade RN e CA encontrada.",
            )
        elif has_rn or has_ca:
            return ValidationResult(
                passed=True, score=0.6,
                validator_name="traceability",
                message="Rastreabilidade parcial: apenas RN ou CA encontrados.",
            )
        return ValidationResult(
            passed=False, score=0.0,
            validator_name="traceability",
            message="Nenhuma referência RN/CA encontrada. Rastreabilidade ausente.",
        )


@dataclass
class ChainResult:
    passed: bool
    confidence_score: float      # Média ponderada dos scores
    results: list[ValidationResult]
    artefact: QAArtefact

    @property
    def failed_validators(self) -> list[str]:
        return [r.validator_name for r in self.results if not r.passed]


class ValidatorChain:
    """
    Executa todos os validadores em sequência e agrega os resultados.
    Open/Closed: adicionar validador = passar no construtor. Não modifica a chain.

    Uso:
        chain = ValidatorChain([
            CompletenessValidator(),
            ContentLengthValidator(),
            TraceabilityValidator(),
        ])
        result = chain.run(artefact)
        if not result.passed:
            # envia para Failure Handler
    """

    def __init__(self, validators: list[BaseValidator]):
        self._validators = validators

    def run(self, artefact: QAArtefact) -> ChainResult:
        results = [v.validate(artefact) for v in self._validators]
        all_passed = all(r.passed for r in results)
        avg_score = sum(r.score for r in results) / len(results) if results else 0.0

        return ChainResult(
            passed=all_passed,
            confidence_score=round(avg_score, 3),
            results=results,
            artefact=artefact,
        )
