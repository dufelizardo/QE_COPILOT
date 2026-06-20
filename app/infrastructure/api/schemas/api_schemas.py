from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Any


# ── Request Schemas ────────────────────────────────────────────────────────

class UserStoryInput(BaseModel):
    nome: str = Field(..., description="Nome/título da User Story")
    descricao: str = Field(..., description="Descrição da User Story")
    regras_negocio: str = Field(..., alias="rns", description="Regras de negócio")
    criterios_aceite: str = Field(..., alias="cas", description="Critérios de aceite")

    class Config:
        populate_by_name = True


class AnalyzeUSRequest(BaseModel):
    user_story: UserStoryInput
    include_gherkin: bool = False
    temperature: float = Field(default=0.2, ge=0.0, le=1.0)
    max_tokens: int = Field(default=2800, ge=100, le=8000)
    channel: str = Field(default="json", description="json | markdown | csv")


class DesignTestsRequest(BaseModel):
    user_story: UserStoryInput
    include_automation_hints: bool = True
    temperature: float = Field(default=0.3, ge=0.0, le=1.0)
    max_tokens: int = Field(default=4000, ge=100, le=8000)
    channel: str = Field(default="json")


class GenerateRTMRequest(BaseModel):
    user_story: UserStoryInput
    temperature: float = Field(default=0.3, ge=0.0, le=1.0)
    max_tokens: int = Field(default=5000, ge=100, le=8000)
    channel: str = Field(default="json")


class CreateUSRequest(BaseModel):
    feature_titulo: str
    persona: str
    objetivo_usuario: str
    beneficio: str
    contexto: str = ""
    regras_negocio: str = ""
    criterios_aceite: str = ""
    restricoes: str = ""
    nfr: str = ""
    integracoes: str = ""
    dados_exemplo: str = ""
    dependencias: str = ""
    riscos: str = ""
    perguntas_abertas: str = ""
    include_gherkin: bool = False
    temperature: float = Field(default=0.2, ge=0.0, le=1.0)
    max_tokens: int = Field(default=3200, ge=100, le=8000)
    channel: str = Field(default="json")
    arquivo_md: str | None = None


class IngestDocumentRequest(BaseModel):
    conteudo: str = Field(..., description="Conteúdo do documento a indexar")
    fonte: str = Field(..., description="Identificador da fonte (ex: 'us/login-mfa')")
    tipo: str = Field(default="documento", description="Tipo: user_story | standard | rtm | documento")
    metadata: dict[str, Any] = Field(default_factory=dict)


class IngestBatchRequest(BaseModel):
    documentos: list[IngestDocumentRequest]


# ── Response Schemas ───────────────────────────────────────────────────────

class ValidationDetail(BaseModel):
    validator: str
    passed: bool
    score: float
    message: str


class BaseQAResponse(BaseModel):
    success: bool
    tipo: str
    confidence_score: float
    modelo_usado: str | None
    tokens_consumidos: int | None
    latencia_ms: float | None
    request_id: str | None
    timestamp: str | None
    validacoes: list[ValidationDetail]
    error_message: str | None = None
    conteudo_markdown: str


class AnalyzeUSResponse(BaseQAResponse):
    user_story_nome: str
    secoes_presentes: list[str]
    secoes_ausentes: list[str]
    completo: bool


class DesignTestsAPIResponse(BaseQAResponse):
    user_story_nome: str
    total_casos: int | None
    casos_positivos: int
    casos_negativos: int


class GenerateRTMAPIResponse(BaseQAResponse):
    user_story_nome: str
    total_tcs: int | None
    rns_cobertas: list[str]
    cas_cobertos: list[str]


class CreateUSAPIResponse(BaseQAResponse):
    feature_titulo: str
    parte_a_user_story: str
    parte_b_analise: str
    completo: bool


class HealthResponse(BaseModel):
    status: str
    llm_ok: bool
    rag_enabled: bool
    version: str = "1.0.0"


class IngestResponse(BaseModel):
    success: bool
    indexed: int
    message: str
